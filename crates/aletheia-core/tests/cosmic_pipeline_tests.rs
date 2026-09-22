use aletheia_core::{
    AletheiaRuntime, CanonicalExpr, Cost, DimensionVector, DomainTag, HypothesisInput,
    HypothesisOutcome, ParetoLawCandidate, Rational, ResolutionOutcome, VariableId,
};
use std::fs;
use std::path::PathBuf;

fn get_test_scratch_dir() -> PathBuf {
    let dir = std::env::temp_dir().join("aletheia_cosmic_tests");
    let _ = fs::create_dir_all(&dir);
    dir
}

#[test]
fn test_cosmic_pipeline_end_to_end_full_lifecycle() {
    let test_dir = get_test_scratch_dir();
    let dna_path = test_dir.join("cosmic_kernel.dna");
    let _ = fs::remove_file(&dna_path);

    // 1. الإقلاع المادي المباشر فوق ملف حقيقي على القرص
    let mut runtime = AletheiaRuntime::boot_or_create(Some(&dna_path), 3)
        .expect("Booting AletheiaRuntime on physical file must succeed");

    let initial_status = runtime.status();
    println!("Initial new file creation + boot latency: {} micros", initial_status.boot_latency_micros);
    assert_eq!(initial_status.dimension_rank, 3);

    // 2. زرع شبكة جسور الاقتران الفيزيائي عبر المجالات
    // جسر 1: الميكانيكا (1) -> الكهرومغناطيسية (2) بثابت اقتران 2/1 وتكلفة 5/1
    let b1 = runtime
        .materialize_bridge(1, 2, Rational::new(2, 1).unwrap(), Rational::new(5, 1).unwrap())
        .expect("Bridge 1->2 must materialize");
    assert_eq!(b1, 0);

    // جسر 2: الكهرومغناطيسية (2) -> ميكانيكا الكم (5) بثابت اقتران 3/1 وتكلفة 5/1
    let b2 = runtime
        .materialize_bridge(2, 5, Rational::new(3, 1).unwrap(), Rational::new(5, 1).unwrap())
        .expect("Bridge 2->5 must materialize");
    assert_eq!(b2, 1);

    // التحقق من استعلام المسار المباشر 1 -> 5
    let (path, k_cum) = runtime
        .query_route(1, 5)
        .expect("Direct multi-hop route 1->5 must exist in O(1)");
    assert_eq!(path, &[1, 2, 5]);
    assert_eq!(k_cum, Rational::new(6, 1).unwrap());

    // التحقق من استخراج برهان أوكام الأصغري
    let proof = runtime
        .prove_minimal_path(1, 5)
        .expect("Occam proof DAG must be constructed");
    assert_eq!(proof.steps.len(), 2);
    assert_eq!(proof.cumulative_coupling, Rational::new(6, 1).unwrap());
    assert_eq!(proof.total_cost, Rational::new(10, 1).unwrap());

    // 3. تقديم فرضية سيادية صالحة واجتياز أقفال الحقيقة
    let var_f = CanonicalExpr::Var(VariableId(1));
    let var_m = CanonicalExpr::Var(VariableId(2));
    let var_a = CanonicalExpr::Var(VariableId(3));
    let newton_expr = CanonicalExpr::Div(
        Box::new(var_f),
        Box::new(CanonicalExpr::Mul(vec![var_m, var_a])),
    );

    let dim_scalar = DimensionVector::dimensionless();
    let hypothesis = HypothesisInput::new(
        "newton_dimensionless_ratio",
        newton_expr,
        DomainTag::ClassicalMechanics,
        dim_scalar,
    ).with_cost(Cost {
        size: 3,
        degree: 1,
        bit_complexity: 6,
        transcendental: 0,
    });

    let outcome = runtime
        .submit_hypothesis(hypothesis)
        .expect("Hypothesis evaluation must complete without fatal errors");

    match outcome {
        HypothesisOutcome::SovereignAnchored { receipt, class_id } => {
            assert_eq!(receipt.domain, DomainTag::ClassicalMechanics);
            assert_eq!(class_id, 2); // الفئات المخصصة للجسرين
            assert!(receipt.verify_integrity());
        }
        other => panic!("Expected SovereignAnchored, got {:?}", other),
    }

    // 4. اختبار التوحيد العكسي (Plotkin's LGG)
    let r_sq = Box::new(CanonicalExpr::Pow(Box::new(CanonicalExpr::Var(VariableId(99))), 2));
    let grav = CanonicalExpr::Div(
        Box::new(CanonicalExpr::Mul(vec![CanonicalExpr::Var(VariableId(10)), CanonicalExpr::Var(VariableId(11))])),
        r_sq.clone(),
    );
    let coul = CanonicalExpr::Div(
        Box::new(CanonicalExpr::Mul(vec![CanonicalExpr::Var(VariableId(20)), CanonicalExpr::Var(VariableId(21))])),
        r_sq,
    );

    let meta = runtime.synthesize_meta_theorem(
        "cosmic_inverse_square",
        "grav",
        1,
        &grav,
        "coul",
        2,
        &coul,
    );
    assert_eq!(meta.meta_id, "cosmic_inverse_square");
    assert_eq!(meta.source_laws.len(), 2);

    // 5. غربال باريتو
    let candidates = vec![
        ParetoLawCandidate::new(
            "simple_candidate",
            CanonicalExpr::Const(Rational::one()),
            Cost { size: 1, degree: 1, bit_complexity: 1, transcendental: 0 },
            Rational::zero(),
            1,
            1,
        ),
        ParetoLawCandidate::new(
            "complex_dominated_candidate",
            CanonicalExpr::Const(Rational::one()),
            Cost { size: 5, degree: 2, bit_complexity: 10, transcendental: 0 },
            Rational::new(2, 1).unwrap(),
            1,
            1,
        ),
    ];
    let ranked = runtime.sieve_pareto(&candidates, Rational::new(1, 2).unwrap(), Rational::new(1, 2).unwrap());
    assert_eq!(ranked.len(), 1);
    assert_eq!(ranked[0].0.candidate_id, "simple_candidate");

    // 6. التطهير المادي والتبديل الذري الثلاثي
    let compacted_runtime = runtime
        .compact_and_cleanse()
        .expect("Compact and cleanse must execute successfully");

    let compacted_status = compacted_runtime.status();
    assert!(compacted_status.is_compacted);
    assert_eq!(compacted_status.total_enodes, 2); // العقدتان الخاصتان بالجسرين
    assert_eq!(compacted_status.total_classes, 2);

    // 7. الاختبار الحاسم: إعادة الإقلاع البارد الكامل من الملف على القرص
    drop(compacted_runtime);

    let rebooted = AletheiaRuntime::boot_or_create(Some(&dna_path), 3)
        .expect("Cold reboot from persisted DNA file must succeed");

    let reboot_status = rebooted.status();
    println!("Cold reboot latency: {} micros", reboot_status.boot_latency_micros);
    assert!(reboot_status.boot_latency_micros < 3000, "Cold reboot must be under 3ms, got {} us", reboot_status.boot_latency_micros);
    assert!(reboot_status.is_compacted);
    assert_eq!(reboot_status.total_enodes, 2);
    assert_eq!(reboot_status.total_classes, 2);

    // التحقق من استعادة الجسور والمصفوفة تلقائياً بنسبة 100%
    let (reboot_path, reboot_k) = rebooted
        .query_route(1, 5)
        .expect("Bridges must be faithfully restored from DNA on cold reboot!");
    assert_eq!(reboot_path, &[1, 2, 5]);
    assert_eq!(reboot_k, Rational::new(6, 1).unwrap());

    let _ = fs::remove_file(&dna_path);
}

#[test]
fn test_sovereign_meta_theorem_and_saturation_rewriting() {
    let mut runtime = AletheiaRuntime::boot_or_create(None, 3)
        .expect("Booting in-memory runtime must succeed");

    // 1. زرع جسر اقتران بين الميكانيكا (1) والكهرومغناطيسية (2) بثابت 4/1 وتكلفة 2/1
    runtime
        .materialize_bridge(1, 2, Rational::new(4, 1).unwrap(), Rational::new(2, 1).unwrap())
        .expect("Bridge materialization must succeed");

    // 2. فرضية قابلة للتبسيط الجبري (x * 1 -> x) عبر الـ E-Graph والتشبع
    let var_x = CanonicalExpr::Var(VariableId(101));
    let reducible_expr = CanonicalExpr::Mul(vec![var_x.clone(), CanonicalExpr::Const(Rational::one())]);
    let dim_x = DimensionVector::from_integers(&[1, 0, 0]);

    let hyp_a = HypothesisInput::new(
        "law_mechanics_reducible",
        reducible_expr,
        DomainTag::ClassicalMechanics,
        dim_x.clone(),
    );

    let outcome_a = runtime
        .submit_hypothesis(hyp_a)
        .expect("Submission must succeed");

    let receipt_a = match outcome_a {
        HypothesisOutcome::SovereignAnchored { receipt, .. } => {
            assert_eq!(receipt.ast, var_x);
            assert_eq!(receipt.lock_receipts.len(), 4);
            assert!(receipt.verify_integrity());
            *receipt
        }
        other => panic!("Expected SovereignAnchored for law A, got {:?}", other),
    };

    // 3. فرضية ثانية في المجال الكهرومغناطيسي
    let var_y = CanonicalExpr::Var(VariableId(202));
    let dim_y = DimensionVector::from_integers(&[1, 2, -1]);

    let hyp_b = HypothesisInput::new(
        "law_electromagnetism_b",
        var_y.clone(),
        DomainTag::Electromagnetism,
        dim_y.clone(),
    );

    let outcome_b = runtime
        .submit_hypothesis(hyp_b)
        .expect("Submission must succeed");

    let receipt_b = match outcome_b {
        HypothesisOutcome::SovereignAnchored { receipt, .. } => *receipt,
        other => panic!("Expected SovereignAnchored for law B, got {:?}", other),
    };

    // 4. استقراء النظرية الفوقية السيادية المقترنة بالأبعاد والجسور
    let meta = runtime.synthesize_sovereign_meta_theorem(
        "meta_mech_em",
        &receipt_a,
        &receipt_b,
    );

    assert_eq!(meta.meta_id, "meta_mech_em");
    assert_eq!(meta.source_laws.len(), 2);
    let expected_diff = &dim_y - &dim_x;
    assert_eq!(meta.dimensional_ratio, expected_diff);
    assert_eq!(meta.bridge_constant, Some(Rational::new(4, 1).unwrap()));
}

#[test]
fn test_domain_descriptor_and_non_trivial_coupling_dimension() {
    let mut runtime = AletheiaRuntime::boot_or_create(None, 7)
        .expect("Booting in-memory runtime must succeed");

    // 1. التحقق من عقد التوصيف الدستوري للمجالات
    let mech_desc = DomainTag::ClassicalMechanics.descriptor();
    assert_eq!(mech_desc.domain_id, 1);
    assert_eq!(mech_desc.invariance_group, "Galilean_SE3");
    assert_eq!(mech_desc.basis_dimension_indices, vec![0, 1, 2]); // [L, M, T]

    let em_desc = DomainTag::Electromagnetism.descriptor();
    assert_eq!(em_desc.domain_id, 2);
    assert_eq!(em_desc.invariance_group, "Gauge_U1_Lorentz");
    assert_eq!(em_desc.basis_dimension_indices, vec![0, 1, 2, 3]); // [L, M, T, I]

    // 2. زرع جسر تلقائي بين الميكانيكا والكهرومغناطيسية
    runtime
        .materialize_bridge(1, 2, Rational::new(2, 1).unwrap(), Rational::new(1, 1).unwrap())
        .expect("Bridge materialization must succeed");

    // 3. التحقق من أن الجسر تم تسجيله بأبعاد حقيقية تمثل فجوة التيار [I^1]
    let bridge_in_registry = runtime
        .sovereignty_engine
        .bridge_registry
        .bridges()
        .iter()
        .find(|b| b.source == DomainTag::ClassicalMechanics && b.target == DomainTag::Electromagnetism)
        .expect("Bridge must be registered in bridge_registry");

    assert!(!bridge_in_registry.coupling_dimension.is_dimensionless(), "Bridge coupling dimension must not be empty/dimensionless!");
    // التيار الكهربائي هو الفهرس 3
    assert_eq!(bridge_in_registry.coupling_dimension.get_coord(3), Rational::one());

    // 4. زرع جسر بمتجه أبعاد مخصص (ثابت كولوم ke: [M L^3 T^-4 I^-2])
    let coulomb_dim = DimensionVector::from_integers(&[3, 1, -4, -2]); // L^3, M^1, T^-4, I^-2
    runtime
        .materialize_bridge_with_dimension(
            1,
            2,
            coulomb_dim,
            Rational::new(89875517923, 10).unwrap(),
            Rational::one(),
        )
        .expect("Custom dimension bridge must succeed");
}

#[test]
fn test_incomplete_law_resolution_and_quarantine() {
    let mut runtime = AletheiaRuntime::boot_or_create(None, 7)
        .expect("In-memory kernel boot must succeed");

    // 1. اختبار قانون آينشتاين غير المكتمل: E ~ m
    let e_var = CanonicalExpr::Var(VariableId(1));
    let m_var = CanonicalExpr::Var(VariableId(2));

    let dim_e = DimensionVector::from_integers(&[2, 1, -2]); // E: [L^2 M T^-2]
    let dim_m = DimensionVector::from_integers(&[0, 1, 0]);  // m: [M]

    let v_base = ("c", DimensionVector::from_integers(&[1, 0, -1])); // [L T^-1]
    let hbar_base = ("hbar", DimensionVector::from_integers(&[2, 1, -1])); // [L^2 M T^-1]

    let report_emc2 = runtime
        .resolve_incomplete_law(
            "einstein_mass_energy",
            &e_var,
            &dim_e,
            &m_var,
            &dim_m,
            &[v_base.clone(), hbar_base],
        )
        .expect("Resolution pipeline must execute successfully");

    match report_emc2.outcome {
        ResolutionOutcome::ExactEntityResolved { symbol, shadow } => {
            assert!(symbol.starts_with("Entity_DeficitResolved_"));
            assert_eq!(shadow.dof, Rational::zero());
            assert_eq!(report_emc2.candidate_solutions.len(), 1);
            assert_eq!(report_emc2.candidate_solutions[0].0, "c");
            assert_eq!(report_emc2.candidate_solutions[0].1, Rational::from_i64(2));
            assert!(report_emc2.completed_expr.is_some());
        }
        other => panic!("Expected ExactEntityResolved, got {:?}", other),
    }

    // 2. اختبار قانون نيوتن للجاذبية غير المكتمل: F ~ (m1 * m2) / r^2
    let f_var = CanonicalExpr::Var(VariableId(10));
    let m1 = CanonicalExpr::Var(VariableId(11));
    let m2 = CanonicalExpr::Var(VariableId(12));
    let r = CanonicalExpr::Var(VariableId(13));
    let r_sq = CanonicalExpr::Pow(Box::new(r), 2);
    let num = CanonicalExpr::Mul(vec![m1, m2]);
    let rhs_grav = CanonicalExpr::Div(Box::new(num), Box::new(r_sq));

    let dim_f = DimensionVector::from_integers(&[1, 1, -2]);     // [L M T^-2]
    let dim_m_body = DimensionVector::from_integers(&[0, 1, 0]); // [M]
    let dim_r_len = DimensionVector::from_integers(&[1, 0, 0]);  // [L]
    let dim_rhs_grav = DimensionVector::from_integers(&[-2, 2, 0]);

    runtime.dim_context.bind(VariableId(10), dim_f.clone());
    runtime.dim_context.bind(VariableId(11), dim_m_body.clone());
    runtime.dim_context.bind(VariableId(12), dim_m_body);
    runtime.dim_context.bind(VariableId(13), dim_r_len);

    let g_base = ("G", DimensionVector::from_integers(&[3, -1, -2]));

    let report_grav = runtime
        .resolve_incomplete_law(
            "newton_gravity",
            &f_var,
            &dim_f,
            &rhs_grav,
            &dim_rhs_grav,
            &[v_base, g_base],
        )
        .expect("Gravity resolution must execute successfully");

    match report_grav.outcome {
        ResolutionOutcome::ExactEntityResolved { shadow, .. } => {
            assert_eq!(shadow.dof, Rational::zero());
            assert_eq!(report_grav.candidate_solutions.len(), 1);
            assert_eq!(report_grav.candidate_solutions[0].0, "G");
            assert_eq!(report_grav.candidate_solutions[0].1, Rational::one());
        }
        other => panic!("Expected ExactEntityResolved for gravity, got {:?}", other),
    }

    // 3. اختبار عجز انحلال بيتا (بدون نيوترينو): درجات حرية غير منعدمة dof > 0 -> حجر صحي
    let n_var = CanonicalExpr::Var(VariableId(30));
    let p_var = CanonicalExpr::Var(VariableId(31));
    let dim_n = DimensionVector::from_integers(&[2, 1, -2]);
    let dim_p = DimensionVector::from_integers(&[0, 1, 0]);

    let initial_quarantine_count = runtime.quarantine.len();

    let report_beta = runtime
        .resolve_incomplete_law(
            "beta_decay_missing_neutrino",
            &n_var,
            &dim_n,
            &p_var,
            &dim_p,
            &[], // لا توجد قواعد مرشحة
        )
        .expect("Quarantine evaluation must succeed");

    match report_beta.outcome {
        ResolutionOutcome::Quarantined(shadow) => {
            assert!(shadow.dof > Rational::zero());
            assert!(!shadow.dim_deficit.is_dimensionless());
            // التحقق من الحفظ في الحجر الصحي الإبستمولوجي
            assert_eq!(runtime.quarantine.len(), initial_quarantine_count + 1);
        }
        other => panic!("Expected Quarantined for deficit without bases, got {:?}", other),
    }
}

#[test]
fn test_knowledge_tree_sovereign_derivation_without_hardcoded_bridges() {
    let mut runtime = AletheiaRuntime::boot_or_create(None, 7)
        .expect("In-memory kernel boot must succeed");

    // 1. التحقق من أن سجل الجسور فارغ تماماً عند الإقلاع النظيف (لا توجد جسور معرفة يدوياً في الكود)
    assert!(
        runtime.sovereignty_engine.bridge_registry.bridges().is_empty(),
        "Bridge registry must be strictly empty on fresh boot - zero hardcoded bridges"
    );

    // 2. تسجيل قانون سرعة الضوء كبديهية سيادية مباشرة في الشجرة المعرفية C_known
    // c_law: c = lambda * nu حيث أبعاد c هي [L T^-1] = [1, 0, -1]
    let c_expr = CanonicalExpr::Mul(vec![
        CanonicalExpr::Var(VariableId(100)), // lambda: [L]
        CanonicalExpr::Var(VariableId(101)), // nu: [T^-1]
    ]);
    let dim_c = DimensionVector::from_integers(&[1, 0, -1]);

    runtime.register_sovereign_axiom(
        "speed_of_light_axiom",
        c_expr,
        DomainTag::Relativity,
        dim_c.clone(),
    ).expect("Registering sovereign axiom must succeed");

    // 3. محاولة حل قانون تكافؤ الكتلة والطاقة E ~ m مع تمرير مصفوفة مرشحات فارغة تماماً (&[])
    let e_var = CanonicalExpr::Var(VariableId(200));
    let m_var = CanonicalExpr::Var(VariableId(201));
    let dim_e = DimensionVector::from_integers(&[2, 1, -2]); // [L^2 M T^-2]
    let dim_m = DimensionVector::from_integers(&[0, 1, 0]);  // [M]

    let report = runtime.resolve_incomplete_law(
        "mass_energy_equivalence",
        &e_var,
        &dim_e,
        &m_var,
        &dim_m,
        &[], // لا توجد أي مدخلات يدوية أو مرشحات خارجية إطلاقاً!
    ).expect("Resolution pipeline must execute successfully");

    // 4. التأكد من أن فضاء يونيدا السالب استدعى البديهية السيادية من الشجرة المعرفية C_known تلقائياً وحل العجز
    match report.outcome {
        ResolutionOutcome::ExactEntityResolved { symbol, shadow } => {
            assert_eq!(shadow.dof, Rational::zero(), "DoF must be zero for exact resolution");
            assert_eq!(report.candidate_solutions.len(), 1);
            assert_eq!(report.candidate_solutions[0].0, "Axiom(speed_of_light_axiom)");
            assert_eq!(report.candidate_solutions[0].1, Rational::from_i64(2)); // (c)^2
            assert!(report.completed_expr.is_some(), "Completed AST must be synthesized");
            assert!(symbol.starts_with("Entity_DeficitResolved_"));
        }
        other => panic!("Expected ExactEntityResolved directly from Knowledge Tree, got {:?}", other),
    }
}

#[test]
fn test_demand_expansion_algebraic_deficit_resolution() {
    let mut runtime = AletheiaRuntime::boot_or_create(None, 3)
        .expect("In-memory kernel boot must succeed");

    // 1. صياغة طرفي قانون توزيع الضرب على الجمع فيزيائياً:
    // a * (b + c) = (a * b) + (a * c)
    let a = VariableId(301);
    let b = VariableId(302);
    let c = VariableId(303);

    let dim_m = DimensionVector::from_integers(&[1, 0, 0]); // كتلة [M]
    let dim_l = DimensionVector::from_integers(&[0, 1, 0]); // مسافة [L]

    runtime.dim_context.bind(a, dim_m.clone());
    runtime.dim_context.bind(b, dim_l.clone());
    runtime.dim_context.bind(c, dim_l.clone());

    // الطرف الأيسر: a * (b + c)
    let lhs_expr = CanonicalExpr::Mul(vec![
        CanonicalExpr::Var(a),
        CanonicalExpr::Add(vec![CanonicalExpr::Var(b), CanonicalExpr::Var(c)]),
    ]);

    // الطرف الأيمن: (a * b) + (a * c)
    let rhs_expr = CanonicalExpr::Add(vec![
        CanonicalExpr::Mul(vec![CanonicalExpr::Var(a), CanonicalExpr::Var(b)]),
        CanonicalExpr::Mul(vec![CanonicalExpr::Var(a), CanonicalExpr::Var(c)]),
    ]);

    let dim_total = DimensionVector::from_integers(&[1, 1, 0]); // [M L]

    // 2. استدعاء معالج العجز بدون أي جسور خارجية (لا حاجة لحامل بعدي، لأن العجز هيكلي بحت audit.d2 = 1)
    let report = runtime
        .resolve_incomplete_law(
            "algebraic_distributivity_law",
            &lhs_expr,
            &dim_total,
            &rhs_expr,
            &dim_total,
            &[],
        )
        .expect("Resolution pipeline must execute successfully");

    // 3. التحقق من أن النواة لم تُحِل القانون إلى الحجر الصحي، بل فعلت قواعد التوسع الموجه (DemandExpansion)
    // وحققت التكافؤ الجبري التام وحولته إلى كيان تم حله بالاشتقاق والتوسع: Entity_ExpansionResolved_...
    match report.outcome {
        ResolutionOutcome::ExactEntityResolved { symbol, shadow } => {
            assert!(
                symbol.starts_with("Entity_ExpansionResolved_"),
                "Symbol must indicate resolution via demand expansion, got: {}",
                symbol
            );
            assert_eq!(shadow.dof, Rational::zero(), "DoF must be zero after expansion proof");
            assert_eq!(runtime.quarantine.len(), 0, "No records must remain in quarantine for proven identity");
        }
        other => panic!("Expected ExactEntityResolved via DemandExpansion, got {:?}", other),
    }

    // 4. التأكد من أن صفي التكافؤ في E-Graph توحدا تماماً
    let lhs_class = runtime.egraph.lookup_expr(&lhs_expr).expect("LHS must exist in E-Graph");
    let rhs_class = runtime.egraph.lookup_expr(&rhs_expr).expect("RHS must exist in E-Graph");
    assert_eq!(runtime.egraph.find(lhs_class), runtime.egraph.find(rhs_class), "LHS and RHS must be in same equivalence class");

    // 5. التحقق المعاكس: علاقة خاطئة جبرياً لا يمكن للتوسع الموجه اشتقاقها -> تودع بالحجر الصحي
    let false_rhs = CanonicalExpr::Mul(vec![CanonicalExpr::Var(a), CanonicalExpr::Var(a)]); // a^2
    let unprovable_report = runtime
        .resolve_incomplete_law(
            "unprovable_algebraic_relation",
            &lhs_expr,
            &dim_total,
            &false_rhs,
            &dim_total,
            &[],
        )
        .expect("Evaluation must succeed");

    match unprovable_report.outcome {
        ResolutionOutcome::Quarantined(shadow) => {
            assert!(shadow.dof > Rational::zero(), "Unprovable law must maintain positive DoF");
            assert_eq!(runtime.quarantine.len(), 1, "Unprovable law must be safely admitted to Epistemic Quarantine");
        }
        other => panic!("Expected Quarantined for unprovable algebraic relation, got {:?}", other),
    }
}

