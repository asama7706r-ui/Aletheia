use crate::error::DnaError;
use crc32fast::Hasher as Crc32Hasher;

/// التوقيع السحري لسجلات المعرفة في قطاع الـ Lineage (4 بايت: RECD)
pub const MAGIC_RECD: &[u8; 4] = b"RECD";

/// الحجم الثابت لبادئة السجل المعرفي الموحد (32 بايت بالضبط)
pub const RECORD_PREFIX_SIZE: usize = 32;

/// أنواع السجلات المعرفية المعتمدة في ركيزة الـ DNA
pub const RECORD_TYPE_SOVEREIGN_AXIOM: u8 = 0x01; // بديهية وقانون سيادي معتمد
pub const RECORD_TYPE_CONGRUENCE_EDGE: u8 = 0x02; // علاقة تكافؤ مبرهنة بين فئتين
pub const RECORD_TYPE_DOMAIN_ENTRY: u8    = 0x03; // تدشين مجال معرفي مستقل
pub const RECORD_TYPE_BRIDGE_DEF: u8      = 0x04; // جسر رابط وثابت اقتران بين مجالين
pub const RECORD_TYPE_TOMBSTONE_MASK: u8  = 0x05; // علامة إبطال أو تقييد لقانون قديم

/// حالات السجل المعرفي
pub const RECORD_STATUS_ACTIVE: u8      = 0x01; // فعال وسيد
pub const RECORD_STATUS_CONDITIONAL: u8 = 0x02; // مخفض كحالة حدية مشروطة
pub const RECORD_STATUS_TOMBSTONE: u8   = 0x03; // شاهد قبر (مخلوع أو مبطل)

/// بادئة السجل المعرفي الموحد (Universal Record Prefix - 32 Bytes)
/// مصممة بـ #[repr(C)] الصارم مع حشو صريح للمحاذاة عند حد 8 بايت
#[repr(C)]
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct UniversalRecordPrefix {
    /// 0x00 - 0x03: التوقيع السحري (b"RECD")
    pub magic: [u8; 4],
    /// 0x04: نوع السجل (Record Type)
    pub record_type: u8,
    /// 0x05: حالة السجل السيادية (Status)
    pub status: u8,
    /// 0x06 - 0x07: حشو صريح للمحاذاة
    pub pad: u16,
    /// 0x08 - 0x0B: طول الحمولة التابعة للسجل بالبايت
    pub payload_len: u32,
    /// 0x0C - 0x0D: معرّف المجال الأنطولوجي (domain_id)
    pub domain_id: u16,
    /// 0x0E - 0x0F: معرّف زمرة التناظر الدستورية (group_id)
    pub group_id: u16,
    /// 0x10 - 0x13: معرّف فضاء الأبعاد الفرعي المولد (basis_id)
    pub basis_id: u32,
    /// 0x14 - 0x17: بصمة CRC32C لحمولة السجل
    pub payload_crc: u32,
    /// 0x18 - 0x1F: بيانات وصفية إضافية (مثل الطابع الزمني أو الحقبة)
    pub extra_meta: u64,
}

impl UniversalRecordPrefix {
    /// إنشاء بادئة سجل سيادي جديد
    pub fn new_axiom(
        payload_len: u32,
        domain_id: u16,
        payload_crc: u32,
        epoch: u64,
    ) -> Self {
        Self {
            magic: *MAGIC_RECD,
            record_type: RECORD_TYPE_SOVEREIGN_AXIOM,
            status: RECORD_STATUS_ACTIVE,
            pad: 0,
            payload_len,
            domain_id,
            group_id: 0,
            basis_id: 0,
            payload_crc,
            extra_meta: epoch,
        }
    }

    /// إنشاء بادئة سجل تدشين مجال جديد
    pub fn new_domain(domain_id: u16, group_id: u16, basis_id: u32) -> Self {
        Self::new_domain_with_payload(domain_id, group_id, basis_id, 0, 0)
    }

    /// إنشاء بادئة سجل تدشين مجال جديد مع حمولة بيانات (مثل الاسم أو الوصف)
    pub fn new_domain_with_payload(
        domain_id: u16,
        group_id: u16,
        basis_id: u32,
        payload_len: u32,
        payload_crc: u32,
    ) -> Self {
        Self {
            magic: *MAGIC_RECD,
            record_type: RECORD_TYPE_DOMAIN_ENTRY,
            status: RECORD_STATUS_ACTIVE,
            pad: 0,
            payload_len,
            domain_id,
            group_id,
            basis_id,
            payload_crc,
            extra_meta: 0,
        }
    }

    /// إنشاء بادئة سجل حافة تكافؤ سيادية أو قاعدة كبرى مخلدة (Macro-Rule)
    pub fn new_congruence_edge(domain_id: u16, payload_len: u32, payload_crc: u32) -> Self {
        Self {
            magic: *MAGIC_RECD,
            record_type: RECORD_TYPE_CONGRUENCE_EDGE,
            status: RECORD_STATUS_ACTIVE,
            pad: 0,
            payload_len,
            domain_id,
            group_id: 0,
            basis_id: 0,
            payload_crc,
            extra_meta: 0,
        }
    }

    /// إنشاء بادئة سجل جسر بين مجالين
    pub fn new_bridge(
        source_domain: u16,
        target_domain: u16,
        payload_len: u32,
        payload_crc: u32,
    ) -> Self {
        Self {
            magic: *MAGIC_RECD,
            record_type: RECORD_TYPE_BRIDGE_DEF,
            status: RECORD_STATUS_ACTIVE,
            pad: 0,
            payload_len,
            domain_id: source_domain,
            group_id: target_domain,
            basis_id: 0,
            payload_crc,
            extra_meta: 0,
        }
    }

    /// حوسبة بصمة CRC32C لأي حمولة بايتات
    pub fn compute_crc(payload: &[u8]) -> u32 {
        let mut hasher = Crc32Hasher::new();
        hasher.update(payload);
        hasher.finalize()
    }

    /// تسلسل البادئة إلى 32 بايت Little-Endian صرفة
    pub fn to_bytes(&self) -> [u8; RECORD_PREFIX_SIZE] {
        let mut bytes = [0u8; RECORD_PREFIX_SIZE];
        bytes[0..4].copy_from_slice(&self.magic);
        bytes[4] = self.record_type;
        bytes[5] = self.status;
        bytes[6..8].copy_from_slice(&self.pad.to_le_bytes());
        bytes[8..12].copy_from_slice(&self.payload_len.to_le_bytes());
        bytes[12..14].copy_from_slice(&self.domain_id.to_le_bytes());
        bytes[14..16].copy_from_slice(&self.group_id.to_le_bytes());
        bytes[16..20].copy_from_slice(&self.basis_id.to_le_bytes());
        bytes[20..24].copy_from_slice(&self.payload_crc.to_le_bytes());
        bytes[24..32].copy_from_slice(&self.extra_meta.to_le_bytes());
        bytes
    }

    /// فك تسلسل البادئة والتحقق الصارم من التوقيع السحري
    pub fn from_bytes(bytes: &[u8]) -> Result<Self, DnaError> {
        if bytes.len() < RECORD_PREFIX_SIZE {
            return Err(DnaError::BufferUnderflow(bytes.len(), RECORD_PREFIX_SIZE));
        }

        let magic: [u8; 4] = bytes[0..4].try_into().unwrap();
        if &magic != MAGIC_RECD {
            return Err(DnaError::InvalidRecordMagic);
        }

        let record_type = bytes[4];
        let status = bytes[5];
        let pad = u16::from_le_bytes(bytes[6..8].try_into().unwrap());
        let payload_len = u32::from_le_bytes(bytes[8..12].try_into().unwrap());
        let domain_id = u16::from_le_bytes(bytes[12..14].try_into().unwrap());
        let group_id = u16::from_le_bytes(bytes[14..16].try_into().unwrap());
        let basis_id = u32::from_le_bytes(bytes[16..20].try_into().unwrap());
        let payload_crc = u32::from_le_bytes(bytes[20..24].try_into().unwrap());
        let extra_meta = u64::from_le_bytes(bytes[24..32].try_into().unwrap());

        Ok(Self {
            magic,
            record_type,
            status,
            pad,
            payload_len,
            domain_id,
            group_id,
            basis_id,
            payload_crc,
            extra_meta,
        })
    }
}
