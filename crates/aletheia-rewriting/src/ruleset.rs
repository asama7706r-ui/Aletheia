use crate::pattern::Pattern;
use crate::rule::{RewriteRule, RuleGuard, RuleKind};
use aletheia_algebra::Rational;

/// حزمة القواعد الجبرية والفيزيائية المعيارية (Standard Algebraic Ruleset)
pub fn standard_algebraic_ruleset() -> Vec<RewriteRule> {
    let zero = Pattern::constant(Rational::zero());
    let one = Pattern::constant(Rational::one());

    let x = Pattern::wildcard(0);
    let y = Pattern::wildcard(1);
    let z = Pattern::wildcard(2);

    vec![
        // 1. x + 0 -> x
        RewriteRule::new(
            "add_zero",
            RuleKind::CanonicalReduction,
            Pattern::add(vec![x.clone(), zero.clone()]),
            x.clone(),
        ),
        // 2. x * 1 -> x
        RewriteRule::new(
            "mul_one",
            RuleKind::CanonicalReduction,
            Pattern::mul(vec![x.clone(), one.clone()]),
            x.clone(),
        ),
        // 3. x * 0 -> 0
        RewriteRule::new(
            "mul_zero",
            RuleKind::CanonicalReduction,
            Pattern::mul(vec![x.clone(), zero.clone()]),
            zero.clone(),
        ),
        // 4. x + (-x) -> 0
        RewriteRule::new(
            "sub_self",
            RuleKind::CanonicalReduction,
            Pattern::add(vec![x.clone(), Pattern::neg(x.clone())]),
            zero.clone(),
        ),
        // 5. -(-x) -> x
        RewriteRule::new(
            "neg_neg",
            RuleKind::CanonicalReduction,
            Pattern::neg(Pattern::neg(x.clone())),
            x.clone(),
        ),
        // 6. x / 1 -> x
        RewriteRule::new(
            "div_one",
            RuleKind::CanonicalReduction,
            Pattern::div(x.clone(), one.clone()),
            x.clone(),
        ),
        // 7. x / x -> 1 (بشرط x != 0)
        RewriteRule::new(
            "div_self",
            RuleKind::CanonicalReduction,
            Pattern::div(x.clone(), x.clone()),
            one.clone(),
        )
        .with_guard(RuleGuard::NonZero(0)),
        // 8. (x * y) / x -> y (بشرط x != 0)
        RewriteRule::new(
            "div_cancel_mul",
            RuleKind::CanonicalReduction,
            Pattern::div(Pattern::mul(vec![x.clone(), y.clone()]), x.clone()),
            y.clone(),
        )
        .with_guard(RuleGuard::NonZero(0)),
        // 9. x^1 -> x
        RewriteRule::new(
            "pow_one",
            RuleKind::CanonicalReduction,
            Pattern::pow(x.clone(), 1),
            x.clone(),
        ),
        // 10. x^0 -> 1 (بشرط x != 0)
        RewriteRule::new(
            "pow_zero",
            RuleKind::CanonicalReduction,
            Pattern::pow(x.clone(), 0),
            one.clone(),
        )
        .with_guard(RuleGuard::NonZero(0)),
        // 11. توزيع الضرب على الجمع: x * (y + z) -> (x * y) + (x * z) (توسع موجه)
        RewriteRule::new(
            "distribute_mul_add",
            RuleKind::DemandExpansion,
            Pattern::mul(vec![x.clone(), Pattern::add(vec![y.clone(), z.clone()])]),
            Pattern::add(vec![
                Pattern::mul(vec![x.clone(), y.clone()]),
                Pattern::mul(vec![x.clone(), z.clone()]),
            ]),
        ),
        // 12. تجميع الضرب: (x * y) + (x * z) -> x * (y + z) (توسع موجه)
        RewriteRule::new(
            "factor_mul_add",
            RuleKind::DemandExpansion,
            Pattern::add(vec![
                Pattern::mul(vec![x.clone(), y.clone()]),
                Pattern::mul(vec![x.clone(), z.clone()]),
            ]),
            Pattern::mul(vec![x.clone(), Pattern::add(vec![y.clone(), z.clone()])]),
        ),
    ]
}
