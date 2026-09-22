use crate::spectral_audit::DiagnosticVector;
use aletheia_algebra::Rational;
use aletheia_egraph::EClassId;
use aletheia_lattice::{DimensionVector, SemanticDomain};
use aletheia_rewriting::DeficitContext;

/// حامل الاقتران البعدي للجسور المعرفية (Dimensional Coupling Carrier: K in Mor(C))
/// يحمل التوقيع البعدي [K] = [B] * [A]^-1 لربط المجالات الفيزيائية عبر الختم الأول
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CouplingCarrier {
    /// اسم أو رمز كائن الاقتران (مثل c^2 أو hbar أو G)
    pub symbol: String,
    /// التوقيع البعدي الصافي لحامل الاقتران في فضاء Q^N
    pub dimension: DimensionVector,
    /// المجال الدلالي للاقتران
    pub domain: SemanticDomain,
}

impl CouplingCarrier {
    pub fn new(symbol: impl Into<String>, dimension: DimensionVector, domain: SemanticDomain) -> Self {
        Self {
            symbol: symbol.into(),
            dimension,
            domain,
        }
    }
}

/// العقد البياني الحتمي لظل يونيدا السالب (LatentShadow Data Contract)
/// يحمل التمثيل المعياري الصرف للعجز الهيكلي السالب دون أي تشتت أو انشطار
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct LatentShadow {
    /// بصمة BLAKE3 الحتمية للنموذج المعياري الصرف
    pub shadow_id: [u8; 32],
    /// سلسلة القوانين المصدرية المولدة للظل (Provenance DAG)
    pub origin_law_ids: Vec<String>,
    /// متجه العجز البعدي الصافي في فضاء Q^N
    pub dim_deficit: DimensionVector,
    /// الرتبة التنسورية المطلوبة (0: قياسي، 1: متجه، 2: تنسور)
    pub tensorial_rank: usize,
    /// درجات الحرية الصافية في حقل الأعداد النسبية Q (يقبل قيماً كسرية مثل 1/2 أو 1/3)
    pub dof: Rational,
    /// المتجه التشخيصي الرباعي للأقفال [d1, d2, d3, d4]
    pub spectral_audit: DiagnosticVector,
    /// كائن الاقتران البعدي إن كانت الفرضية جسراً بين مجالين
    pub coupling_carrier: Option<CouplingCarrier>,
    /// فئات التكافؤ المستهدفة لتوجيه محرك التشبع في المحور الخامس
    pub target_classes: Vec<EClassId>,
    /// سقف ماكولاي الاستباقي المشتق رياضياً
    pub macaulay_ceiling: usize,
}

impl LatentShadow {
    /// إنشاء ظل كامن جديد
    pub fn new(
        origin_law_ids: Vec<String>,
        dim_deficit: DimensionVector,
        tensorial_rank: usize,
        dof: Rational,
        target_classes: Vec<EClassId>,
    ) -> Self {
        let macaulay_ceiling = 10;
        let shadow_id = Self::compute_canonical_id(&dim_deficit, tensorial_rank, &dof, macaulay_ceiling);
        Self {
            shadow_id,
            origin_law_ids,
            dim_deficit,
            tensorial_rank,
            dof,
            spectral_audit: DiagnosticVector::default(),
            coupling_carrier: None,
            target_classes,
            macaulay_ceiling,
        }
    }

    /// حساب البصمة المعيارية الحتمية عبر BLAKE3
    pub fn compute_canonical_id(
        dim_deficit: &DimensionVector,
        tensorial_rank: usize,
        dof: &Rational,
        macaulay_ceiling: usize,
    ) -> [u8; 32] {
        let mut hasher = blake3::Hasher::new();
        hasher.update(b"LATENT_SHADOW_V1");
        for (idx, coord) in dim_deficit.coords().iter().enumerate() {
            if !coord.is_zero() {
                hasher.update(&idx.to_le_bytes());
                hasher.update(coord.to_string().as_bytes());
            }
        }
        hasher.update(&tensorial_rank.to_le_bytes());
        hasher.update(dof.to_string().as_bytes());
        hasher.update(&macaulay_ceiling.to_le_bytes());
        *hasher.finalize().as_bytes()
    }
}

/// إغلاق حلقة التغذية الراجعة مع المحور الخامس:
/// يتيح لمحرك التشبع في المحور 5 استهلاك سياق العجز مباشرة من ظل يونيدا
impl DeficitContext for LatentShadow {
    fn remaining_dof(&self) -> usize {
        if self.dof.is_zero() {
            0
        } else {
            // تقريب درجات الحرية الكسرية (مثل 1/2 أو 1/3) إلى سقفها كدرجات صحيحة للتوجيه
            let numer = self.dof.numer();
            let denom = self.dof.denom();
            let one = num_bigint::BigInt::from(1);
            let div_ceil: num_bigint::BigInt = (numer + denom - &one) / denom;
            div_ceil.iter_u64_digits().next().unwrap_or(1).max(1) as usize
        }
    }

    fn target_classes(&self) -> &[EClassId] {
        &self.target_classes
    }

    fn macaulay_bound(&self) -> usize {
        self.macaulay_ceiling
    }
}
