use aletheia_algebra::{CanonicalExpr, VariableId};
use std::collections::HashMap;

/// تمثيل النظرية الفوقية المستخلصة عبر التوحيد العكسي (Plotkin's LGG Meta-Theorem)
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct MetaTheorem {
    pub meta_id: String,
    pub generalized_expr: CanonicalExpr,
    pub source_laws: Vec<(String, u16)>, // (اسم القانون، معرف المجال)
    pub left_substitution: HashMap<VariableId, CanonicalExpr>,
    pub right_substitution: HashMap<VariableId, CanonicalExpr>,
}

/// محرك التوحيد العكسي الشامل (Plotkin's Anti-Unification Engine)
#[derive(Default)]
pub struct AntiUnifier {
    next_var_id: u32,
    memo: HashMap<(CanonicalExpr, CanonicalExpr), VariableId>,
    left_subst: HashMap<VariableId, CanonicalExpr>,
    right_subst: HashMap<VariableId, CanonicalExpr>,
}

impl AntiUnifier {
    pub fn new(start_var_id: u32) -> Self {
        Self {
            next_var_id: start_var_id,
            memo: HashMap::new(),
            left_subst: HashMap::new(),
            right_subst: HashMap::new(),
        }
    }

    /// تنفيذ خوارزمية بلوتكين لاستخراج التعميم الأقل عمومية (LGG)
    pub fn anti_unify(
        left: &CanonicalExpr,
        right: &CanonicalExpr,
    ) -> (
        CanonicalExpr,
        HashMap<VariableId, CanonicalExpr>,
        HashMap<VariableId, CanonicalExpr>,
    ) {
        let mut unifier = Self::new(1000); // تخصيص معرفات المتغيرات الفوقية بدءاً من 1000
        let generalized = unifier.lgg_recursive(left, right);
        (generalized, unifier.left_subst, unifier.right_subst)
    }

    /// استقراء وصياغة نظرية فوقية بين قانونين من مجالين مختلفين
    #[allow(clippy::too_many_arguments)]
    pub fn synthesize_meta_theorem(
        meta_id: impl Into<String>,
        law_a: &str,
        domain_a: u16,
        expr_a: &CanonicalExpr,
        law_b: &str,
        domain_b: u16,
        expr_b: &CanonicalExpr,
    ) -> MetaTheorem {
        let (generalized_expr, left_substitution, right_substitution) =
            Self::anti_unify(expr_a, expr_b);

        MetaTheorem {
            meta_id: meta_id.into(),
            generalized_expr,
            source_laws: vec![
                (law_a.to_string(), domain_a),
                (law_b.to_string(), domain_b),
            ],
            left_substitution,
            right_substitution,
        }
    }

    fn lgg_recursive(
        &mut self,
        left: &CanonicalExpr,
        right: &CanonicalExpr,
    ) -> CanonicalExpr {
        match (left, right) {
            (CanonicalExpr::Const(c1), CanonicalExpr::Const(c2)) if c1 == c2 => {
                CanonicalExpr::Const(c1.clone())
            }
            (CanonicalExpr::Var(v1), CanonicalExpr::Var(v2)) if v1 == v2 => {
                CanonicalExpr::Var(*v1)
            }
            (CanonicalExpr::Add(args1), CanonicalExpr::Add(args2)) if args1.len() == args2.len() => {
                let gen_args = args1
                    .iter()
                    .zip(args2.iter())
                    .map(|(a1, a2)| self.lgg_recursive(a1, a2))
                    .collect();
                CanonicalExpr::Add(gen_args)
            }
            (CanonicalExpr::Mul(args1), CanonicalExpr::Mul(args2)) if args1.len() == args2.len() => {
                let gen_args = args1
                    .iter()
                    .zip(args2.iter())
                    .map(|(a1, a2)| self.lgg_recursive(a1, a2))
                    .collect();
                CanonicalExpr::Mul(gen_args)
            }
            (CanonicalExpr::Div(num1, den1), CanonicalExpr::Div(num2, den2)) => {
                let gen_num = self.lgg_recursive(num1, num2);
                let gen_den = self.lgg_recursive(den1, den2);
                CanonicalExpr::Div(Box::new(gen_num), Box::new(gen_den))
            }
            (CanonicalExpr::Pow(base1, exp1), CanonicalExpr::Pow(base2, exp2)) if exp1 == exp2 => {
                let gen_base = self.lgg_recursive(base1, base2);
                CanonicalExpr::Pow(Box::new(gen_base), *exp1)
            }
            (CanonicalExpr::Neg(inner1), CanonicalExpr::Neg(inner2)) => {
                let gen_inner = self.lgg_recursive(inner1, inner2);
                CanonicalExpr::Neg(Box::new(gen_inner))
            }
            // في حال عدم تطابق الرأس أو المعاملات: نعمم التعبيرين إلى متغير فوقي جديد
            _ => self.generalize_pair(left, right),
        }
    }

    fn generalize_pair(
        &mut self,
        left: &CanonicalExpr,
        right: &CanonicalExpr,
    ) -> CanonicalExpr {
        let key = (left.clone(), right.clone());
        if let Some(&var_id) = self.memo.get(&key) {
            return CanonicalExpr::Var(var_id);
        }

        let new_var = VariableId(self.next_var_id);
        self.next_var_id += 1;

        self.memo.insert(key, new_var);
        self.left_subst.insert(new_var, left.clone());
        self.right_subst.insert(new_var, right.clone());

        CanonicalExpr::Var(new_var)
    }
}
