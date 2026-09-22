use crate::error::DnaError;
use crate::header::{
    DEFAULT_ARENA_CAPACITY, DEFAULT_UF_CAPACITY, FLAG_COMPACTED, FLAG_LITTLE_ENDIAN, HEADER_SIZE,
    PackedDNAHeader,
};
use crate::mmap_engine::DnaStorageEngine;
use crate::packed_enode::{ENODE_SIZE, PackedENode};
use crate::record::{
    RECORD_PREFIX_SIZE, RECORD_STATUS_ACTIVE, RECORD_STATUS_CONDITIONAL, RECORD_STATUS_TOMBSTONE,
    RECORD_TYPE_TOMBSTONE_MASK, UniversalRecordPrefix,
};
use std::collections::HashMap;
use std::fs::File;
use std::io::Write;
use std::path::{Path, PathBuf};

/// تقرير إحصائي عن عملية التطهير المادي للملف
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CompactionReport {
    pub original_file_bytes: u64,
    pub compacted_file_bytes: u64,
    pub pruned_tombstone_records: usize,
    pub remaining_active_records: usize,
    pub remaining_enodes: u32,
    pub remaining_classes: u32,
}

/// نمط التبديل الثلاثي الآمن للملفات على نظام Windows
/// يمنع خطأ AlreadyExists (رمز 183) مع ضمان عدم فقدان البيانات عند حدوث أي تعثر
pub fn safe_atomic_replace(temp_path: &Path, target_path: &Path) -> Result<(), std::io::Error> {
    let backup_path = target_path.with_extension("dna.bak");

    // 1. حذف النسخة الاحتياطية القديمة إن وجدت
    if backup_path.exists() {
        let _ = std::fs::remove_file(&backup_path);
    }

    // 2. ترحيل الملف الأصلي كنسخة احتياطية لتفريغ مسار الهدف
    if target_path.exists() {
        std::fs::rename(target_path, &backup_path)?;
    }

    // 3. نقل الملف المؤقت الجديد النظيف إلى المسار النهائي
    if let Err(e) = std::fs::rename(temp_path, target_path) {
        // في حال حدوث أي خطأ، استعادة النسخة الاحتياطية فوراً
        if backup_path.exists() {
            let _ = std::fs::rename(&backup_path, target_path);
        }
        return Err(e);
    }

    // 4. حذف النسخة الاحتياطية بعد نجاح التبديل بالكامل
    if backup_path.exists() {
        let _ = std::fs::remove_file(&backup_path);
    }

    Ok(())
}

/// محرك التطهير المادي لشواهد القبور (Tombstone Compactor)
pub struct PhysicalCompactor;

impl PhysicalCompactor {
    /// تطهير ملف DNA من شواهد القبور والسجلات الميتة على القرص
    pub fn compact_file(target_path: &Path) -> Result<CompactionReport, DnaError> {
        let original_meta = std::fs::metadata(target_path)
            .map_err(|e| DnaError::IoError(format!("فشل قراءة بيانات الملف: {}", e)))?;
        let original_file_bytes = original_meta.len();

        let mut active_records: Vec<(UniversalRecordPrefix, Vec<u8>)> = Vec::new();
        let mut pruned_count = 0;
        let rank: u16;
        let mut active_enodes: Vec<PackedENode> = Vec::new();
        let mut old_classes_present = HashMap::new();

        // 1. فتح الملف للقراءة واستخراج السجلات النشطة والعقد
        {
            let storage = DnaStorageEngine::open_read_only(target_path)?;
            rank = storage.header.dimension_rank();

            // قراءة العقد
            for i in 0..storage.header.total_enodes {
                if let Ok(node) = storage.read_enode(i) {
                    old_classes_present.insert(node.left_class_id, true);
                    active_enodes.push(node);
                }
            }

            // مسح قطاع السجلات (Lineage Log)
            let buf = storage.buffer();
            let mut offset = storage.header.offset_lineage as usize;
            let lineage_end = offset + storage.header.lineage_size as usize;

            while offset + RECORD_PREFIX_SIZE <= lineage_end && offset + RECORD_PREFIX_SIZE <= buf.len() {
                if let Ok(prefix) = UniversalRecordPrefix::from_bytes(&buf[offset..offset + RECORD_PREFIX_SIZE]) {
                    let p_start = offset + RECORD_PREFIX_SIZE;
                    let p_end = p_start + prefix.payload_len as usize;

                    if p_end > buf.len() || p_end > lineage_end {
                        break;
                    }

                    // تصفية شواهد القبور
                    if prefix.status == RECORD_STATUS_TOMBSTONE || prefix.record_type == RECORD_TYPE_TOMBSTONE_MASK {
                        pruned_count += 1;
                    } else if prefix.status == RECORD_STATUS_ACTIVE || prefix.status == RECORD_STATUS_CONDITIONAL {
                        let payload = buf[p_start..p_end].to_vec();
                        active_records.push((prefix, payload));
                    }
                    offset = p_end;
                } else {
                    break;
                }
            }
        } // هنا تسقط storage وتتحرر كافة مقابض الـ mmap للملف تماماً في Windows!

        // 2. إعادة تعيين أصناف التكافؤ لتكون متتالية دون فجوات
        let mut sorted_classes: Vec<u32> = old_classes_present.keys().copied().collect();
        sorted_classes.sort_unstable();

        let mut class_remap: HashMap<u32, u32> = HashMap::new();
        for (new_idx, &old_c) in sorted_classes.iter().enumerate() {
            class_remap.insert(old_c, new_idx as u32);
        }

        let new_total_classes = sorted_classes.len() as u32;

        // تعديل العقد بالفئات الجديدة
        for node in &mut active_enodes {
            if let Some(&new_c) = class_remap.get(&node.left_class_id) {
                node.left_class_id = new_c;
            }
        }

        // 3. كتابة الملف المنقى في مسار مؤقت
        let temp_path: PathBuf = target_path.with_extension("compact.tmp");
        {
            let mut temp_file = File::create(&temp_path)
                .map_err(|e| DnaError::IoError(format!("فشل إنشاء الملف المؤقت: {}", e)))?;

            let offset_enodes = HEADER_SIZE as u64;
            let offset_uf = offset_enodes + DEFAULT_ARENA_CAPACITY;
            let offset_lineage = offset_uf + DEFAULT_UF_CAPACITY;

            let mut total_lineage_size = 0u32;
            for (_prefix, payload) in &active_records {
                total_lineage_size += (RECORD_PREFIX_SIZE + payload.len()) as u32;
            }

            let flags = FLAG_LITTLE_ENDIAN | FLAG_COMPACTED | ((rank << 8) & crate::header::DIMENSION_RANK_MASK);

            let mut header = PackedDNAHeader {
                magic: *crate::header::MAGIC_KDNA,
                version: 0x0100,
                flags,
                total_axioms: active_records.len() as u32,
                total_enodes: active_enodes.len() as u32,
                total_classes: new_total_classes,
                lineage_size: total_lineage_size,
                offset_enodes,
                offset_uf,
                offset_lineage,
                state_checksum: 0,
                merkle_root_id: 0,
            };
            header.state_checksum = header.compute_checksum();

            // كتابة الترويسة
            temp_file.write_all(&header.to_bytes())
                .map_err(|e| DnaError::IoError(e.to_string()))?;

            // كتابة العقد في الـ Arena
            for node in &active_enodes {
                temp_file.write_all(&node.to_bytes())
                    .map_err(|e| DnaError::IoError(e.to_string()))?;
            }

            // حشو الـ Arena المتبقية حتى offset_uf
            let current_pos = HEADER_SIZE + (active_enodes.len() * ENODE_SIZE);
            if (current_pos as u64) < offset_uf {
                let pad_len = (offset_uf - current_pos as u64) as usize;
                temp_file.write_all(&vec![0u8; pad_len])
                    .map_err(|e| DnaError::IoError(e.to_string()))?;
            }

            // كتابة الـ Union-Find بضغط مسار كامل 100% (parent[c] = c)
            for c in 0..new_total_classes {
                temp_file.write_all(&c.to_le_bytes())
                    .map_err(|e| DnaError::IoError(e.to_string()))?;
            }

            // حشو الـ UF حتى offset_lineage
            let uf_written = (new_total_classes as u64) * 4;
            if uf_written < DEFAULT_UF_CAPACITY {
                let pad_len = (DEFAULT_UF_CAPACITY - uf_written) as usize;
                temp_file.write_all(&vec![0u8; pad_len])
                    .map_err(|e| DnaError::IoError(e.to_string()))?;
            }

            // كتابة السجلات المعرفية النشطة
            for (prefix, payload) in &active_records {
                temp_file.write_all(&prefix.to_bytes())
                    .map_err(|e| DnaError::IoError(e.to_string()))?;
                temp_file.write_all(payload)
                    .map_err(|e| DnaError::IoError(e.to_string()))?;
            }

            temp_file.flush()
                .map_err(|e| DnaError::IoError(e.to_string()))?;
        }

        let compacted_file_bytes = std::fs::metadata(&temp_path)
            .map_err(|e| DnaError::IoError(e.to_string()))?
            .len();

        // 4. تنفيذ التبديل الذري المتوافق مع نظام Windows
        safe_atomic_replace(&temp_path, target_path)
            .map_err(|e| DnaError::IoError(format!("فشل التبديل الذري للملف: {}", e)))?;

        Ok(CompactionReport {
            original_file_bytes,
            compacted_file_bytes,
            pruned_tombstone_records: pruned_count,
            remaining_active_records: active_records.len(),
            remaining_enodes: active_enodes.len() as u32,
            remaining_classes: new_total_classes,
        })
    }

    /// تطهير محرك الـ DNA النشط وإعادة تحميله بصيغة مدمجة نقية
    pub fn compact_engine(engine: DnaStorageEngine) -> Result<DnaStorageEngine, DnaError> {
        let path = engine.file_path()
            .ok_or_else(|| DnaError::IoError("لا يمكن تطهير محرك تخزين يعمل من الذاكرة فقط".to_string()))?
            .to_path_buf();

        let rank = engine.header.dimension_rank();
        // إغلاق المحرك لتحرير المراجع والـ mmap
        drop(engine);

        // إجراء التطهير
        Self::compact_file(&path)?;

        // إعادة فتح المحرك المدمج
        DnaStorageEngine::open_or_create(&path, rank)
    }
}
