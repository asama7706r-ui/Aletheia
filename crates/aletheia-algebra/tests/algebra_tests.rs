use aletheia_algebra::derivation::*;
use aletheia_algebra::error::FormalContradictionError;
use aletheia_algebra::grobner::*;
use aletheia_algebra::koszul::*;
use aletheia_algebra::monomial::*;
use aletheia_algebra::polynomial::*;
use aletheia_algebra::rational::Rational;
use std::cmp::Ordering;

#[test]
fn test_rational_field_axioms_and_zero_drift() {
    // 1. Zero Float Drift: 1/3 + 1/6 == 1/2 بالضبط
    let r1 = Rational::new(1, 3).unwrap();
    let r2 = Rational::new(1, 6).unwrap();
    let sum = &r1 + &r2;
    let expected = Rational::new(1, 2).unwrap();
    assert_eq!(sum, expected);

    // 2. المحايد الجمعي والضربي
    assert_eq!(&r1 + &Rational::zero(), r1);
    assert_eq!(&r1 * &Rational::one(), r1);

    // 3. المعكوس الجمعي والضربي
    assert_eq!(&r1 + &(-&r1), Rational::zero());
    assert_eq!((&r1 * &r1.inv().unwrap()), Rational::one());

    // 4. حظر القسمة على الصفر برفع FormalContradictionError
    let zero = Rational::zero();
    assert_eq!(r1.checked_div(&zero), Err(FormalContradictionError::DivisionByZero));
    assert_eq!(zero.inv(), Err(FormalContradictionError::DivisionByZero));

    // 5. الأعداد الهائلة (BigInt) دون طفحان
    let huge1 = Rational::from_i64(1_000_000_000_000_000_000);
    let huge2 = Rational::from_i64(2_000_000_000_000_000_000);
    let huge_prod = &huge1 * &huge2;
    assert_eq!(huge_prod.to_string(), "2000000000000000000000000000000000000");
}

#[test]
fn test_monomial_arithmetic_and_well_ordering() {
    let x0 = VariableId(0);
    let x1 = VariableId(1);
    let x2 = VariableId(2);

    // بناء مونوميات: m1 = x0^2 * x1, m2 = x1^3 * x2
    let m1 = Monomial::from_factors(vec![(x0, 2), (x1, 1)]);
    let m2 = Monomial::from_factors(vec![(x1, 3), (x2, 1)]);

    assert_eq!(m1.total_degree(), 3);
    assert_eq!(m2.total_degree(), 4);

    // الضرب
    let prod = m1.mul(&m2);
    assert_eq!(prod.total_degree(), 7);
    assert_eq!(prod.exponent_of(x0), 2);
    assert_eq!(prod.exponent_of(x1), 4);
    assert_eq!(prod.exponent_of(x2), 1);

    // GCD و LCM
    let gcd = m1.gcd(&m2);
    assert_eq!(gcd.total_degree(), 1);
    assert_eq!(gcd.exponent_of(x1), 1);

    let lcm = m1.lcm(&m2);
    assert_eq!(lcm.total_degree(), 6);
    assert_eq!(lcm.exponent_of(x0), 2);
    assert_eq!(lcm.exponent_of(x1), 3);
    assert_eq!(lcm.exponent_of(x2), 1);

    // قابلية القسمة
    assert!(prod.is_divisible_by(&m1));
    assert!(prod.is_divisible_by(&m2));
    assert_eq!(prod.checked_div(&m1).unwrap(), m2);

    // بديهية الترتيب المونومي DegRevLex (Cox, Little, O'Shea)
    // x0 > x1 > x2
    let mono_x0 = Monomial::variable(x0, 1);
    let mono_x1 = Monomial::variable(x1, 1);
    let mono_x2 = Monomial::variable(x2, 1);

    assert_eq!(mono_x0.cmp_with_order(&mono_x1, MonomialOrder::DegRevLex), Ordering::Greater);
    assert_eq!(mono_x1.cmp_with_order(&mono_x2, MonomialOrder::DegRevLex), Ordering::Greater);

    // مقارنة شهيرة في DegRevLex: x0^2 * x1 * x2^2 مقابل x0 * x1^3 * x2 (الدرجة = 5 متساوية)
    // في DegRevLex: x0 * x1^3 * x2 أكبر لأن أس x2 فيه أقل (1 < 2)!
    let test_a = Monomial::from_factors(vec![(x0, 2), (x1, 1), (x2, 2)]);
    let test_b = Monomial::from_factors(vec![(x0, 1), (x1, 3), (x2, 1)]);
    assert_eq!(test_a.cmp_with_order(&test_b, MonomialOrder::DegRevLex), Ordering::Less);

    // اختبار الترتيب المعجمي Lex: في Lex، الدرجة لا تهم إذا كان المتغير الأول أكبر
    // x0 > x1^10 في Lex
    let x0_pow1 = Monomial::variable(x0, 1);
    let x1_pow10 = Monomial::variable(x1, 10);
    assert_eq!(x0_pow1.cmp_with_order(&x1_pow10, MonomialOrder::Lex), Ordering::Greater);

    // بديهية Well-Ordering: x^alpha >= 1 لأي مونوم
    assert_ne!(m1.cmp_with_order(&Monomial::one(), MonomialOrder::DegRevLex), Ordering::Less);

    // شرط التوافق: a > b => a * c > b * c
    let a = Monomial::variable(x0, 2);
    let b = Monomial::variable(x1, 2);
    let c = Monomial::variable(x2, 1);
    assert_eq!(a.cmp_with_order(&b, MonomialOrder::DegRevLex), Ordering::Greater);
    assert_eq!(a.mul(&c).cmp_with_order(&b.mul(&c), MonomialOrder::DegRevLex), Ordering::Greater);
}

#[test]
fn test_polynomial_arithmetic_and_multivariate_division() {
    let x0 = VariableId(0);
    let x1 = VariableId(1);

    // f = x0^2 * x1 + x0 * x1^2 + x1^2
    // f1 = x0 * x1 - 1
    // f2 = x1^2 - 1
    let poly_f = Polynomial::from_terms(
        vec![
            Term::new(Rational::one(), Monomial::from_factors(vec![(x0, 2), (x1, 1)])),
            Term::new(Rational::one(), Monomial::from_factors(vec![(x0, 1), (x1, 2)])),
            Term::new(Rational::one(), Monomial::variable(x1, 2)),
        ],
        MonomialOrder::DegRevLex,
    );

    let poly_f1 = Polynomial::from_terms(
        vec![
            Term::new(Rational::one(), Monomial::from_factors(vec![(x0, 1), (x1, 1)])),
            Term::new(-Rational::one(), Monomial::one()),
        ],
        MonomialOrder::DegRevLex,
    );

    let poly_f2 = Polynomial::from_terms(
        vec![
            Term::new(Rational::one(), Monomial::variable(x1, 2)),
            Term::new(-Rational::one(), Monomial::one()),
        ],
        MonomialOrder::DegRevLex,
    );

    // خوارزمية القسمة متعددة المتغيرات
    let (quots, rem) = poly_f.divide_multivariate(&[poly_f1.clone(), poly_f2.clone()]);

    // التحقق من مبرهنة القسمة: f == q1*f1 + q2*f2 + r
    let reconstructed = quots[0].mul_poly(&poly_f1)
        .add_poly(&quots[1].mul_poly(&poly_f2))
        .add_poly(&rem);

    assert_eq!(poly_f, reconstructed);
}

#[test]
fn test_egraph_canonical_expr_interop() {
    let x0 = VariableId(0);
    let x1 = VariableId(1);

    // كثير حدود 3*x0^2 - 2*x1 + 5
    let p = Polynomial::from_terms(
        vec![
            Term::new(Rational::from_i64(3), Monomial::variable(x0, 2)),
            Term::new(Rational::from_i64(-2), Monomial::variable(x1, 1)),
            Term::new(Rational::from_i64(5), Monomial::one()),
        ],
        MonomialOrder::DegRevLex,
    );

    // 1. التصدير إلى CanonicalExpr
    let expr = p.to_canonical_expr();

    // 2. إعادة البناء من CanonicalExpr
    let imported = Polynomial::from_canonical_expr(&expr, MonomialOrder::DegRevLex).unwrap();

    // يجب أن يتطابق كثير الحدود المعاد بناؤه 100% مع الأصل
    assert_eq!(p, imported);
}

#[test]
fn test_grobner_basis_buchberger_and_reduced() {
    let x0 = VariableId(0);
    let x1 = VariableId(1);

    // مثالي في Q[x0, x1]:
    // f1 = x0^2 - x1
    // f2 = x0^3 - x0
    let f1 = Polynomial::from_terms(
        vec![
            Term::new(Rational::one(), Monomial::variable(x0, 2)),
            Term::new(-Rational::one(), Monomial::variable(x1, 1)),
        ],
        MonomialOrder::DegRevLex,
    );

    let f2 = Polynomial::from_terms(
        vec![
            Term::new(Rational::one(), Monomial::variable(x0, 3)),
            Term::new(-Rational::one(), Monomial::variable(x0, 1)),
        ],
        MonomialOrder::DegRevLex,
    );

    let config = GrobnerConfig {
        max_degree: Some(10),
        step_budget: Some(1000),
    };

    // حساب أساس غروبنر المختزل
    let reduced_basis = reduced_grobner_basis(&[f1.clone(), f2.clone()], &config).unwrap();
    assert!(!reduced_basis.is_empty());

    // كل عنصر أصلي يجب أن يختزل إلى صفر بالنسبة لأساس غروبنر
    assert_eq!(f1.reduce_by(&reduced_basis), Polynomial::zero());
    assert_eq!(f2.reduce_by(&reduced_basis), Polynomial::zero());

    // اختبار سقف ميزانية الحساب
    let tight_config = GrobnerConfig {
        max_degree: None,
        step_budget: Some(0),
    };
    let err = buchberger(&[f1, f2], &tight_config);
    assert_eq!(err, Err(FormalContradictionError::StepBudgetExceeded { budget: 0 }));
}

#[test]
fn test_koszul_parity_axiom() {
    // درجة 0 (بوزوني) ودرجة 0 -> (-1)^(0*0) = +1
    assert_eq!(koszul_parity_sign(0, 0), 1);
    // درجة 0 ودرجة 1 -> (-1)^(0*1) = +1
    assert_eq!(koszul_parity_sign(0, 1), 1);
    // درجة 1 (فرميوني) ودرجة 1 (فرميوني) -> (-1)^(1*1) = -1
    assert_eq!(koszul_parity_sign(1, 1), -1);

    let elem_a = GradedElement::new("A", 1);
    let elem_b = GradedElement::new("B", 1);

    assert!(elem_a.is_fermionic());
    assert_eq!(elem_a.exchange_sign(&elem_b), -1);

    // التحقق يمر بنجاح عند مطابقة الإشارة
    assert!(elem_a.verify_commutation_sign(&elem_b, -1).is_ok());
    // ويفشل ويرفع ParityViolation عند التناقض
    assert!(elem_a.verify_commutation_sign(&elem_b, 1).is_err());

    // تقليص أينشتاين
    let upper = ContravariantIndex(3);
    let lower_match = CovariantIndex(3);
    let lower_diff = CovariantIndex(4);
    assert!(can_contract_einstein(upper, lower_match));
    assert!(!can_contract_einstein(upper, lower_diff));
}

#[test]
fn test_symbolic_leibniz_derivation() {
    let x0 = VariableId(0);
    let x1 = VariableId(1);

    // p = 4*x0^3 * x1^2 + 7*x0 - 5
    let p = Polynomial::from_terms(
        vec![
            Term::new(Rational::from_i64(4), Monomial::from_factors(vec![(x0, 3), (x1, 2)])),
            Term::new(Rational::from_i64(7), Monomial::variable(x0, 1)),
            Term::new(Rational::from_i64(-5), Monomial::one()),
        ],
        MonomialOrder::DegRevLex,
    );

    // dp/dx0 = 12*x0^2 * x1^2 + 7
    let dp_dx0 = diff_var(&p, x0);
    let expected_dp_dx0 = Polynomial::from_terms(
        vec![
            Term::new(Rational::from_i64(12), Monomial::from_factors(vec![(x0, 2), (x1, 2)])),
            Term::new(Rational::from_i64(7), Monomial::one()),
        ],
        MonomialOrder::DegRevLex,
    );
    assert_eq!(dp_dx0, expected_dp_dx0);

    // dp/dx1 = 8*x0^3 * x1
    let dp_dx1 = diff_var(&p, x1);
    let expected_dp_dx1 = Polynomial::from_terms(
        vec![
            Term::new(Rational::from_i64(8), Monomial::from_factors(vec![(x0, 3), (x1, 1)])),
        ],
        MonomialOrder::DegRevLex,
    );
    assert_eq!(dp_dx1, expected_dp_dx1);

    // اختبار قانون لايبنتز للجداء: d(f * g)/dx == f * dg/dx + g * df/dx
    let f = Polynomial::from_terms(
        vec![
            Term::new(Rational::from_i64(2), Monomial::variable(x0, 2)),
            Term::new(Rational::from_i64(3), Monomial::variable(x1, 1)),
        ],
        MonomialOrder::DegRevLex,
    );

    let g = Polynomial::from_terms(
        vec![
            Term::new(Rational::from_i64(5), Monomial::variable(x0, 1)),
            Term::new(Rational::from_i64(-1), Monomial::one()),
        ],
        MonomialOrder::DegRevLex,
    );

    assert!(verify_leibniz_rule(&f, &g, x0));
    assert!(verify_leibniz_rule(&f, &g, x1));
}

#[test]
fn test_macaulay_ceiling_and_step_budget_limits() {
    let x0 = VariableId(0);
    let x1 = VariableId(1);

    // f = x0^4 - x1^4
    // g = x0^3 * x1 - x0
    let f = Polynomial::from_terms(
        vec![
            Term::new(Rational::one(), Monomial::variable(x0, 4)),
            Term::new(-Rational::one(), Monomial::variable(x1, 4)),
        ],
        MonomialOrder::DegRevLex,
    );

    let g = Polynomial::from_terms(
        vec![
            Term::new(Rational::one(), Monomial::from_factors(vec![(x0, 3), (x1, 1)])),
            Term::new(-Rational::one(), Monomial::variable(x0, 1)),
        ],
        MonomialOrder::DegRevLex,
    );

    // سقف ماكولاي منخفض (درجة 3): يجب أن يتجاهل الأزواج ذات الدرجة الأعلى دون تعطل
    let config_low_degree = GrobnerConfig {
        max_degree: Some(3),
        step_budget: Some(100),
    };

    let basis = buchberger(&[f.clone(), g.clone()], &config_low_degree).unwrap();
    // لم يتم إضافة أي S-poly لأن درجة الـ LCM = 5 تتجاوز سقف 3
    assert_eq!(basis.len(), 2);

    // مع سقف ماكولاي كافٍ (درجة 10) وميزانية خطوات كافية
    let config_normal = GrobnerConfig {
        max_degree: Some(10),
        step_budget: Some(100),
    };
    let full_basis = buchberger(&[f, g], &config_normal).unwrap();
    assert!(full_basis.len() > 2);
}

#[test]
fn test_complex_canonical_expr_nested_roundtrip() {
    let x0 = VariableId(0);
    let x1 = VariableId(1);
    let x2 = VariableId(2);

    // بناء شجرة تعبيرات معقدة: -( (x0 + 2*x1)^2 * (x2 - 1/3) )
    let expr = CanonicalExpr::Neg(Box::new(CanonicalExpr::Mul(vec![
        CanonicalExpr::Pow(
            Box::new(CanonicalExpr::Add(vec![
                CanonicalExpr::Var(x0),
                CanonicalExpr::Mul(vec![
                    CanonicalExpr::Const(Rational::from_i64(2)),
                    CanonicalExpr::Var(x1),
                ]),
            ])),
            2,
        ),
        CanonicalExpr::Add(vec![
            CanonicalExpr::Var(x2),
            CanonicalExpr::Const(Rational::new(-1, 3).unwrap()),
        ]),
    ])));

    // تحويل الشجرة إلى Polynomial
    let poly = Polynomial::from_canonical_expr(&expr, MonomialOrder::DegRevLex).unwrap();
    assert!(!poly.is_zero());

    // تصديرها مجدداً إلى CanonicalExpr ثم استيرادها
    let exported = poly.to_canonical_expr();
    let re_imported = Polynomial::from_canonical_expr(&exported, MonomialOrder::DegRevLex).unwrap();

    // التحقق من التطابق التام
    assert_eq!(poly, re_imported);
}
