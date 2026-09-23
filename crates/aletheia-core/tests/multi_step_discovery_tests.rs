use aletheia_algebra::{CanonicalExpr, Rational, VariableId};
use aletheia_dna::{DnaStorageEngine, MacroRuleSealer};
use aletheia_egraph::{GhostNodeManager, TransactionalEGraph};
use aletheia_lattice::{DimensionVector, DimensionalContext, LatticeData, SemanticDomain};
use aletheia_rewriting::{
    BidirectionalMeetInMiddle, EmptyDeficitContext, LyapunovAStarPlanner, MacroRule, Pattern,
};
use aletheia_yoneda::{DeficitOrchestrator, DeficitTarget, ResolutionOutcome};

#[test]
fn test_multi_step_proof_roadmap_and_lyapunov_convergence() {
    let mut egraph = TransactionalEGraph::new();
    let ctx = DimensionalContext::mathematical();

    let x = VariableId(1);
    let y = VariableId(2);

    // البداية: ((x + 0) + (y * 1))
    let start_expr = CanonicalExpr::Add(vec![
        CanonicalExpr::Add(vec![
            CanonicalExpr::Var(x),
            CanonicalExpr::Const(Rational::zero()),
        ]),
        CanonicalExpr::Mul(vec![
            CanonicalExpr::Var(y),
            CanonicalExpr::Const(Rational::one()),
        ]),
    ]);

    // الهدف: x + y
    let target_expr = CanonicalExpr::Add(vec![CanonicalExpr::Var(x), CanonicalExpr::Var(y)]);

    let rules = aletheia_rewriting::standard_algebraic_ruleset();
    let deficit = EmptyDeficitContext;

    // 1. فحص مصفوفة الوقوع كخارطة طريق استباقية
    let planner = LyapunovAStarPlanner::new(15, 2000);
    let result = planner
        .plan_equivalence(&mut egraph, &ctx, &start_expr, &target_expr, &rules, &deficit)
        .expect("فشل التخطيط الاستدلالي");

    assert!(result.success, "يجب أن ينجح التخطيط الاستدلالي متعدد الخطوات");
    assert_eq!(result.final_energy, Rational::zero(), "يجب أن تنكمش طاقة لياكونوف إلى الصفر");
    assert!(!result.proof_trace.is_empty(), "يجب تسجيل مسار البرهان الفعلي");
}

#[test]
fn test_speculative_ghost_node_instantiation_and_materialization() {
    let mut egraph = TransactionalEGraph::new();
    let mut ctx = DimensionalContext::new();

    // تسجيل الأبعاد الفيزيائية:
    // [0]: Mass (M)
    // [1]: Length (L)
    // [2]: Time (T)
    let v_dim = DimensionVector::from_integers(&[0, 1, -1]); // L T^-1 (Velocity)

    // 1. بدء معاملة تخمينية ذرية معزولة
    let checkpoint = egraph.checkpoint();
    let mut ghost_mgr = GhostNodeManager::new();

    // 2. تخليق عقدة شبحية ذات توقيع بعدي لسرعة مدارية وسيطة
    let ghost = ghost_mgr.spawn_ghost(
        &mut egraph,
        Some(LatticeData::new(v_dim.clone(), SemanticDomain::PhysicalCore)),
    );

    assert_eq!(ghost_mgr.active_count(), 1);
    assert!(!ghost.is_materialized);
    assert!(GhostNodeManager::is_ghost_variable(ghost.variable_id));

    // 3. ربط العقدة الشبحية بتعبير فيزيائي داخل الـ E-Graph
    let r_var = VariableId(10);
    let t_var = VariableId(11);
    ctx.bind(r_var, DimensionVector::from_integers(&[0, 1, 0])); // L
    ctx.bind(t_var, DimensionVector::from_integers(&[0, 0, 1])); // T

    let expr_v_def = CanonicalExpr::Div(
        Box::new(CanonicalExpr::Var(r_var)),
        Box::new(CanonicalExpr::Var(t_var)),
    );
    let id_v_def = egraph.add_expr(&expr_v_def, &ctx).unwrap();

    // دمج العقدة الشبحية مع تعريفها الوسيط
    egraph.union(ghost.class_id, id_v_def).unwrap();
    egraph.rebuild().unwrap();

    assert_eq!(egraph.find(ghost.class_id), egraph.find(id_v_def));

    // 4. ترقية وتثبيت العقدة الشبحية بعد إغلاق الفجوة
    let materialized = ghost_mgr.materialize_ghost(ghost.ghost_id).unwrap();
    assert!(materialized.is_materialized);

    // تثبيت المعاملة في الذاكرة الدائمة
    egraph.commit(checkpoint);
}

#[test]
fn test_bidirectional_meet_in_middle_and_macro_rule_dna_sealing() {
    let mut egraph = TransactionalEGraph::new();
    let ctx = DimensionalContext::mathematical();

    let a = VariableId(101);
    let b = VariableId(102);

    // LHS: (a + 0) * (b * 1)
    let lhs = CanonicalExpr::Mul(vec![
        CanonicalExpr::Add(vec![
            CanonicalExpr::Var(a),
            CanonicalExpr::Const(Rational::zero()),
        ]),
        CanonicalExpr::Mul(vec![
            CanonicalExpr::Var(b),
            CanonicalExpr::Const(Rational::one()),
        ]),
    ]);

    // RHS: a * b
    let rhs = CanonicalExpr::Mul(vec![CanonicalExpr::Var(a), CanonicalExpr::Var(b)]);

    let rules = aletheia_rewriting::standard_algebraic_ruleset();
    let deficit = EmptyDeficitContext;

    // 1. تشغيل البحث ثنائي الاتجاه والالتقاء في المنتصف
    let bidi = BidirectionalMeetInMiddle::new(15, 2000);
    let result = bidi
        .search_intersection(&mut egraph, &ctx, &lhs, &rhs, &rules, None, &deficit)
        .expect("فشل البحث ثنائي الاتجاه");

    assert!(result.success, "يجب أن يلتقي البحث ثنائي الاتجاه في المنتصف");

    // 2. صياغة قاعدة كبرى (Macro-Rule) من المسار المكتشف
    let macro_rule = MacroRule::new(
        "Macro_SimplifyMulAddConstants",
        Pattern::from_canonical_expr(&lhs),
        Pattern::from_canonical_expr(&rhs),
    );

    // 3. ختم وتخليد القاعدة الكبرى في شريط الـ DNA الثنائي عبر Anti-Unification
    let mut storage = DnaStorageEngine::from_memory(Vec::new()).expect("فشل تهيئة محرك الـ DNA");
    let initial_axioms = storage.header.total_axioms;

    let offset = MacroRuleSealer::seal_macro_rule(&mut storage, &macro_rule, 1)
        .expect("فشل ختم القاعدة الكبرى في الـ DNA");

    assert!(offset > 0, "يجب أن تكون إزاحة السجل في الـ DNA موجبة");
    assert_eq!(
        storage.header.total_axioms,
        initial_axioms + 1,
        "يجب زيادة عداد البديهيات السيادية بعد الختم"
    );
}

#[test]
fn test_yoneda_speculative_ghost_resolution_flow() {
    let mut egraph = TransactionalEGraph::new();
    let ctx = DimensionalContext::mathematical();

    let x = CanonicalExpr::Var(VariableId(50));
    let y = CanonicalExpr::Var(VariableId(50)); // متطابقان أصلاً

    let target = DeficitTarget::scalar(&x, &y);
    let rules = aletheia_rewriting::standard_algebraic_ruleset();

    let outcome = DeficitOrchestrator::resolve_speculative_with_ghost(
        &mut egraph,
        &ctx,
        target,
        &[],
        "Law_Identity_Speculative",
        &rules,
    )
    .expect("فشل منسق يونيدا التخميني");

    match outcome {
        ResolutionOutcome::ExactEntityResolved { symbol, .. } => {
            assert!(symbol.contains("Entity_DeficitResolved"));
        }
        _ => panic!("كان من المتوقع حل الكيان فورياً للتطابق التام"),
    }
}
