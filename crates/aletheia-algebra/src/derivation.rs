use crate::monomial::{Monomial, VariableId};
use crate::polynomial::{Polynomial, Term};
use crate::rational::Rational;
use smallvec::SmallVec;

/// التفاضل الرمزي لمونوم بالنسبة لمتغير x_i
/// d/dx_i (x_1^a1 ... x_i^ai ... x_n^an) = ai * (x_1^a1 ... x_i^(ai - 1) ... x_n^an)
pub fn diff_monomial(mono: &Monomial, var: VariableId) -> Option<Term> {
    let power = mono.exponent_of(var);
    if power == 0 {
        return None;
    }

    let coeff = Rational::from_i64(power as i64);

    let mut new_factors: SmallVec<[(VariableId, u32); 4]> = SmallVec::new();
    for &(v, p) in mono.factors() {
        if v == var {
            if p > 1 {
                new_factors.push((v, p - 1));
            }
        } else {
            new_factors.push((v, p));
        }
    }

    let new_mono = Monomial::from_factors(new_factors);
    Some(Term::new(coeff, new_mono))
}

/// التفاضل الجبري الرمزي لكثير حدود بالنسبة لمتغير x_i
/// يحقق بديهية الخطية المطلقة وقانون لايبنتز للجداء (Leibniz Product Rule)
pub fn diff_var(poly: &Polynomial, var: VariableId) -> Polynomial {
    if poly.is_zero() || poly.is_constant() {
        return Polynomial::zero_with_order(poly.order());
    }

    let mut new_terms = Vec::with_capacity(poly.terms().len());

    for term in poly.terms() {
        if let Some(d_term) = diff_monomial(&term.monomial, var) {
            let combined_coeff = &term.coeff * &d_term.coeff;
            new_terms.push(Term::new(combined_coeff, d_term.monomial));
        }
    }

    Polynomial::from_terms(new_terms, poly.order())
}

/// التفاضل المتعدد المتتابع d^k / (dx_i1 ... dx_ik)
pub fn diff_multi(poly: &Polynomial, vars: &[VariableId]) -> Polynomial {
    let mut current = poly.clone();
    for &var in vars {
        current = diff_var(&current, var);
        if current.is_zero() {
            break;
        }
    }
    current
}

/// تحقق برمجي من انطباق قانون لايبنتز للجداء:
/// diff(f * g, x) == f * diff(g, x) + g * diff(f, x)
pub fn verify_leibniz_rule(f: &Polynomial, g: &Polynomial, var: VariableId) -> bool {
    let fg = f.mul_poly(g);
    let lhs = diff_var(&fg, var);

    let df = diff_var(f, var);
    let dg = diff_var(g, var);
    let rhs = f.mul_poly(&dg).add_poly(&g.mul_poly(&df));

    lhs == rhs
}
