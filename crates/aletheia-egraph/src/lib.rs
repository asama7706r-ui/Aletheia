//! # 🧱 حزمة الـ E-Graph المعاملاتية الصرفة ومصفوفات الذاكرة (`aletheia-egraph`)
//! الطبقة الثانية (Layer 2) وفق ميثاق المحور الرابع في Notion
//!
//! تضمن هذه الحزمة:
//! 1. **المفاعل الاستكشافي الذري (Speculative Sandbox):** دعم طرح الفرضيات والتراجع اللحظي التام (`Bit-Exact Rollback`).
//! 2. **الهياكل الكنسية الأربعة:** مستودع الفئات، شجرة الاتحاد والبحث العكسية، جدول التجزئة الكنسي، ومؤشرات الآباء.
//! 3. **الفرز الكنسي للعمليات التبادلية:** فرز معاملات `Add` و `Mul` لدمج $a+b$ مع $b+a$ فورياً دون قواعد تحويل.
//! 4. **سجل التراجع ونقاط التفتيش (`UndoJournal`):** تعقب كل عملية عكسية بنسبة 100%.
//! 5. **التكامل الدلالي مع المحور الثالث (`LatticeData`):** إطلاق التراجع الذري فوراً عند أي تعارض في الأبعاد الفيزيائية.
//! 6. **مدير سياق المعاملات (`Transaction`):** نمط RAII لضمان طهارة الذاكرة ضد أي استثناء أو انقطاع.

pub mod eclass;
pub mod egraph;
pub mod error;
pub mod id;
pub mod node;
pub mod transaction;
pub mod undo;
pub mod union_find;

// Re-exports
pub use eclass::EClass;
pub use egraph::TransactionalEGraph;
pub use error::EGraphError;
pub use id::EClassId;
pub use node::ENode;
pub use transaction::Transaction;
pub use undo::{UndoJournal, UndoOp};
pub use union_find::UnionFind;
