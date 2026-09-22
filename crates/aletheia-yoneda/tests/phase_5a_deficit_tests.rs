use aletheia_algebra::{CanonicalExpr, Rational, VariableId};
use aletheia_egraph::TransactionalEGraph;
use aletheia_lattice::{DimensionVector, DimensionalContext, SemanticDomain};
use aletheia_rewriting::DeficitContext;
use aletheia_yoneda::*;

#[test]
fn test_parallel_audit_no_early_assassination() {
    let egraph = TransactionalEGraph::new();
    let mut ctx = DimensionalContext::new();

    let x = VariableId(0);
    let m = VariableId(1);

    // x له بُعد طاقة [M L^2 T^-2]
    let energy_dim = DimensionVector::from_integers(&[1, 2, -2]);
    // m له بُعد كتلة [M]
    let mass_dim = DimensionVector::from_integers(&[1, 0, 0]);

    ctx.bind(x, energy_dim);
    ctx.bind(m, mass_dim);

    let expr_lhs = CanonicalExpr::Var(x);
    let expr_rhs = CanonicalExpr::Var(m);

    // فحص الفرضية: E == m
    let audit = ParallelSpectralAuditor::audit_equivalence(&egraph, &ctx, &expr_lhs, &expr_rhs);

    // المبدأ الدستوري: حظر الإعدام المبكر
    // لا يجوز رفع علم الرفض القاتل لأن الفجوة بعدية قابلة للرتق
    assert!(!audit.has_fatal_contradiction());
    assert!(audit.has_reparable_deficit());
    assert!(audit.d1 > 0); // عجز بعدي
    assert_eq!(audit.d2, 1); // فجوة جبرية أولية

    // فحص التناقض القاتل الصريح: 1 = 0
    let one_expr = CanonicalExpr::Const(Rational::one());
    let zero_expr = CanonicalExpr::Const(Rational::zero());
    let fatal_audit = ParallelSpectralAuditor::audit_equivalence(&egraph, &ctx, &one_expr, &zero_expr);
    assert!(fatal_audit.has_fatal_contradiction());
    assert!(!fatal_audit.has_reparable_deficit());
}

#[test]
fn test_linear_multi_term_homogeneity_rref() {
    // الحدود الجمعية: T1 = [L^2 T^-2], T2 = [L^2 T^-2] (متجانسة)
    let t1 = DimensionVector::from_integers(&[0, 2, -2]);
    let t2 = DimensionVector::from_integers(&[0, 2, -2]);

    let res_homo = LinearRREFEngine::solve_homogeneity(&[t1, t2], &[]);
    assert!(res_homo.is_consistent);
    assert!(res_homo.deficit_vector.is_dimensionless());
    assert_eq!(res_homo.dof, Rational::zero());

    // حد غير متجانس: T3 = [M] مقابل T1 = [L^2 T^-2]
    // نبحث في قواعد كسرية: قاعدة 1 = [L T^-1] (سرعة v)، قاعدة 2 = [M] (كتلة m)
    let target_deficit = DimensionVector::from_integers(&[0, 2, -2]);
    let velocity_base = DimensionVector::from_integers(&[0, 1, -1]); // v
    let candidate_bases = vec![velocity_base];

    let res_system = LinearRREFEngine::solve_linear_system(&candidate_bases, &target_deficit);
    assert!(res_system.is_consistent);
    assert_eq!(res_system.rank, 1);
    assert_eq!(res_system.dof, Rational::zero());

    let sol = res_system.particular_solution.unwrap();
    // [v]^2 = [L^2 T^-2] => الأس المطلوب هو 2
    assert_eq!(sol[0], Rational::from_i64(2));
}

#[test]
fn test_opposing_dimensional_differences_do_not_cancel() {
    // T1 = [M]
    let t1 = DimensionVector::from_integers(&[1, 0, 0]);
    // T2 = [M L] (الفارق +[L])
    let t2 = DimensionVector::from_integers(&[1, 1, 0]);
    // T3 = [M L^-1] (الفارق -[L])
    let t3 = DimensionVector::from_integers(&[1, -1, 0]);

    // المجموع التراكمي الساذج (+L) + (-L) = 0 كان سيعلن التجانس كذباً!
    // الفحص الفردي الصارم يمنع هذا التلاشي العرضي ويكتشف العجز الحقيقي
    let res = LinearRREFEngine::solve_homogeneity(&[t1, t2, t3], &[]);
    assert!(!res.deficit_vector.is_dimensionless());
}

#[test]
fn test_toric_smith_normal_form_power_law() {
    // مسألة قانون قوى: y = x^alpha
    // target = [2] (أس مربع سرعة الضوء c^2)
    // candidate = [[1]] (أس سرعة الضوء c)
    let target = vec![Rational::from_i64(2)];
    let candidate = vec![vec![Rational::one()]];
    let degrees = vec![1];

    let res = ToricIdealClassifier::solve_power_law_relation(&target, &candidate, &degrees, 50);
    match res {
        ToricResolutionResult::Solved { exponents, dof } => {
            assert_eq!(exponents.len(), 1);
            assert_eq!(exponents[0], Rational::from_i64(2));
            assert_eq!(dof, Rational::zero());
        }
        _ => panic!("Expected solved toric power-law relation"),
    }
}

#[test]
fn test_macaulay_guard_dos_prevention() {
    // درجات كثيرات حدود ضخمة: sum(deg - 1) + 1
    let degrees = vec![10, 15, 20];
    let bound = ToricIdealClassifier::compute_macaulay_bound(&degrees);
    // (10 - 1) + (15 - 1) + (20 - 1) + 1 = 9 + 14 + 19 + 1 = 43
    assert_eq!(bound, 43);

    // سقف الميزانية الآمنة = 30
    let res = ToricIdealClassifier::check_macaulay_budget(&degrees, 30);
    assert!(res.is_err());
    assert_eq!(res.unwrap_err(), 43);

    // فحص التحويل الفوري للحجر عند تجاوز الميزانية
    let target = vec![Rational::one()];
    let candidate = vec![vec![Rational::one()]];
    let toric_res = ToricIdealClassifier::solve_power_law_relation(&target, &candidate, &degrees, 30);
    assert!(matches!(
        toric_res,
        ToricResolutionResult::HighComplexitySafeQuarantine { macaulay_degree: 43, budget: 30 }
    ));
}

#[test]
fn test_tensorial_rank_gap_and_einstein_contraction() {
    let scalar_sig = TensorSignature::scalar();
    let vector_sig = TensorSignature::vector();

    // فجوة بين كمية قياسية ومتجه
    let gap = TensorialEngine::compute_rank_gap(scalar_sig, vector_sig);
    assert!(!gap.is_scalar_invariant);
    assert_eq!(gap.required_rank, 1);

    // التحقق من الانكماش: كائن برتبة 1 يستطيع الانكماش مع المتجه لينتج قياسياً
    let form1_sig = TensorSignature::form_1();
    assert!(TensorialEngine::can_contract_to_scalar(gap, form1_sig));
}

#[test]
fn test_coupling_carrier_and_fractional_dof() {
    // 1. اختبار حامل الاقتران البعدي للجسور المعرفية
    let c_squared_dim = DimensionVector::from_integers(&[0, 2, -2]);
    let carrier = CouplingCarrier::new("c^2", c_squared_dim.clone(), SemanticDomain::PhysicalCore);
    assert_eq!(carrier.symbol, "c^2");
    assert_eq!(carrier.dimension, c_squared_dim);

    // 2. اختبار درجات الحرية الكسرية dof in Q (مثل 1/2 للكميات المقترنة بجذور)
    let half_dof = Rational::new(1, 2).unwrap();
    let shadow = LatentShadow {
        shadow_id: [0u8; 32],
        origin_law_ids: vec!["law_quantum_gravity_bridge".into()],
        dim_deficit: c_squared_dim,
        tensorial_rank: 0,
        dof: half_dof,
        spectral_audit: DiagnosticVector::default(),
        coupling_carrier: Some(carrier),
        target_classes: Vec::new(),
        macaulay_ceiling: 5,
    };

    // التحقق من حفظ القيمة الكسرية بدقة
    assert_eq!(shadow.dof.numer().to_string(), "1");
    assert_eq!(shadow.dof.denom().to_string(), "2");

    // التحقق من ربط واجهة DeficitContext للمحور الخامس وتقريب السقف
    assert_eq!(shadow.remaining_dof(), 1);
    assert_eq!(shadow.macaulay_bound(), 5);
}

#[test]
fn test_orchestrator_exact_resolution_and_quarantine() {
    let egraph = TransactionalEGraph::new();
    let mut ctx = DimensionalContext::new();

    let e_var = VariableId(0);
    let m_var = VariableId(1);

    // E = [M L^2 T^-2]
    let energy_dim = DimensionVector::from_integers(&[1, 2, -2]);
    // m = [M]
    let mass_dim = DimensionVector::from_integers(&[1, 0, 0]);

    ctx.bind(e_var, energy_dim);
    ctx.bind(m_var, mass_dim);

    let expr_e = CanonicalExpr::Var(e_var);
    let expr_m = CanonicalExpr::Var(m_var);

    // قاعدة السرعة v = [L T^-1]
    let v_base = DimensionVector::from_integers(&[0, 1, -1]);

    // الحالة 1: قاعدة v متاحة للاقتران => العجز البعدي [L^2 T^-2] قابل للحل تماماً بـ v^2
    // dof = 0 => ExactEntityResolved
    let target1 = DeficitTarget::scalar(&expr_e, &expr_m);
    let outcome_resolved = DeficitOrchestrator::resolve_deficit(
        &egraph,
        &ctx,
        target1,
        &[v_base],
        Vec::new(),
        "einstein_mass_energy_hypothesis",
    ).unwrap();

    match outcome_resolved {
        ResolutionOutcome::ExactEntityResolved { symbol, shadow } => {
            assert!(symbol.starts_with("Entity_DeficitResolved_"));
            assert_eq!(shadow.dof, Rational::zero());
            assert!(shadow.coupling_carrier.is_some());
        }
        _ => panic!("Expected ExactEntityResolved for solvable mass-energy bridge"),
    }

    // الحالة 2: لا توجد قواعد كافية لحل العجز => dof > 0 => Quarantined
    let target2 = DeficitTarget::scalar(&expr_e, &expr_m);
    let outcome_quarantined = DeficitOrchestrator::resolve_deficit(
        &egraph,
        &ctx,
        target2,
        &[], // لا توجد قواعد مرشحة
        Vec::new(),
        "unresolved_bridge_hypothesis",
    ).unwrap();

    match outcome_quarantined {
        ResolutionOutcome::Quarantined(shadow) => {
            assert!(shadow.dof > Rational::zero());
            assert!(!shadow.dim_deficit.is_dimensionless());
        }
        _ => panic!("Expected Quarantined for deficit with no candidate bases"),
    }
}
