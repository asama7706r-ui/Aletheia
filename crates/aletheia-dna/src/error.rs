use thiserror::Error;

/// أخطاء ركيزة الجينوم المعرفي ومحرك الـ DNA
#[derive(Error, Debug, PartialEq, Eq, Clone)]
pub enum DnaError {
    #[error("ترويسة سحرية غير صالحة لملف الـ DNA: المتوقع 'KDNA' والمسجل '{0}'")]
    InvalidMagicHeader(String),

    #[error("إصدار مخطط ثنائي غير متوافق: {0:#06x}")]
    UnsupportedVersion(u16),

    #[error("فساد في بصمة فحص سلامة الترويسة CRC32C: المتوقع {expected:#018x} والمحسوب {computed:#018x}")]
    ChecksumMismatch { expected: u64, computed: u64 },

    #[error("حجم غير كافٍ للترويسة أو قطاعات الذاكرة: الحجم المتاح {0} بايت والأدنى المطلوب {1} بايت")]
    BufferUnderflow(usize, usize),

    #[error("تجاوز سعة الحيز المحجوز مسبقاً لمصفوفة الـ Arena: السعة {0} بايت")]
    ArenaCapacityExceeded(u64),

    #[error("فساد في سجل المعرفة: التوقيع السحري 'RECD' غير مطابق")]
    InvalidRecordMagic,

    #[error("تلف في حمولة السجل: بصمة CRC32 لا تطابق البيانات")]
    RecordChecksumMismatch,

    #[error("خطأ إدخال/إخراج أو عتاد في خريطة الذاكرة mmap: {0}")]
    IoError(String),

    #[error("خطأ في فضاء التكافؤ أو الإغلاق التطابقي: {0}")]
    CongruenceError(String),

    #[error("فشل استيعاب صك سيادي من المحور السابع: {0}")]
    PayloadIngestionError(String),

    #[error("فشل غربال الاستقلال الجبري: البعد المقترح ليس مستقلاً خطياً عن الأبعاد القائمة: {0}")]
    AlgebraicDependenceError(String),
}
