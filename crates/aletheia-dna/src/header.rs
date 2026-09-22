use crate::error::DnaError;
use crc32fast::Hasher as Crc32Hasher;

/// التوقيع السحري الثابت لملف الجينوم المعرفي (4 بايت: KDNA)
pub const MAGIC_KDNA: &[u8; 4] = b"KDNA";

/// الحجم الثابت للترويسة الرئيسية (64 بايت بالضبط)
pub const HEADER_SIZE: usize = 64;

/// رايات الحالة المعمارية للجينوم المعرفي
pub const FLAG_LITTLE_ENDIAN: u16 = 0x0001; // Bit 0: ترتيب بايتات Little-Endian
pub const FLAG_COMPACTED: u16 = 0x0002;     // Bit 1: ملف مضغوط ومطهر من شواهد القبور
pub const FLAG_SEED_MODE: u16 = 0x0004;     // Bit 2: وضع البذرة المدمجة للقراءة فقط
pub const DIMENSION_RANK_MASK: u16 = 0xFF00; // Bits 8-15: رتبة فضاء الأبعاد Q^N

/// ترويسة الجينوم المعرفي الرئيسية (Packed Master DNA Header - 64 Bytes)
/// مصممة بـ #[repr(C)] الصارم مع محاذاة طبيعية ومنع أي حشو عشوائي أو Unaligned Access
#[repr(C)]
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct PackedDNAHeader {
    /// 0x00 - 0x03: التوقيع السحري (ASCII: "KDNA")
    pub magic: [u8; 4],
    /// 0x04 - 0x05: إصدار المخطط الثنائي للنواة (مثال: 0x0100 للإصدار 1.0)
    pub version: u16,
    /// 0x06 - 0x07: رايات الحالة ورتبة فضاء الأبعاد الفيزيائية Q^N
    pub flags: u16,
    /// 0x08 - 0x0B: العدد الإجمالي للبديهيات والقوانين السيادية المثبتة
    pub total_axioms: u32,
    /// 0x0C - 0x0F: العدد الكلي للعقد في مصفوفة الـ ENode Arena
    pub total_enodes: u32,
    /// 0x10 - 0x13: العدد الكلي لفئات التكافؤ النشطة
    pub total_classes: u32,
    /// 0x14 - 0x17: الحجم البايتي التراكمي المكتوب في قطاع الـ Lineage
    pub lineage_size: u32,
    /// 0x18 - 0x1F: الإزاحة البايتية لبداية مصفوفة الـ ENode Arena
    pub offset_enodes: u64,
    /// 0x20 - 0x27: الإزاحة البايتية لبداية جدول الـ Union-Find
    pub offset_uf: u64,
    /// 0x28 - 0x2F: الإزاحة البايتية لبداية سجل التطور وصكوك السيادة (Lineage Log)
    pub offset_lineage: u64,
    /// 0x30 - 0x37: بصمة فحص سلامة الترويسة (CRC32C)
    pub state_checksum: u64,
    /// 0x38 - 0x3F: بادئة هاش الحالة الكلية للشجرة المعرفية (Merkle Root)
    pub merkle_root_id: u64,
}

/// السعة الافتراضية الأولية لقطاع مصفوفة العقد في الحجز المسبق (1 ميغابايت = 65,536 عقدة)
pub const DEFAULT_ARENA_CAPACITY: u64 = 1024 * 1024;
/// السعة الافتراضية الأولية لقطاع جدول الـ Union-Find في الحجز المسبق (512 كيلوبايت = 131,072 فئة)
pub const DEFAULT_UF_CAPACITY: u64 = 512 * 1024;

impl PackedDNAHeader {
    /// إنشاء ترويسة افتراضية نظيفة لنواة جديدة بحساب إزاحات القطاعات المحجوزة مسبقاً
    pub fn new(initial_rank: u16) -> Self {
        let flags = FLAG_LITTLE_ENDIAN | ((initial_rank << 8) & DIMENSION_RANK_MASK);
        let offset_enodes = HEADER_SIZE as u64;
        let offset_uf = offset_enodes + DEFAULT_ARENA_CAPACITY;
        let offset_lineage = offset_uf + DEFAULT_UF_CAPACITY;

        let mut header = Self {
            magic: *MAGIC_KDNA,
            version: 0x0100,
            flags,
            total_axioms: 0,
            total_enodes: 0,
            total_classes: 0,
            lineage_size: 0,
            offset_enodes,
            offset_uf,
            offset_lineage,
            state_checksum: 0,
            merkle_root_id: 0,
        };
        header.state_checksum = header.compute_checksum();
        header
    }

    /// استخراج رتبة فضاء الأبعاد Q^N الحالية من رايات الترويسة
    #[inline]
    pub fn dimension_rank(&self) -> u16 {
        (self.flags & DIMENSION_RANK_MASK) >> 8
    }

    /// تحديث رتبة فضاء الأبعاد Q^N في رايات الترويسة
    #[inline]
    pub fn set_dimension_rank(&mut self, rank: u16) {
        self.flags = (self.flags & !DIMENSION_RANK_MASK) | ((rank << 8) & DIMENSION_RANK_MASK);
        self.state_checksum = self.compute_checksum();
    }

    /// هل الملف مضغوط ومطهر من شواهد القبور؟
    #[inline]
    pub fn is_compacted(&self) -> bool {
        (self.flags & FLAG_COMPACTED) != 0
    }

    /// هل النواة تعمل في وضع البذرة المدمجة للقراءة فقط؟
    #[inline]
    pub fn is_seed_mode(&self) -> bool {
        (self.flags & FLAG_SEED_MODE) != 0
    }

    /// حوسبة بصمة التحقق التشفيرية CRC32C لكافة حقول الترويسة
    pub fn compute_checksum(&self) -> u64 {
        let mut hasher = Crc32Hasher::new();
        hasher.update(&self.magic);
        hasher.update(&self.version.to_le_bytes());
        hasher.update(&self.flags.to_le_bytes());
        hasher.update(&self.total_axioms.to_le_bytes());
        hasher.update(&self.total_enodes.to_le_bytes());
        hasher.update(&self.total_classes.to_le_bytes());
        hasher.update(&self.lineage_size.to_le_bytes());
        hasher.update(&self.offset_enodes.to_le_bytes());
        hasher.update(&self.offset_uf.to_le_bytes());
        hasher.update(&self.offset_lineage.to_le_bytes());
        hasher.update(&self.merkle_root_id.to_le_bytes());
        hasher.finalize() as u64
    }

    /// تسلسل الترويسة إلى مصفوفة 64 بايت Little-Endian صرفة
    pub fn to_bytes(&self) -> [u8; HEADER_SIZE] {
        let mut bytes = [0u8; HEADER_SIZE];
        bytes[0..4].copy_from_slice(&self.magic);
        bytes[4..6].copy_from_slice(&self.version.to_le_bytes());
        bytes[6..8].copy_from_slice(&self.flags.to_le_bytes());
        bytes[8..12].copy_from_slice(&self.total_axioms.to_le_bytes());
        bytes[12..16].copy_from_slice(&self.total_enodes.to_le_bytes());
        bytes[16..20].copy_from_slice(&self.total_classes.to_le_bytes());
        bytes[20..24].copy_from_slice(&self.lineage_size.to_le_bytes());
        bytes[24..32].copy_from_slice(&self.offset_enodes.to_le_bytes());
        bytes[32..40].copy_from_slice(&self.offset_uf.to_le_bytes());
        bytes[40..48].copy_from_slice(&self.offset_lineage.to_le_bytes());
        bytes[48..56].copy_from_slice(&self.state_checksum.to_le_bytes());
        bytes[56..64].copy_from_slice(&self.merkle_root_id.to_le_bytes());
        bytes
    }

    /// فك تسلسل الترويسة والتحقق الصارم من التوقيع السحري والبصمة
    pub fn from_bytes(bytes: &[u8]) -> Result<Self, DnaError> {
        if bytes.len() < HEADER_SIZE {
            return Err(DnaError::BufferUnderflow(bytes.len(), HEADER_SIZE));
        }

        let magic: [u8; 4] = bytes[0..4].try_into().unwrap();
        if &magic != MAGIC_KDNA {
            return Err(DnaError::InvalidMagicHeader(
                String::from_utf8_lossy(&magic).to_string(),
            ));
        }

        let version = u16::from_le_bytes(bytes[4..6].try_into().unwrap());
        let flags = u16::from_le_bytes(bytes[6..8].try_into().unwrap());
        let total_axioms = u32::from_le_bytes(bytes[8..12].try_into().unwrap());
        let total_enodes = u32::from_le_bytes(bytes[12..16].try_into().unwrap());
        let total_classes = u32::from_le_bytes(bytes[16..20].try_into().unwrap());
        let lineage_size = u32::from_le_bytes(bytes[20..24].try_into().unwrap());
        let offset_enodes = u64::from_le_bytes(bytes[24..32].try_into().unwrap());
        let offset_uf = u64::from_le_bytes(bytes[32..40].try_into().unwrap());
        let offset_lineage = u64::from_le_bytes(bytes[40..48].try_into().unwrap());
        let state_checksum = u64::from_le_bytes(bytes[48..56].try_into().unwrap());
        let merkle_root_id = u64::from_le_bytes(bytes[56..64].try_into().unwrap());

        let header = Self {
            magic,
            version,
            flags,
            total_axioms,
            total_enodes,
            total_classes,
            lineage_size,
            offset_enodes,
            offset_uf,
            offset_lineage,
            state_checksum,
            merkle_root_id,
        };

        let computed = header.compute_checksum();
        if computed != state_checksum {
            return Err(DnaError::ChecksumMismatch {
                expected: state_checksum,
                computed,
            });
        }

        Ok(header)
    }
}
