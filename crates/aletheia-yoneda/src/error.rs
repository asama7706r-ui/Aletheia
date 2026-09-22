use thiserror::Error;

/// أخطاء فضاء يونيدا السالب ومفاعل الحجر الصحي المعرفي
#[derive(Debug, Error)]
pub enum YonedaError {
    #[error("تناقض منطقي/رياضي قاتل غير قابل للرتق: {0}")]
    FatalContradiction(String),

    #[error("نظام المعادلات البعدية الخطية غير متسق ومستحيل الحل في Q")]
    InconsistentLinearSystem,

    #[error("تجاوز سقف ماكولاي الاستباقي: الدرجة {current} تتجاوز السقف الآمن {ceiling}")]
    MacaulayCeilingExceeded { current: usize, ceiling: usize },

    #[error("خطأ في قراءة أو كتابة ملف الحجر الصحي: {0}")]
    StorageError(String),

    #[error("خطأ في محرك الـ E-Graph: {0}")]
    EGraphError(#[from] aletheia_egraph::EGraphError),

    #[error("خطأ في محرك إعادة الكتابة: {0}")]
    RewritingError(#[from] aletheia_rewriting::RewritingError),

    #[error("انكماش جبر لي منفرد ومتباعد (Singular Lie contraction): {0}")]
    SingularContraction(String),

    #[error("انتهاك متطابقة ياكوبي لجبر لي: {0}")]
    JacobiViolation(String),

    #[error("رفض الترقية إلى السيادة: {0}")]
    PromotionDenied(String),

    #[error("خطأ في تحليل مضلع نيوتن الاستوائي: {0}")]
    TropicalNewtonError(String),
}
