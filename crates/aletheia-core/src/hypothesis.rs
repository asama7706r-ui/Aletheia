use aletheia_algebra::{CanonicalExpr, Rational};
use aletheia_epistemic::{DomainTag, SovereignReceipt};
use aletheia_lattice::DimensionVector;
use aletheia_rewriting::Cost;

/// مدخلات فرضية أو قانون فيزيائي/معرفي يُقدم للنواة
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct HypothesisInput {
    pub law_id: String,
    pub expr: CanonicalExpr,
    pub domain: DomainTag,
    pub dimension: DimensionVector,
    pub cost: Option<Cost>,
    pub epoch: u64,
}

impl HypothesisInput {
    pub fn new(
        law_id: impl Into<String>,
        expr: CanonicalExpr,
        domain: DomainTag,
        dimension: DimensionVector,
    ) -> Self {
        Self {
            law_id: law_id.into(),
            expr,
            domain,
            dimension,
            cost: None,
            epoch: 1,
        }
    }

    pub fn with_cost(mut self, cost: Cost) -> Self {
        self.cost = Some(cost);
        self
    }

    pub fn with_epoch(mut self, epoch: u64) -> Self {
        self.epoch = epoch;
        self
    }
}

/// النتيجة الدستورية النهائية لمعالجة الفرضية عبر خط الأنابيب الكوني
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum HypothesisOutcome {
    /// تم قبول الفرضية كقانون سيادي راسخ وثبتت في ركيزة الـ DNA
    SovereignAnchored {
        receipt: Box<SovereignReceipt>,
        class_id: u32,
    },

    /// فرضية غير مكتملة بعدياً أو جبرياً واحتُجزت في حجر فضاء يونيدا الصحي لإنضاجها
    QuarantinedInYoneda {
        deficit: Box<DimensionVector>,
        dof: Rational,
        reason: String,
    },

    /// نزاع معرفي لم يُحسم وعُلّق حكمه تحت مبدأ Epoché في محكمة التحكيم
    DisputedAndSuspended {
        reason: String,
    },

    /// رُفضت الفرضية دستورياً لوجود تناقض حتمي أو انتهاك لقفل تجانس
    RejectedContradiction {
        reason: String,
    },
}
