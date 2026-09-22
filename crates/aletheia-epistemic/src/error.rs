use thiserror::Error;

/// شجرة أخطاء واستثناءات الحراسة الإبستمولوجية وبوابات الحقيقة
#[derive(Error, Debug)]
pub enum EpistemicError {
    #[error("خرق في قفل البواقي الصفرية (Seal 1): {0}")]
    ResidualViolation(String),

    #[error("خرق في قفل التجانس البعدي (Seal 2): {0}")]
    DimensionalClash(String),

    #[error("خرق في قفل عزل المجالات (Seal 3): {0}")]
    DomainIsolationViolation(String),

    #[error("لا يوجد مسار جسر معتمد يربط بين المجالين: {0}")]
    BridgeNotFound(String),

    #[error("خرق في قفل التجذير الأنطولوجي (Seal 4): {0}")]
    OntologicalAnchorViolation(String),

    #[error("تناقض صريح غير قابل للحل: {0}")]
    FormalContradiction(String),

    #[error("رصد نزاع إبستمولوجي مع المعرفة القائمة (Dispute): {0}")]
    DisputeDetected(String),

    #[error("رفض بروتوكول التدشين التوليدي (Meta-Admission): {0}")]
    MetaAdmissionRejected(String),

    #[error("رفض بواسطة غربال مناهضة بطليموس (Anti-Ptolemaic): {0}")]
    PtolemaicOverfitting(String),

    #[error("خطأ في التحكيم الإبستمولوجي (Arbitration): {0}")]
    ArbitrationError(String),

    #[error("خطأ في محرك الـ E-Graph: {0}")]
    EGraphError(#[from] aletheia_egraph::EGraphError),

    #[error("خطأ في شبيكة الأبعاد الدلالية: {0}")]
    LatticeError(#[from] aletheia_lattice::LatticeError),

    #[error("خطأ في فضاء يونيدا والحجر الصحي: {0}")]
    YonedaError(#[from] aletheia_yoneda::YonedaError),
}
