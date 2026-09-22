use blake3::Hasher;
use serde::{Deserialize, Serialize};

/// تمثيل النزاع المعرفي بين فرضيتين متنافستين أو قانونين متنازعين
/// تطبيق المبدأ الدستوري: تعليق الحكم مع الحصانة (UNCERTAIN_EPOCHE)
/// يُمنع إعدام أي طرف من طرفي النزاع مبكراً، ويُمنح الطرفان حصانة الحجر الصحي المؤقتة
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct DisputedPair {
    /// البصمة المعمارية الفريدة للنزاع
    pub pair_id: [u8; 32],
    /// بصمة الفرضية أو القانون الأول A
    pub hypothesis_a: [u8; 32],
    /// بصمة الفرضية أو القانون الثاني B
    pub hypothesis_b: [u8; 32],
    /// سبب النزاع المعرفي (مثل تناقض في حدود مجال ما أو تكافؤ نسبي غير محسوم)
    pub dispute_reason: String,
    /// راية الحصانة المعرفية (Epoché Immunity) - تحمي الطرفين من الحذف أثناء استمرار النزاع
    pub epoche_immunity: bool,
    /// الحقبة الزمنية أو الجيل المعرفي الذي نشأ فيه النزاع
    pub created_at_epoch: u64,
    /// معيار الحل المستهدف (مثل الانكماش التقاربي عند عتبة محددة)
    pub resolution_criterion: Option<String>,
    /// هل تم حسم النزاع
    pub is_resolved: bool,
    /// الفرضية الفائزة بعد الحسم (إن وجدت)
    pub winning_hypothesis: Option<[u8; 32]>,
    /// تعليل رياضي أو فيزيائي لحسم النزاع
    pub resolution_explanation: Option<String>,
}

impl DisputedPair {
    /// إنشاء نزاع معرفي جديد مع تفعيل حصانة التعليق المعرفي (UNCERTAIN_EPOCHE)
    pub fn new(
        hyp_a: [u8; 32],
        hyp_b: [u8; 32],
        reason: impl Into<String>,
        epoch: u64,
    ) -> Self {
        let pair_id = Self::compute_pair_id(&hyp_a, &hyp_b);
        Self {
            pair_id,
            hypothesis_a: hyp_a,
            hypothesis_b: hyp_b,
            dispute_reason: reason.into(),
            epoche_immunity: true,
            created_at_epoch: epoch,
            resolution_criterion: None,
            is_resolved: false,
            winning_hypothesis: None,
            resolution_explanation: None,
        }
    }

    /// حساب البصمة الكنسية للنزاع بشكل متناظر بغض النظر عن ترتيب (A, B)
    pub fn compute_pair_id(hyp_a: &[u8; 32], hyp_b: &[u8; 32]) -> [u8; 32] {
        let mut hasher = Hasher::new();
        hasher.update(b"ALETH_DISPUTE_V1");
        if hyp_a <= hyp_b {
            hasher.update(hyp_a);
            hasher.update(hyp_b);
        } else {
            hasher.update(hyp_b);
            hasher.update(hyp_a);
        }
        *hasher.finalize().as_bytes()
    }

    /// تعيين معيار الحسم
    pub fn with_resolution_criterion(mut self, criterion: impl Into<String>) -> Self {
        self.resolution_criterion = Some(criterion.into());
        self
    }

    /// فحص ما إذا كانت الفرضية تتمتع بحصانة النزاع حالياً
    pub fn protects_hypothesis(&self, hyp_id: &[u8; 32]) -> bool {
        self.epoche_immunity
            && !self.is_resolved
            && (*hyp_id == self.hypothesis_a || *hyp_id == self.hypothesis_b)
    }

    /// حسم النزاع بناءً على برهان رياضي أو تقارب حدي
    pub fn resolve(
        &mut self,
        winner: [u8; 32],
        explanation: impl Into<String>,
    ) {
        self.is_resolved = true;
        self.winning_hypothesis = Some(winner);
        self.resolution_explanation = Some(explanation.into());
        // عند الحسم، تُسقط حصانة النزاع للسماح للطرف الخاسر بالمعالجة أو الأرشفة
        self.epoche_immunity = false;
    }
}
