use crate::error::DnaError;
use crate::header::{HEADER_SIZE, PackedDNAHeader};
use crate::packed_enode::{ENODE_SIZE, PackedENode};
use memmap2::{Mmap, MmapMut};
use std::fs::{File, OpenOptions};
use std::path::{Path, PathBuf};

/// السعة الافتراضية الأولية للحجز المسبق لملف الـ DNA (4 ميغابايت)
pub const INITIAL_PREALLOCATION_SIZE: u64 = 4 * 1024 * 1024;

/// المحرك التنفيذي لخريطة الذاكرة المباشرة (Zero-Copy mmap Engine)
/// يدعم وضعين:
/// 1. ملف فيزيائي على القرص مربوط عبر mmap/mmap_mut مع حماية Windows من خطأ 0x4C8.
/// 2. ذاكرة حية مستقلة (In-Memory Buffer) للاستدلال السريع أو البذرة المدمجة.
pub struct DnaStorageEngine {
    file: Option<File>,
    file_path: Option<PathBuf>,
    mmap_mut: Option<MmapMut>,
    mmap_read: Option<Mmap>,
    memory_buffer: Option<Vec<u8>>,
    static_slice: Option<&'static [u8]>,
    pub header: PackedDNAHeader,
    pub is_read_only: bool,
}

impl DnaStorageEngine {
    /// استرجاع مسار الملف إن وجد
    pub fn file_path(&self) -> Option<&Path> {
        self.file_path.as_deref()
    }

    /// فتح ملف DNA موجود للقراءة المباشرة فقط عبر Zero-Copy mmap
    pub fn open_read_only<P: AsRef<Path>>(path: P) -> Result<Self, DnaError> {
        let file = OpenOptions::new()
            .read(true)
            .open(path.as_ref())
            .map_err(|e| DnaError::IoError(e.to_string()))?;

        let meta = file
            .metadata()
            .map_err(|e| DnaError::IoError(e.to_string()))?;

        if meta.len() < HEADER_SIZE as u64 {
            return Err(DnaError::BufferUnderflow(meta.len() as usize, HEADER_SIZE));
        }

        let mmap_read = unsafe {
            Mmap::map(&file).map_err(|e| DnaError::IoError(e.to_string()))?
        };

        let header = PackedDNAHeader::from_bytes(&mmap_read[..HEADER_SIZE])?;

        Ok(Self {
            file: Some(file),
            file_path: Some(path.as_ref().to_path_buf()),
            mmap_mut: None,
            mmap_read: Some(mmap_read),
            memory_buffer: None,
            static_slice: None,
            header,
            is_read_only: true,
        })
    }

    /// فتح ملف DNA موجود للتطور أو إنشاؤه مسبقاً بحجم 4 ميغابايت (Pre-allocated Arena)
    pub fn open_or_create<P: AsRef<Path>>(
        path: P,
        initial_rank: u16,
    ) -> Result<Self, DnaError> {
        let path_ref = path.as_ref();
        let exists = path_ref.exists();

        let file = OpenOptions::new()
            .read(true)
            .write(true)
            .create(true)
            .truncate(false)
            .open(path_ref)
            .map_err(|e| DnaError::IoError(e.to_string()))?;

        let meta = file
            .metadata()
            .map_err(|e| DnaError::IoError(e.to_string()))?;

        let current_len = meta.len();

        let header = if exists && current_len >= HEADER_SIZE as u64 {
            // قراءة الترويسة القائمة
            let mmap = unsafe {
                Mmap::map(&file).map_err(|e| DnaError::IoError(e.to_string()))?
            };
            PackedDNAHeader::from_bytes(&mmap[..HEADER_SIZE])?
        } else {
            // تهيئة ملف جديد مع الحجز المسبق لـ 4 ميغابايت
            let new_header = PackedDNAHeader::new(initial_rank);
            let target_len = INITIAL_PREALLOCATION_SIZE.max(HEADER_SIZE as u64);
            file.set_len(target_len)
                .map_err(|e| DnaError::IoError(e.to_string()))?;

            let mut mmap_mut = unsafe {
                MmapMut::map_mut(&file).map_err(|e| DnaError::IoError(e.to_string()))?
            };
            mmap_mut[..HEADER_SIZE].copy_from_slice(&new_header.to_bytes());
            mmap_mut.flush().map_err(|e| DnaError::IoError(e.to_string()))?;
            new_header
        };

        let mmap_mut = unsafe {
            MmapMut::map_mut(&file).map_err(|e| DnaError::IoError(e.to_string()))?
        };

        Ok(Self {
            file: Some(file),
            file_path: Some(path_ref.to_path_buf()),
            mmap_mut: Some(mmap_mut),
            mmap_read: None,
            memory_buffer: None,
            static_slice: None,
            header,
            is_read_only: false,
        })
    }

    /// إنشاء محرك تخزين يعمل بالكامل في الـ RAM من بايتات قابلة للتعديل
    pub fn from_memory(mut bytes: Vec<u8>) -> Result<Self, DnaError> {
        if bytes.len() < HEADER_SIZE {
            bytes.resize(HEADER_SIZE, 0);
            let hdr = PackedDNAHeader::new(3);
            bytes[..HEADER_SIZE].copy_from_slice(&hdr.to_bytes());
        }

        let header = PackedDNAHeader::from_bytes(&bytes[..HEADER_SIZE])?;

        Ok(Self {
            file: None,
            file_path: None,
            mmap_mut: None,
            mmap_read: None,
            memory_buffer: Some(bytes),
            static_slice: None,
            header,
            is_read_only: false,
        })
    }

    /// تشغيل المحرك من شريحة ذاكرة ثابتة (البذرة المدمجة في .rodata)
    pub fn from_static_slice(slice: &'static [u8]) -> Result<Self, DnaError> {
        let header = PackedDNAHeader::from_bytes(&slice[..HEADER_SIZE])?;
        Ok(Self {
            file: None,
            file_path: None,
            mmap_mut: None,
            mmap_read: None,
            memory_buffer: None,
            static_slice: Some(slice),
            header,
            is_read_only: true,
        })
    }

    /// الحصول على شريحة البايتات للقراءة
    #[inline]
    pub fn buffer(&self) -> &[u8] {
        if let Some(m) = &self.mmap_read {
            m
        } else if let Some(m) = &self.mmap_mut {
            m
        } else if let Some(b) = &self.memory_buffer {
            b
        } else if let Some(s) = self.static_slice {
            s
        } else {
            &[]
        }
    }

    /// الحصول على شريحة البايتات للكتابة
    #[inline]
    pub fn buffer_mut(&mut self) -> Result<&mut [u8], DnaError> {
        if self.is_read_only {
            return Err(DnaError::IoError(
                "محاولة تعديل محرك تخزين في وضع القراءة فقط".to_string(),
            ));
        }

        if let Some(m) = &mut self.mmap_mut {
            Ok(m)
        } else if let Some(b) = &mut self.memory_buffer {
            Ok(b)
        } else {
            Err(DnaError::IoError(
                "لا توجد ذاكرة قابلة للكتابة متاحة".to_string(),
            ))
        }
    }

    /// استعلام التكافؤ اللحظي في زمن O(1) الحقيقي دون أي دوران أو تخصيص للذاكرة
    /// يستند بصرامة إلى شرط تسطيح أشجار الـ Union-Find بنسبة 100%
    pub fn query_fast_equivalence(&self, class_a: u32, class_b: u32) -> Result<bool, DnaError> {
        if class_a == class_b {
            return Ok(true);
        }

        if class_a >= self.header.total_classes || class_b >= self.header.total_classes {
            return Ok(false);
        }

        let buf = self.buffer();
        let offset_uf = self.header.offset_uf as usize;
        let pos_a = offset_uf + (class_a as usize * 4);
        let pos_b = offset_uf + (class_b as usize * 4);

        if pos_a + 4 > buf.len() || pos_b + 4 > buf.len() {
            return Err(DnaError::BufferUnderflow(buf.len(), pos_a.max(pos_b) + 4));
        }

        let root_a = u32::from_le_bytes(buf[pos_a..pos_a + 4].try_into().unwrap());
        let root_b = u32::from_le_bytes(buf[pos_b..pos_b + 4].try_into().unwrap());

        Ok(root_a == root_b)
    }

    /// قراءة عقدة ENode مسطحة من مصفوفة الـ Arena
    pub fn read_enode(&self, index: u32) -> Result<PackedENode, DnaError> {
        if index >= self.header.total_enodes {
            return Err(DnaError::BufferUnderflow(
                index as usize,
                self.header.total_enodes as usize,
            ));
        }

        let offset = self.header.offset_enodes as usize + (index as usize * ENODE_SIZE);
        let buf = self.buffer();
        PackedENode::from_bytes(&buf[offset..offset + ENODE_SIZE])
    }

    /// كتابة الترويسة المحدثة ذرياً
    pub fn sync_header(&mut self) -> Result<(), DnaError> {
        self.header.state_checksum = self.header.compute_checksum();
        let header_bytes = self.header.to_bytes();
        let buf = self.buffer_mut()?;
        buf[..HEADER_SIZE].copy_from_slice(&header_bytes);
        Ok(())
    }

    /// مزامنة التعديلات على القرص (Flush / msync)
    pub fn flush(&mut self) -> Result<(), DnaError> {
        self.sync_header()?;
        if let Some(m) = &mut self.mmap_mut {
            m.flush().map_err(|e| DnaError::IoError(e.to_string()))?;
        }
        if let Some(f) = &self.file {
            f.sync_data().map_err(|e| DnaError::IoError(e.to_string()))?;
        }
        Ok(())
    }

    /// التحقق من توفر مساحة كافية في حيز الحجز المسبق، وتوسيعه بنظافة عند الحاجة
    pub fn ensure_capacity(&mut self, required_len: usize) -> Result<(), DnaError> {
        let current_capacity = self.buffer().len();
        if current_capacity >= required_len {
            return Ok(());
        }

        // مضاعفة السعة لتفادي التوسيع المتكرر (Growth Factor = 2x)
        let new_capacity = (current_capacity * 2).max(required_len).max(HEADER_SIZE * 2);

        if let Some(b) = &mut self.memory_buffer {
            b.resize(new_capacity, 0);
            return Ok(());
        }

        // في بيئة Windows: يجب إسقاط mmap_mut قبل تغيير حجم الملف لتفادي ERROR_USER_MAPPED_FILE
        if let Some(file) = &self.file {
            if self.mmap_mut.is_some() {
                self.mmap_mut = None; // إسقاط المقبض بنظافة

                file.set_len(new_capacity as u64)
                    .map_err(|e| DnaError::IoError(e.to_string()))?;

                let new_mmap = unsafe {
                    MmapMut::map_mut(file).map_err(|e| DnaError::IoError(e.to_string()))?
                };
                self.mmap_mut = Some(new_mmap);
                return Ok(());
            }
        }

        Err(DnaError::ArenaCapacityExceeded(new_capacity as u64))
    }
}
