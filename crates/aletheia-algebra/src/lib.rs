//! # 🧮 حزمة الجبر الدقيق والرياضيات الصرفة (`aletheia-algebra`)
//! النواة البديهية التأسيسية للطبقة الصفرية (Layer 0) وفق ميثاق المحور الثاني
//!
//! تضمن هذه الحزمة:
//! 1. **الصفر العائم المطلق (`Zero Float Drift`):** حساب كسري تام ودقيق في حقل Q عبر كائن `Rational` المصمت.
//! 2. **المونوميات المجردة الخالية من الـ Heap Allocations:** تمثيل المتغيرات بـ `VariableId` رقمي صرف.
//! 3. **ترتيب المونوميات الصارم:** `DegRevLex`, `Lex`, `DegLex`.
//! 4. **كثيرات الحدود متعددة المتغيرات وخوارزمية القسمة:** مع تكامل كامل مع شجرة التعبيرات الكنسية `CanonicalExpr`.
//! 5. **محرك أسس غروبنر المختزلة:** مع سقف ماكولاي وميزانية الحساب `GrobnerConfig` للحصانة ضد الانفجار التوافقي.
//! 6. **بديهية كوزول للتناظر الموتري المدرج:** إشارة التبادل $(-1)^{\text{deg}(a)\cdot\text{deg}(b)}$.
//! 7. **التفاضل الرمزي التام:** بديهيات لايبنتز والخطية الصرفة.

pub mod derivation;
pub mod error;
pub mod grobner;
pub mod koszul;
pub mod monomial;
pub mod polynomial;
pub mod rational;

// Re-exports
pub use derivation::{diff_multi, diff_var, verify_leibniz_rule};
pub use error::FormalContradictionError;
pub use grobner::{buchberger, reduced_grobner_basis, s_polynomial, GrobnerConfig};
pub use koszul::{
    can_contract_einstein, koszul_parity_rational, koszul_parity_sign, ContravariantIndex,
    CovariantIndex, GradedElement,
};
pub use monomial::{Monomial, MonomialOrder, VariableId};
pub use polynomial::{CanonicalExpr, Polynomial, Term};
pub use rational::Rational;
