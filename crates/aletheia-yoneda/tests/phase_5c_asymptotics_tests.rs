use aletheia_algebra::{CanonicalExpr, Monomial, MonomialOrder, Polynomial, Rational, Term, VariableId};
use aletheia_lattice::DimensionVector;
use aletheia_rewriting::Cost;
use aletheia_yoneda::{
    AsymptoticLimitCertificate, DisputedPair, InonuWignerContraction, LatentBuffer, LatentShadow,
    LieAlgebra, NewtonPoint, NewtonPolygon, QuarantineRecord, SovereignPromotionPipeline,
    YonedaError,
};

#[test]
fn test_knowledge_dispute_and_uncertain_epoche() {
    let hyp_a = [1u8; 32];
    let hyp_b = [2u8; 32];
    let third_party = [3u8; 32];

    let mut dispute = DisputedPair::new(
        hyp_a,
        hyp_b,
        "تناقض في حد السرعات العالية بين الميكانيكا الكلاسيكية والنسبية",
        100,
    )
    .with_resolution_criterion("انكماش جبر بوانكاريه إلى جبر غاليليو عند c -> inf");

    // تحقق من أن كلا الطرفين محمي بحصانة تعليق الحكم المعرفي UNCERTAIN_EPOCHE
    assert!(dispute.protects_hypothesis(&hyp_a));
    assert!(dispute.protects_hypothesis(&hyp_b));
    // طرف ثالث لا علاقة له بالنزاع لا يحصل على الحصانة
    assert!(!dispute.protects_hypothesis(&third_party));
    assert!(!dispute.is_resolved);

    // حسم النزاع لصالح الفرضية الأكثر شمولاً
    dispute.resolve(
        hyp_a,
        "النسبية تفسر الحركة عموماً وتتطابق مع الكلاسيكية تقاربياً",
    );

    assert!(dispute.is_resolved);
    assert_eq!(dispute.winning_hypothesis, Some(hyp_a));
    // تسقط الحصانة فور حسم النزاع
    assert!(!dispute.protects_hypothesis(&hyp_a));
    assert!(!dispute.protects_hypothesis(&hyp_b));
}

#[test]
fn test_tropical_newton_convex_hull_zero_floats() {
    // إدخال نقاط متعددة في المستوى الاستوائي
    // نقاط تمثل الحدود: (0, 4), (1, 2), (2, 1), (4, 0), (2, 3)
    let points = vec![
        NewtonPoint::from_integers(0, 4),
        NewtonPoint::from_integers(1, 2),
        NewtonPoint::from_integers(2, 1),
        NewtonPoint::from_integers(4, 0),
        NewtonPoint::from_integers(2, 3), // نقطة داخلية في الغلاف
    ];

    let polygon = NewtonPolygon::from_points(points).expect("فشل بناء مضلع نيوتن");

    // الغلاف السفلي يحدد السلوك التقاربي
    assert!(!polygon.lower_hull.is_empty());
    assert_eq!(polygon.lower_hull.first().unwrap(), &NewtonPoint::from_integers(0, 4));
    assert_eq!(polygon.lower_hull.last().unwrap(), &NewtonPoint::from_integers(4, 0));

    // التحقق من حساب الميول في Q الصرفة
    let slopes = polygon.lower_hull_slopes();
    assert!(!slopes.is_empty());
    // الميول سالبة في هذا التدرج
    for slope in &slopes {
        assert!(slope < &Rational::zero());
    }

    // التحقق من أسس بويزو المقترحة
    let puiseux = polygon.candidate_puiseux_exponents();
    assert_eq!(puiseux.len(), slopes.len());

    // اختبار البناء من كثير حدود جبري P(x, y) = y^3 - x^2 * y + x^4
    let vx = VariableId(1);
    let vy = VariableId(2);

    let t1 = Term::new(Rational::one(), Monomial::variable(vy, 3));
    let t2 = Term::new(-Rational::one(), Monomial::from_factors(vec![(vx, 2), (vy, 1)]));
    let t3 = Term::new(Rational::one(), Monomial::variable(vx, 4));

    let poly = Polynomial::from_terms(vec![t1, t2, t3], MonomialOrder::DegRevLex);
    let poly_polygon = NewtonPolygon::from_polynomial(&poly, vx, vy).expect("فشل بناء مضلع كثير الحدود");

    assert_eq!(poly_polygon.points.len(), 3);
    assert_eq!(poly_polygon.hull_vertices.len(), 3);
}

#[test]
fn test_inonu_wigner_lie_algebra_contraction_so3_to_se2() {
    // 1. بناء جبر الدوران so(3)
    let so3 = LieAlgebra::so3();
    assert_eq!(so3.dim, 3);
    // التحقق من متطابقة ياكوبي لـ so(3)
    so3.verify_jacobi_identity().expect("so(3) يجب أن يحقق متطابقة ياكوبي");

    // 2. تطبيق انكماش إينونو-فيغنر: s = [1, 1, 0]
    // P1 = eps * J1, P2 = eps * J2, J = J3
    let scaling = vec![1, 1, 0];
    let contracted_names = vec!["P1".to_string(), "P2".to_string(), "J".to_string()];

    let se2 = InonuWignerContraction::contract(&so3, &scaling, contracted_names)
        .expect("فشل انكماش so(3) إلى se(2)");

    assert_eq!(se2.dim, 3);
    // التحقق من متطابقة ياكوبي للجبر المنكمش se(2) في Q
    se2.verify_jacobi_identity().expect("se(2) المنكمش يجب أن يحقق ياكوبي");

    // في se(2):
    // [P1, P2] يجب أن ينكمش إلى صفر تام
    assert!(se2.get_c(0, 1, 2).is_zero());
    assert!(se2.get_c(1, 0, 2).is_zero());

    // [P2, J] = P1 (أي [1, 2, 0] = 1)
    assert_eq!(se2.get_c(1, 2, 0), &Rational::one());
    // [J, P1] = P2 (أي [2, 0, 1] = 1)
    assert_eq!(se2.get_c(2, 0, 1), &Rational::one());
}

#[test]
fn test_singular_contraction_rejected() {
    let so3 = LieAlgebra::so3();
    // تدريج يؤدي إلى أس سالب: s = [0, 0, 1]
    // [J1, J2] = J3 => s_0 + s_1 - s_2 = 0 + 0 - 1 = -1 < 0 (انكماش منفرد يتباعد)
    let invalid_scaling = vec![0, 0, 1];
    let names = vec!["X0".to_string(), "X1".to_string(), "X2".to_string()];

    let result = InonuWignerContraction::contract(&so3, &invalid_scaling, names);
    assert!(matches!(result, Err(YonedaError::SingularContraction(_))));
}

#[test]
fn test_asymptotic_limit_certificate_issuance_and_integrity() {
    let hyp_id = [42u8; 32];
    let cert = AsymptoticLimitCertificate::issue(
        hyp_id,
        "epsilon",
        Rational::zero(),
        vec![Rational::new(-1, 2).unwrap()],
        vec![Rational::new(2, 1).unwrap()],
        Some(3),
        true,
        true,
        vec!["Inonu-Wigner contraction evaluated at eps=0".to_string()],
        1,
    );

    // التحقق من سلامة البصمة التشفيرية
    assert!(cert.verify_integrity());

    // العبث المتعمد بالشهادة يجب أن يبطل التوثيق
    let mut tampered = cert.clone();
    tampered.parameter_name = "tampered_param".to_string();
    assert!(!tampered.verify_integrity());
}

#[test]
fn test_sovereign_promotion_pipeline_dof_zero_quenched() {
    let mut buffer = LatentBuffer::new();

    // إنشاء فرضية مع dof = 0 (تم إطفاؤها بنجاح عبر RREF و دورات النيوترينو)
    let shadow = LatentShadow::new(
        vec!["law_10".to_string()],
        DimensionVector::default(),
        0,
        Rational::zero(),
        vec![aletheia_egraph::EClassId(1)],
    );
    let record = QuarantineRecord::new(shadow);
    let record_id = record.record_id;
    buffer.admit(record);

    assert_eq!(buffer.len(), 1);

    // محاولة الترقية للسيادة
    let ast = CanonicalExpr::Const(Rational::one());
    let dim = DimensionVector::default();
    let cost = Cost::zero();

    let candidate = SovereignPromotionPipeline::promote_record(
        &mut buffer,
        &record_id,
        ast,
        dim,
        cost,
        vec!["Fully quenched dof=0".to_string()],
        None,
        500,
    )
    .expect("يجب أن تنجح الترقية للسيادة فور تصفير درجات الحرية");

    assert_eq!(candidate.canonical_id, record_id);
    assert_eq!(candidate.sovereignty_epoch, 500);

    // التأكد من إسقاط صفة الحجر وسحب السجل ذرياً من الحجر الصحي
    assert_eq!(buffer.len(), 0);
    assert!(buffer.get(&record_id).is_none());
}

#[test]
fn test_sovereign_promotion_denied_when_dof_positive() {
    let mut buffer = LatentBuffer::new();

    // إنشاء فرضية لا زالت تحتوي على درجات حرية موجبة / كسرية: dof = 1/2
    let shadow = LatentShadow::new(
        vec!["law_20".to_string()],
        DimensionVector::default(),
        0,
        Rational::new(1, 2).unwrap(),
        vec![aletheia_egraph::EClassId(2)],
    );
    let record = QuarantineRecord::new(shadow);
    let record_id = record.record_id;
    buffer.admit(record);

    let ast = CanonicalExpr::Const(Rational::one());
    let dim = DimensionVector::default();
    let cost = Cost::zero();

    let result = SovereignPromotionPipeline::promote_record(
        &mut buffer,
        &record_id,
        ast,
        dim,
        cost,
        vec![],
        None,
        500,
    );

    assert!(matches!(result, Err(YonedaError::PromotionDenied(_))));
    // السجل يبقى محتجزاً في الحجر الصحي
    assert_eq!(buffer.len(), 1);
}
