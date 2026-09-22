use crate::asymptotic_cert::AsymptoticLimitCertificate;
use crate::error::YonedaError;
use crate::quarantine_buffer::LatentBuffer;
use crate::shadow::LatentShadow;
use aletheia_algebra::CanonicalExpr;
use aletheia_lattice::DimensionVector;
use aletheia_rewriting::Cost;

/// عقد المرشح السيادي للقانون الفيزيائي / الرياضي (CandidateSovereignLawAST)
/// يمثل الفرضية بعد تصفير درجات حريتها بالكامل (dof == 0) وتطهيرها من صفة الحجر الصحي
/// لتسليمها لحوكمة النواة المعرفية في المحور السابع
#[derive(Clone, Debug, PartialEq)]
pub struct CandidateSovereignLawAST {
    /// البصمة المعمارية الكنسية للقانون (BLAKE3)
    pub canonical_id: [u8; 32],
    /// التعبير الرياضي الكنسي الصافي
    pub ast: CanonicalExpr,
    /// التوقيع البعدي المصادق عليه متجانساً من المحور 3
    pub dim: DimensionVector,
    /// تكلفة التعقيد المعرفي وفق نصل أوكام (MDL Complexity)
    pub cost: Cost,
    /// سجل البراهين المتسلسل ومسار التحولات الجبرية
    pub proof_trace: Vec<String>,
    /// شهادة السلوك التقاربي (إن تمت عبر الانكماش أو حدود الأبعاد)
    pub asymptotic_certificate: Option<AsymptoticLimitCertificate>,
    /// حقبة الترقية السيادية
    pub sovereignty_epoch: u64,
}

/// بوابة الترقية السيادية الذرية (Atomic Sovereign Promotion Pipeline)
/// تسحب الفرضيات من الحجر الصحي فور إطفاء درجات حريتها dof == 0 وتؤهلها كقوانين سيادية
pub struct SovereignPromotionPipeline;

impl SovereignPromotionPipeline {
    /// ترقية سجل حجر صحي مكتمل إلى قانون سيادي مرشح
    #[allow(clippy::too_many_arguments)]
    pub fn promote_record(
        buffer: &mut LatentBuffer,
        record_id: &[u8; 32],
        ast: CanonicalExpr,
        dim: DimensionVector,
        cost: Cost,
        proof_trace: Vec<String>,
        asymptotic_certificate: Option<AsymptoticLimitCertificate>,
        epoch: u64,
    ) -> Result<CandidateSovereignLawAST, YonedaError> {
        // التحقق من وجود السجل في الحجر
        let record = buffer
            .get(record_id)
            .cloned()
            .ok_or_else(|| YonedaError::PromotionDenied("السجل غير موجود في الحجر الصحي".into()))?;

        // الفحص الدستوري الأول: درجات الحرية يجب أن تكون صفراً تماماً
        if !record.remaining_dof.is_zero() {
            return Err(YonedaError::PromotionDenied(format!(
                "لا يمكن الترقية: درجات الحرية لا زالت كسرية/موجبة (dof = {})",
                record.remaining_dof
            )));
        }

        // سحب السجل ذرياً من الحجر الصحي (إسقاط صفة NON_SOVEREIGN)
        buffer.remove(record_id);

        Ok(CandidateSovereignLawAST {
            canonical_id: record.record_id,
            ast,
            dim,
            cost,
            proof_trace,
            asymptotic_certificate,
            sovereignty_epoch: epoch,
        })
    }

    /// ترقية كائن LatentShadow مباشرة فور استيفاء قيوده
    pub fn promote_shadow(
        shadow: &LatentShadow,
        ast: CanonicalExpr,
        dim: DimensionVector,
        cost: Cost,
        proof_trace: Vec<String>,
        asymptotic_certificate: Option<AsymptoticLimitCertificate>,
        epoch: u64,
    ) -> Result<CandidateSovereignLawAST, YonedaError> {
        if !shadow.dof.is_zero() {
            return Err(YonedaError::PromotionDenied(format!(
                "درجات الحرية للظل لا زالت موجبة (dof = {})",
                shadow.dof
            )));
        }

        Ok(CandidateSovereignLawAST {
            canonical_id: shadow.shadow_id,
            ast,
            dim,
            cost,
            proof_trace,
            asymptotic_certificate,
            sovereignty_epoch: epoch,
        })
    }
}
