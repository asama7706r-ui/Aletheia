use crate::pattern::{Pattern, Subst};
use aletheia_egraph::{ENode, TransactionalEGraph};
use std::sync::Arc;

/// التصنيف الثنائي الصارم لهوية القواعد (RuleKind)
/// يفصل دستورياً بين الاختزال الكنسي الحتمي والتوسع الموجه بالعجز
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum RuleKind {
    /// قواعد الاختزال القاطعة: تُنقص التكلفة دائماً وتقرب التعبير نحو صورته القياسية
    /// تعمل بحرية تامة وبأعلى أولوية حتى الوصول إلى نقطة الثبات (Fixpoint)
    CanonicalReduction,

    /// قواعد التوسع الهيكلي الموجه: قد تزيد التكلفة ظاهرياً وتفكك البنية الرياضية
    /// لا تُطلق إلا عند وجود عجز هيكلي وتحت سقف دفتر الأستاذ وسقف ماكولاي
    DemandExpansion,
}

/// دالة حارس مخصصة
pub type CustomGuardFn = Arc<dyn Fn(&TransactionalEGraph, &Subst) -> bool + Send + Sync>;

/// حارس إشارة كوزول وغراسمان المدرجة (Koszul Graded Parity Guard)
/// يربط بديهية كوزول (المحور 2) بمحرك المطابقة والتشبع (المحور 5)
/// يضمن احترام إشارة التبادل: (-1)^(grade_a * grade_b) == expected_sign
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct KoszulParityGuard {
    pub var_a: u32,
    pub var_b: u32,
    pub grade_a: u32,
    pub grade_b: u32,
    pub expected_sign: i8,
}

impl KoszulParityGuard {
    pub fn new(var_a: u32, var_b: u32, grade_a: u32, grade_b: u32, expected_sign: i8) -> Self {
        Self {
            var_a,
            var_b,
            grade_a,
            grade_b,
            expected_sign,
        }
    }

    /// التحقق من مطابقة إشارة كوزول المحسوبة في حقل الجبر الصرف مع الإشارة المتوقعة
    pub fn check(&self, _egraph: &TransactionalEGraph, subst: &Subst) -> bool {
        if subst.get(self.var_a).is_none() || subst.get(self.var_b).is_none() {
            return false;
        }
        let sign = aletheia_algebra::koszul::koszul_parity_sign(self.grade_a, self.grade_b);
        sign == self.expected_sign
    }
}

/// الحراس البنيويون لقواعد إعادة الكتابة (Structural Guards)
#[derive(Clone)]
pub enum RuleGuard {
    /// حارس رياضي: التحقق من عدم صفرية فئة تكافؤ معينة لمنع القسمة على صفر أو انهيار 0 = 1
    NonZero(u32),

    /// حارس إشارة كوزول وغراسمان للتناظر الموتري المدرج (المحور 2 -> المحور 5)
    KoszulParity(KoszulParityGuard),

    /// حارس مخصص لأي شرط رياضي أو دلالي إضافي
    Custom(CustomGuardFn),
}

impl RuleGuard {
    /// مساعد لإنشاء حارس كوزول بسرعة
    pub fn koszul(var_a: u32, var_b: u32, grade_a: u32, grade_b: u32, expected_sign: i8) -> Self {
        RuleGuard::KoszulParity(KoszulParityGuard::new(var_a, var_b, grade_a, grade_b, expected_sign))
    }
}

impl std::fmt::Debug for RuleGuard {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            RuleGuard::NonZero(v) => write!(f, "NonZero(?{})", v),
            RuleGuard::KoszulParity(k) => write!(
                f,
                "KoszulParity(?{}, ?{}, grades=({}, {}), sign={})",
                k.var_a, k.var_b, k.grade_a, k.grade_b, k.expected_sign
            ),
            RuleGuard::Custom(_) => write!(f, "CustomGuard(...)"),
        }
    }
}

/// قاعدة إعادة الكتابة الكنسية (Canonical Rewrite Rule)
#[derive(Clone, Debug)]
pub struct RewriteRule {
    pub name: &'static str,
    pub kind: RuleKind,
    pub lhs: Pattern,
    pub rhs: Pattern,
    pub guards: Vec<RuleGuard>,
}

impl RewriteRule {
    /// إنشاء قاعدة جديدة
    pub fn new(name: &'static str, kind: RuleKind, lhs: Pattern, rhs: Pattern) -> Self {
        Self {
            name,
            kind,
            lhs,
            rhs,
            guards: Vec::new(),
        }
    }

    /// إضافة حارس للقاعدة
    pub fn with_guard(mut self, guard: RuleGuard) -> Self {
        self.guards.push(guard);
        self
    }

    /// توليد زوج قواعد ثنائي الاتجاه من قانون سيادي متوج (LHS = RHS)
    /// 1. قاعدة اختزال كنسي (CanonicalReduction): LHS -> RHS
    /// 2. قاعدة توسع موجه بالعجز (DemandExpansion): RHS -> LHS
    pub fn from_sovereign_law(
        law_id: &str,
        lhs: &aletheia_algebra::CanonicalExpr,
        rhs: &aletheia_algebra::CanonicalExpr,
    ) -> (Self, Self) {
        let pat_lhs = Pattern::from_canonical_expr(lhs);
        let pat_rhs = Pattern::from_canonical_expr(rhs);

        let fwd_name = Box::leak(format!("Rule_Sovereign_{}_Fwd", law_id).into_boxed_str());
        let rev_name = Box::leak(format!("Rule_Sovereign_{}_Rev", law_id).into_boxed_str());

        let fwd = RewriteRule::new(fwd_name, RuleKind::CanonicalReduction, pat_lhs.clone(), pat_rhs.clone());
        let rev = RewriteRule::new(rev_name, RuleKind::DemandExpansion, pat_rhs, pat_lhs);

        (fwd, rev)
    }

    /// فحص كافة حراس القاعدة على التعويض المعطى
    pub fn check_guards(&self, egraph: &TransactionalEGraph, subst: &Subst) -> bool {
        for guard in &self.guards {
            match guard {
                RuleGuard::NonZero(var_id) => {
                    if let Some(cid) = subst.get(*var_id) {
                        let canon = egraph.find(cid);
                        if let Some(class) = egraph.classes.get(&canon) {
                            // إذا كانت الفئة تحتوي على الثابت 0، يفشل الحارس
                            for node in &class.nodes {
                                if let ENode::Const(c) = node {
                                    if c.is_zero() {
                                        return false;
                                    }
                                }
                            }
                        }
                    } else {
                        return false;
                    }
                }
                RuleGuard::KoszulParity(guard) => {
                    if !guard.check(egraph, subst) {
                        return false;
                    }
                }
                RuleGuard::Custom(predicate) => {
                    if !predicate(egraph, subst) {
                        return false;
                    }
                }
            }
        }
        true
    }
}

/// قاعدة عليا مركبة مستخلصة من عبور الهضاب (Synthesized Macro-Rule - المحور 5 القسم 1.6)
/// تخلد المسارات الاشتقاقية المعقدة لتصبح قفزة فورية O(1)
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct MacroRule {
    pub name: String,
    pub lhs: Pattern,
    pub rhs: Pattern,
}

impl MacroRule {
    pub fn new(name: impl Into<String>, lhs: Pattern, rhs: Pattern) -> Self {
        Self {
            name: name.into(),
            lhs,
            rhs,
        }
    }
}
