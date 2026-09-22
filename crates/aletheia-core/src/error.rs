use thiserror::Error;

/// أخطاء المنسق السيادي الشامل للنواة (Aletheia Core Errors)
#[derive(Error, Debug)]
pub enum CoreError {
    #[error("خطأ ركيزة الـ DNA وتخزين الجينوم: {0}")]
    Dna(#[from] aletheia_dna::DnaError),

    #[error("خطأ منظومة السيادة والتحكيم المعرفي: {0}")]
    Epistemic(#[from] aletheia_epistemic::EpistemicError),

    #[error("خطأ فضاء يونيدا السالب والحجر الصحي: {0}")]
    Yoneda(#[from] aletheia_yoneda::YonedaError),

    #[error("خطأ محرك إعادة الكتابة والتشبع: {0}")]
    Rewriting(#[from] aletheia_rewriting::RewritingError),

    #[error("خطأ بيان الـ E-Graph: {0}")]
    EGraph(#[from] aletheia_egraph::EGraphError),

    #[error("خطأ شبكة الأبعاد الفيزيائية: {0}")]
    Lattice(#[from] aletheia_lattice::LatticeError),

    #[error("خطأ الحقل الجبري والحساب الكسري: {0}")]
    Algebra(#[from] aletheia_algebra::FormalContradictionError),

    #[error("خطأ إدخال/إخراج أو نظام تشغيل: {0}")]
    Io(String),

    #[error("تم رفض الفرضية المعرفية دستورياً: {0}")]
    HypothesisRejected(String),
}
