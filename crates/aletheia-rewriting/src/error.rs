use aletheia_algebra::FormalContradictionError;
use aletheia_egraph::{EClassId, EGraphError};
use aletheia_lattice::LatticeError;
use thiserror::Error;

/// أخطاء محرك التشبع والمطابقة وإعادة الكتابة (المحور 5)
#[derive(Debug, Error)]
pub enum RewritingError {
    #[error("تناقض صوري: رصد حلقة تكافؤ دائرية غير مؤسسة دون عقدة أرضية للفئة {0:?}")]
    FormalCycleContradiction(EClassId),

    #[error("تناقض كمي: تجاوز التكلفة للسقف الهيكلي لماكولاي (التكلفة الحالية: {current_cost}، السقف المسموح: {ceiling})")]
    QuantitativeContradiction {
        current_cost: String,
        ceiling: String,
    },

    #[error("استبعاد مسبق: إثبات استحالة الوصول للهدف عبر مصفوفة الوقوع وفاركاس في O(1)")]
    UnreachableTarget,

    #[error("استنفاد ميزانية الخطوات المحددة للتشبع")]
    BudgetExceeded,

    #[error("متغير النمط {0} غير موجود في جدول التعويضات Subst")]
    UnboundPatternVar(u32),

    #[error("خطأ الـ E-Graph: {0}")]
    EGraph(#[from] EGraphError),

    #[error("خطأ الشبكة الدلالية: {0}")]
    Lattice(#[from] LatticeError),

    #[error("خطأ جبري صوري: {0}")]
    Algebra(#[from] FormalContradictionError),
}
