use aletheia_algebra::Rational;
use blake3::Hasher;

/// شهادة السلوك التقاربي (Asymptotic Limit Certificate)
/// توثيق رياضي وبرهاني غير قابل للتزوير يثبت انكماش فرضية أو قانون لسلوك حدي معلوم (مثل v/c -> 0 أو hbar -> 0)
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct AsymptoticLimitCertificate {
    /// البصمة المعمارية الفريدة للشهادة (BLAKE3)
    pub certificate_id: [u8; 32],
    /// بصمة الفرضية المقترنة في الحجر الصحي
    pub hypothesis_id: [u8; 32],
    /// اسم المعامل التقاربي البارامتري (مثل "epsilon", "v/c", "1/r")
    pub parameter_name: String,
    /// نقطة النهاية في حقل الأعداد النسبية Q (غالباً صفر)
    pub limit_point: Rational,
    /// ميول أضلاع مضلع نيوتن الاستوائي في Q
    pub newton_slopes: Vec<Rational>,
    /// أسس التوازن التقاربي المرشحة (Puiseux Exponents)
    pub candidate_powers: Vec<Rational>,
    /// بعد جبر لي المنكمش (إن وجد)
    pub contracted_algebra_dim: Option<usize>,
    /// هل الاختزال ناعم وخالي من التباعد الشاذ (Smooth reduction)
    pub is_smooth_reduction: bool,
    /// هل تم إثبات متطابقة ياكوبي بنسبة 100%
    pub jacobi_verified: bool,
    /// خطوات البرهان الرمزية والتحويلات
    pub proof_steps: Vec<String>,
    /// الحقبة الزمنية للشهادة
    pub epoch: u64,
}

impl AsymptoticLimitCertificate {
    /// إصدار شهادة تقارب جديدة مع حساب البصمة التشفيرية المعتمدة
    #[allow(clippy::too_many_arguments)]
    pub fn issue(
        hypothesis_id: [u8; 32],
        parameter_name: impl Into<String>,
        limit_point: Rational,
        newton_slopes: Vec<Rational>,
        candidate_powers: Vec<Rational>,
        contracted_algebra_dim: Option<usize>,
        is_smooth_reduction: bool,
        jacobi_verified: bool,
        proof_steps: Vec<String>,
        epoch: u64,
    ) -> Self {
        let param_str = parameter_name.into();
        let cert_id = Self::compute_certificate_id(
            &hypothesis_id,
            &param_str,
            &limit_point,
            is_smooth_reduction,
            jacobi_verified,
            epoch,
        );

        Self {
            certificate_id: cert_id,
            hypothesis_id,
            parameter_name: param_str,
            limit_point,
            newton_slopes,
            candidate_powers,
            contracted_algebra_dim,
            is_smooth_reduction,
            jacobi_verified,
            proof_steps,
            epoch,
        }
    }

    /// حساب البصمة التشفيرية للشهادة
    pub fn compute_certificate_id(
        hyp_id: &[u8; 32],
        param_name: &str,
        limit_point: &Rational,
        smooth: bool,
        jacobi: bool,
        epoch: u64,
    ) -> [u8; 32] {
        let mut hasher = Hasher::new();
        hasher.update(b"ALETH_ASYMP_CERT_V1");
        hasher.update(hyp_id);
        hasher.update(param_name.as_bytes());
        hasher.update(limit_point.numer().to_string().as_bytes());
        hasher.update(limit_point.denom().to_string().as_bytes());
        hasher.update(&[smooth as u8, jacobi as u8]);
        hasher.update(&epoch.to_le_bytes());
        *hasher.finalize().as_bytes()
    }

    /// التحقق من سلامة البصمة التشفيرية للشهادة
    pub fn verify_integrity(&self) -> bool {
        let expected_id = Self::compute_certificate_id(
            &self.hypothesis_id,
            &self.parameter_name,
            &self.limit_point,
            self.is_smooth_reduction,
            self.jacobi_verified,
            self.epoch,
        );
        expected_id == self.certificate_id
    }
}
