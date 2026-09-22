use aletheia_algebra::{CanonicalExpr, Rational, VariableId};
use aletheia_lattice::*;

#[test]
fn test_zero_extension_rule() {
    let reg = DimensionRegistry::new();

    // متجه أبعاد بطول 7 (الأبعاد السبعة الأساسية)
    let length_7 = reg.length();
    assert_eq!(length_7.len(), 7);

    // متجه بطول 9 يحتوي أصفاراً إضافية في النهاية
    let mut length_9_coords = length_7.coords().to_vec();
    length_9_coords.push(Rational::zero());
    length_9_coords.push(Rational::zero());
    let length_9 = DimensionVector::from_coords(length_9_coords);
    assert_eq!(length_9.len(), 9);

    // 1. التساوي الكنسي مع التمدد الصفري
    assert_eq!(length_7, length_9);
    assert_eq!(length_9, length_7);

    // 2. إذا اختلف بعد زائد غير صفري، يفشل التساوي
    let mut diff_coords = length_7.coords().to_vec();
    diff_coords.push(Rational::one());
    let diff_vec = DimensionVector::from_coords(diff_coords);
    assert_ne!(length_7, diff_vec);

    // 3. الجمع والطرح بين متجهات ذات أطوال مختلفة
    let time_7 = reg.time();
    let sum = &time_7 + &diff_vec;
    assert_eq!(sum.len(), 8);
    assert_eq!(sum.get_coord(DimensionRegistry::LENGTH_IDX), Rational::from_i64(1));
    assert_eq!(sum.get_coord(DimensionRegistry::TIME_IDX), Rational::from_i64(1));
    assert_eq!(sum.get_coord(7), Rational::from_i64(1));
}

#[test]
fn test_dimension_registry_and_orthogonal_extension() {
    let mut reg = DimensionRegistry::new();
    assert_eq!(reg.dimension_count(), 7);

    // الأبعاد المشتقة
    let force = reg.force();
    // [M * L * T^(-2)]
    assert_eq!(force.get_coord(DimensionRegistry::MASS_IDX), Rational::from_i64(1));
    assert_eq!(force.get_coord(DimensionRegistry::LENGTH_IDX), Rational::from_i64(1));
    assert_eq!(force.get_coord(DimensionRegistry::TIME_IDX), Rational::from_i64(-2));

    // الطاقة: [M * L^2 * T^(-2)]
    let energy = reg.energy();
    assert_eq!(energy.get_coord(DimensionRegistry::LENGTH_IDX), Rational::from_i64(2));

    // التوسع المتعامد: إضافة بعد المعلومات [Bit]
    let bit_id = reg.register_orthogonal("InformationBit").unwrap();
    assert_eq!(reg.dimension_count(), 8);
    assert_eq!(bit_id.0, 7);

    let bit_vec = reg.unit_basis(bit_id).unwrap();
    assert_eq!(bit_vec.get_coord(7), Rational::from_i64(1));
    assert_eq!(bit_vec.get_coord(DimensionRegistry::LENGTH_IDX), Rational::from_i64(0));

    // رفض تكرار البعد
    assert!(reg.register_orthogonal("InformationBit").is_err());
}

#[test]
fn test_exact_rref_and_nullspace() {
    // مصفوفة كسرية 2x3:
    // [ 1,  2, -1 ]
    // [ 2,  4, -2 ]
    let mat = RationalMatrix::from_rows(vec![
        vec![Rational::from_i64(1), Rational::from_i64(2), Rational::from_i64(-1)],
        vec![Rational::from_i64(2), Rational::from_i64(4), Rational::from_i64(-2)],
    ]);

    let nullspace = mat.nullspace();
    // الرتبة = 1، عدد المتغيرات = 3 -> الفضاء الصفري له بعد = 2
    assert_eq!(nullspace.len(), 2);

    for sol in &nullspace {
        assert!(mat.verifies_nullspace_vector(sol));
    }
}

#[test]
fn test_buckingham_pi_pendulum() {
    let reg = DimensionRegistry::new();

    // مسألة البندول البسيط الكلاسيكية:
    // المتغيرات:
    // L: طول الخيط [L]
    // m: كتلة الكرة [M]
    // g: تسارع الجاذبية [L * T^(-2)]
    // t: الزمن الدوري [T]
    let vars = vec![
        PhysicalVariable::new("L", reg.length()),
        PhysicalVariable::new("m", reg.mass()),
        PhysicalVariable::new("g", reg.acceleration()),
        PhysicalVariable::new("t", reg.time()),
    ];

    let groups = BuckinghamPiEngine::analyze(&vars);
    // n = 4 متغيرات، الأبعاد الأساسية المستقلة = 3 (L, M, T)
    // p = 4 - 3 = 1 مجموعة لابُعدية وحيدة فريدة!
    assert_eq!(groups.len(), 1);

    let pi1 = &groups[0];
    assert!(pi1.verify_dimensionless(&vars));

    // الكتلة m لا تؤثر في دورة البندول (يجب أن يكون أسها صفراً)
    let m_exp = pi1.exponents.iter().find(|(s, _)| s == "m");
    assert!(m_exp.is_none() || m_exp.unwrap().1.is_zero());

    // التحقق من العلاقة الشهيرة t * sqrt(g / L) = t * g^(1/2) * L^(-1/2)
    // النسبة بين أس t وأس g وأس L
    let t_exp = pi1.exponents.iter().find(|(s, _)| s == "t").unwrap().1.clone();
    let g_exp = pi1.exponents.iter().find(|(s, _)| s == "g").unwrap().1.clone();
    let l_exp = pi1.exponents.iter().find(|(s, _)| s == "L").unwrap().1.clone();

    // t_exp / g_exp يجب أن يساوي 2، و l_exp / g_exp يجب أن يساوي -1
    let ratio_t_g = t_exp.checked_div(&g_exp).unwrap();
    let ratio_l_g = l_exp.checked_div(&g_exp).unwrap();
    assert_eq!(ratio_t_g, Rational::from_i64(2));
    assert_eq!(ratio_l_g, Rational::from_i64(-1));
}

#[test]
fn test_coupling_constants_synthesis() {
    let reg = DimensionRegistry::new();

    // 1. اشتقاق ثابت الجاذبية لنيوتن G: F ~ m1 * m2 / r^2
    // [G] = [M^(-1) * L^3 * T^(-2)]
    let newton_g = synthesize_newton_g(&reg.force(), &reg.mass(), &reg.length());
    assert_eq!(newton_g.get_coord(DimensionRegistry::MASS_IDX), Rational::from_i64(-1));
    assert_eq!(newton_g.get_coord(DimensionRegistry::LENGTH_IDX), Rational::from_i64(3));
    assert_eq!(newton_g.get_coord(DimensionRegistry::TIME_IDX), Rational::from_i64(-2));

    // 2. اشتقاق ثابت بلانك h: E ~ nu (حيث nu = T^(-1))
    // [h] = [M * L^2 * T^(-1)]
    let planck_h = synthesize_planck_h(&reg.energy(), &reg.time());
    assert_eq!(planck_h.get_coord(DimensionRegistry::MASS_IDX), Rational::from_i64(1));
    assert_eq!(planck_h.get_coord(DimensionRegistry::LENGTH_IDX), Rational::from_i64(2));
    assert_eq!(planck_h.get_coord(DimensionRegistry::TIME_IDX), Rational::from_i64(-1));

    // 3. اشتقاق ثابت كولوم ke: F ~ q^2 / r^2
    let coulomb_ke = synthesize_coulomb_ke(&reg.force(), &reg.current(), &reg.time(), &reg.length());
    assert_eq!(coulomb_ke.get_coord(DimensionRegistry::MASS_IDX), Rational::from_i64(1));
    assert_eq!(coulomb_ke.get_coord(DimensionRegistry::LENGTH_IDX), Rational::from_i64(3));
    assert_eq!(coulomb_ke.get_coord(DimensionRegistry::TIME_IDX), Rational::from_i64(-4));
    assert_eq!(coulomb_ke.get_coord(DimensionRegistry::CURRENT_IDX), Rational::from_i64(-2));
}

#[test]
fn test_semantic_guard_and_dimensional_context() {
    let reg = DimensionRegistry::new();
    let mut ctx = DimensionalContext::new();

    let x0 = VariableId(0); // مسافة r
    let x1 = VariableId(1); // زمن t
    let x2 = VariableId(2); // كتلة m

    ctx.bind(x0, reg.length());
    ctx.bind(x1, reg.time());
    ctx.bind(x2, reg.mass());

    // 1. تعبير متجانس جمعياً: (x0 + 2*x0)
    let expr_homo = CanonicalExpr::Add(vec![
        CanonicalExpr::Var(x0),
        CanonicalExpr::Mul(vec![
            CanonicalExpr::Const(Rational::from_i64(2)),
            CanonicalExpr::Var(x0),
        ]),
    ]);
    let dim_homo = SemanticGuard::infer_dimension(&expr_homo, &ctx).unwrap();
    assert_eq!(dim_homo, reg.length());

    // 2. تعبير غير متجانس: x0 + x1 (مسافة + زمن) -> يجب رفضه فورياً
    let expr_inhomo = CanonicalExpr::Add(vec![
        CanonicalExpr::Var(x0),
        CanonicalExpr::Var(x1),
    ]);
    let err_inhomo = SemanticGuard::infer_dimension(&expr_inhomo, &ctx);
    assert!(matches!(err_inhomo, Err(LatticeError::IncompatibleDimensions { .. })));

    // 3. دعم الأسس السالبة: قانون مقلوب مربع المسافة r^(-2)
    let expr_inv_sq = CanonicalExpr::Pow(Box::new(CanonicalExpr::Var(x0)), -2);
    let dim_inv_sq = SemanticGuard::infer_dimension(&expr_inv_sq, &ctx).unwrap();
    assert_eq!(dim_inv_sq.get_coord(DimensionRegistry::LENGTH_IDX), Rational::from_i64(-2));

    // 4. حارس الدوال المتسامية (Transcendental Invariant)
    // مدخل الدالة المتسامية يجب أن يكون لا بُعدياً تماماً
    assert!(SemanticGuard::check_transcendental_argument(&DimensionVector::dimensionless()).is_ok());
    assert!(SemanticGuard::check_transcendental_argument(&reg.length()).is_err());
}

#[test]
fn test_lattice_data_merge_with_rollback() {
    let reg = DimensionRegistry::new();

    let data_len1 = LatticeData::physical(reg.length());
    let data_len2 = LatticeData::physical(reg.length());
    let data_time = LatticeData::physical(reg.time());

    // 1. دمج فئات متوافقة في الأبعاد ينجح
    let merged_ok = data_len1.merge(&data_len2);
    assert!(merged_ok.is_ok());

    // 2. دمج فئات متناقضة الأبعاد (مسافة مع زمن) يُرفض فورياً ويُطلق ContradictoryMerge
    let merge_err = data_len1.merge(&data_time);
    assert!(matches!(merge_err, Err(LatticeError::ContradictoryMerge(_))));
}
