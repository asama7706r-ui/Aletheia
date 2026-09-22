//! # 🌐 حزمة الشبكة الدلالية والأبعاد الكونية (`aletheia-lattice`)
//! الطبقة الأولى الوسيطة (Layer 1) وفق ميثاق المحور الثالث في Notion
//!
//! تضمن هذه الحزمة:
//! 1. **فضاء الشبكيات النسبي Q^N:** تمثيل دقيق لمتجهات الأبعاد `DimensionVector` بدقة حقل Q مع Zero-Extension Rule.
//! 2. **سجل الأبعاد الكونية (`DimensionRegistry`):** دعم الأبعاد السبعة الأساسية SI-7 والتوسع المتعامد للأبعاد الجديدة.
//! 3. **محرك الحذف الغاوسي النسبي الصرف (`RationalMatrix` و RREF):** حساب الفضاء الصفري بدقة كسريّة تامة دون أي فواصل عائمة.
//! 4. **محرك نظرية باكنغهام باي (`BuckinghamPiEngine`):** استخراج المجموعات اللابُعدية وتوليد القوانين الفيزيائية الخالية من الوحدات.
//! 5. **مستنتج ثوابت الاقتران وسد الفجوات البُعدية:** اشتقاق الثوابت الكونية (G, h, k_e) تلقائياً.
//! 6. **حارس القبول الدلالي الصارم (`SemanticGuard` و `DimensionalContext`):** فرض التجانس الجمعي وحظر الأبعاد في متسلسلات تايلور.
//! 7. **تكامل الـ E-Graph:** كائن `LatticeData` ودالة `merge` لفرض التراجع المعاملاتي الفوري عند تعارض الأبعاد.

pub mod buckingham;
pub mod coupling;
pub mod egraph_data;
pub mod error;
pub mod guard;
pub mod registry;
pub mod rref;
pub mod vector;

// Re-exports
pub use buckingham::{BuckinghamPiEngine, DimensionlessGroup, PhysicalVariable};
pub use coupling::{
    calculate_dimensional_gap, synthesize_coulomb_ke, synthesize_coupling_constant,
    synthesize_newton_g, synthesize_planck_h,
};
pub use egraph_data::{LatticeData, SemanticDomain};
pub use error::LatticeError;
pub use guard::{DimensionalContext, SemanticGuard};
pub use registry::{DimensionId, DimensionRegistry};
pub use rref::RationalMatrix;
pub use vector::DimensionVector;
