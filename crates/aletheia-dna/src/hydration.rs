use crate::embedded_seed::get_embedded_seed;
use crate::error::DnaError;
use crate::header::HEADER_SIZE;
use crate::mmap_engine::DnaStorageEngine;
use std::fs;
use std::path::{Path, PathBuf};
use std::time::Instant;

/// خط أنابيب الإنعاش اللحظي المعرفي (Instant Hydration Pipeline)
/// يحقق الإقلاع الفائق في زمن شبه معدوم (< 3 ms) عبر بروتوكول الإقلاع الثنائي الذكي
pub struct InstantHydrationPipeline {
    pub storage: DnaStorageEngine,
    pub boot_latency_micros: u128,
    pub is_evolutionary_mode: bool,
    pub local_path: Option<PathBuf>,
}

impl InstantHydrationPipeline {
    /// الإقلاع التلقائي الذكي للنواة:
    /// 1. محاولة الإقلاع من الملف المحلي kernel.dna عبر Zero-Copy mmap.
    /// 2. في حال عدم وجود الملف أو تلفه: الإقلاع الاحتياطي الفوري من البذرة المدمجة في الـ RAM.
    pub fn boot<P: AsRef<Path>>(
        local_path_opt: Option<P>,
        allow_evolution: bool,
    ) -> Result<Self, DnaError> {
        let start = Instant::now();

        if let Some(path) = local_path_opt {
            let p = path.as_ref();
            if p.exists() {
                if let Ok(meta) = fs::metadata(p) {
                    if meta.len() >= HEADER_SIZE as u64 {
                        // محاولة فتح الملف المحلي
                        let storage_res = if allow_evolution {
                            DnaStorageEngine::open_or_create(p, 3)
                        } else {
                            DnaStorageEngine::open_read_only(p)
                        };

                        if let Ok(storage) = storage_res {
                            let latency = start.elapsed().as_micros();
                            return Ok(Self {
                                storage,
                                boot_latency_micros: latency,
                                is_evolutionary_mode: allow_evolution,
                                local_path: Some(p.to_path_buf()),
                            });
                        }
                    }
                }
            }

            // إذا كان مسار التطور مطلوباً ولكن الملف غير موجود بعد:
            // نقوم بإنشاء الملف المحلي وتفريغ البذرة الجينية المدمجة فيه فورياً
            if allow_evolution {
                let seed_bytes = get_embedded_seed();
                let seed_header = crate::header::PackedDNAHeader::from_bytes(&seed_bytes[..HEADER_SIZE])?;
                let mut storage = DnaStorageEngine::open_or_create(p, seed_header.dimension_rank())?;

                let seed_enodes_start = seed_header.offset_enodes as usize;
                let seed_enodes_end = seed_enodes_start + (seed_header.total_enodes as usize * crate::packed_enode::ENODE_SIZE);
                let target_enodes_start = storage.header.offset_enodes as usize;

                let seed_uf_start = seed_header.offset_uf as usize;
                let seed_uf_end = seed_uf_start + (seed_header.total_classes as usize * 4);
                let target_uf_start = storage.header.offset_uf as usize;

                let seed_lineage_start = seed_header.offset_lineage as usize;
                let seed_lineage_end = seed_bytes.len();
                let target_lineage_start = storage.header.offset_lineage as usize;
                let lineage_len = seed_lineage_end.saturating_sub(seed_lineage_start);

                {
                    let buf = storage.buffer_mut()?;
                    buf[target_enodes_start..target_enodes_start + (seed_header.total_enodes as usize * crate::packed_enode::ENODE_SIZE)]
                        .copy_from_slice(&seed_bytes[seed_enodes_start..seed_enodes_end]);
                    buf[target_uf_start..target_uf_start + (seed_header.total_classes as usize * 4)]
                        .copy_from_slice(&seed_bytes[seed_uf_start..seed_uf_end]);
                    if lineage_len > 0 {
                        buf[target_lineage_start..target_lineage_start + lineage_len]
                            .copy_from_slice(&seed_bytes[seed_lineage_start..seed_lineage_end]);
                    }
                }

                storage.header.total_enodes = seed_header.total_enodes;
                storage.header.total_classes = seed_header.total_classes;
                storage.header.total_axioms = seed_header.total_axioms;
                storage.header.offset_lineage = (target_lineage_start + lineage_len) as u64;
                storage.flush()?;

                let latency = start.elapsed().as_micros();
                return Ok(Self {
                    storage,
                    boot_latency_micros: latency,
                    is_evolutionary_mode: true,
                    local_path: Some(p.to_path_buf()),
                });
            }
        }

        // الإقلاع الافتراضي النقي من البذرة المدمجة في الـ RAM (Zero Disk Access)
        let seed_slice = get_embedded_seed();
        let storage = DnaStorageEngine::from_static_slice(seed_slice)?;
        let latency = start.elapsed().as_micros();

        Ok(Self {
            storage,
            boot_latency_micros: latency,
            is_evolutionary_mode: false,
            local_path: None,
        })
    }

    /// استعلام التكافؤ اللحظي في زمن O(1)
    #[inline]
    pub fn query_equivalence(&self, class_a: u32, class_b: u32) -> Result<bool, DnaError> {
        self.storage.query_fast_equivalence(class_a, class_b)
    }

    /// التحقق من أن زمن الإقلاع لا يتجاوز سقف الـ 3 ميلي ثانية
    pub fn verify_sub_3ms_invariant(&self) -> bool {
        self.boot_latency_micros < 3000
    }
}
