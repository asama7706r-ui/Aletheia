use aletheia_algebra::CanonicalExpr;
use aletheia_egraph::TransactionalEGraph;
use aletheia_lattice::{DimensionVector, DimensionalContext, SemanticGuard};

/// المتجه التشخيصي الرباعي للأقفال الإبستمولوجية [d1, d2, d3, d4]
#[derive(Copy, Clone, Debug, PartialEq, Eq, Default)]
pub struct DiagnosticVector {
    /// عجز التجانس البعدي (Dimensional Deficit)
    pub d1: usize,
    /// عجز المطابقة الجبرية الهيكلية (Algebraic / Structural Gap)
    pub d2: usize,
    /// عجز عزل المجالات والجسور (Domain Bridge Deficit)
    pub d3: usize,
    /// عجز التجذير والرسوخ التناظري / التناقض (Contradiction / Anchor Deficit)
    pub d4: usize,
}

impl DiagnosticVector {
    pub fn new(d1: usize, d2: usize, d3: usize, d4: usize) -> Self {
        Self { d1, d2, d3, d4 }
    }

    /// هل توجد إدانة بتناقض قاتل غير قابل للرتق (مثل 1 = 0)؟
    pub fn has_fatal_contradiction(&self) -> bool {
        self.d4 > 0
    }

    /// هل يوجد عجز هيكلي أو بعدي قابل للرتق في فضاء يونيدا السالب؟
    pub fn has_reparable_deficit(&self) -> bool {
        !self.has_fatal_contradiction() && (self.d1 > 0 || self.d2 > 0 || self.d3 > 0)
    }

    /// هل اجتاز التكافؤ كافة الأقفال الأربعة بنقاء تام؟
    pub fn is_pure_identity(&self) -> bool {
        self.d1 == 0 && self.d2 == 0 && self.d3 == 0 && self.d4 == 0
    }
}

/// المدقق الطيفي الموازي للأقفال الأربعة (Parallel Spectral Auditor)
/// يعمل بنمط المجس التشخيصي O(1) فوق فضاء التكافؤات
pub struct ParallelSpectralAuditor;

impl ParallelSpectralAuditor {
    /// فحص التكافؤ بين تعبيرين رياضيين وإصدار المتجه التشخيصي الرباعي
    pub fn audit_equivalence(
        egraph: &TransactionalEGraph,
        ctx: &DimensionalContext,
        lhs: &CanonicalExpr,
        rhs: &CanonicalExpr,
    ) -> DiagnosticVector {
        let mut d1 = 0;
        let mut d2 = 0;
        // TODO: ربط القفل الثالث d3 بفحص الجسور ومطابقة المجالات الدلالية SemanticDomain بين أطراف التكافؤ
        let d3 = 0;
        let mut d4 = 0;

        // 1. فحص التناقض القاتل الصريح (1 = 0 أو ثوابت غير متساوية)
        if let (CanonicalExpr::Const(c1), CanonicalExpr::Const(c2)) = (lhs, rhs) {
            if c1 != c2 {
                d4 = 1;
                return DiagnosticVector::new(d1, d2, d3, d4);
            }
        }

        // 2. فحص التجانس البعدي (القفل الأول / d1)
        let dim_lhs = SemanticGuard::infer_dimension(lhs, ctx).unwrap_or_else(|_| DimensionVector::dimensionless());
        let dim_rhs = SemanticGuard::infer_dimension(rhs, ctx).unwrap_or_else(|_| DimensionVector::dimensionless());

        if dim_lhs != dim_rhs {
            // وجود عجز بعدي قابل للرتق عبر حامل اقتران
            d1 = 1;
        }

        // 3. فحص التطابق الهيكلي والتكافؤ في شجرة المعرفة (القفل الثاني / d2)
        if lhs != rhs {
            // إذا لم يتطابقا لفظياً، نفحص هل ينتميان لنفس صنف التكافؤ في الـ E-Graph
            let in_same_class = match (egraph.lookup_expr(lhs), egraph.lookup_expr(rhs)) {
                (Some(c1), Some(c2)) => c1 == c2,
                _ => false,
            };

            if !in_same_class {
                d2 = 1;
            }
        }

        DiagnosticVector::new(d1, d2, d3, d4)
    }
}
