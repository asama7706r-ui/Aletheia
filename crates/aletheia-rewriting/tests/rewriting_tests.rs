use aletheia_algebra::{CanonicalExpr, Rational, VariableId};
use aletheia_egraph::{EClassId, TransactionalEGraph};
use aletheia_lattice::DimensionalContext;
use aletheia_rewriting::*;

#[test]
fn test_leapfrog_slice_intersection() {
    let list1 = vec![EClassId(1), EClassId(3), EClassId(5), EClassId(7), EClassId(9)];
    let list2 = vec![EClassId(3), EClassId(5), EClassId(8), EClassId(9), EClassId(10)];
    let list3 = vec![EClassId(2), EClassId(3), EClassId(5), EClassId(9), EClassId(12)];

    let intersection = leapfrog_intersect(&[&list1, &list2, &list3]);
    assert_eq!(intersection, vec![EClassId(3), EClassId(5), EClassId(9)]);

    // فحص التقاطع الخالي
    let disjoint = vec![EClassId(100), EClassId(200)];
    assert!(leapfrog_intersect(&[&list1, &disjoint]).is_empty());
}

#[test]
fn test_pattern_wildcard_and_literal_var_separation() {
    let mut egraph = TransactionalEGraph::new();
    let ctx = DimensionalContext::mathematical();

    let x0 = VariableId(0);
    let x1 = VariableId(1);

    // إضافة التعبير: x0 + x1
    let expr = CanonicalExpr::Add(vec![CanonicalExpr::Var(x0), CanonicalExpr::Var(x1)]);
    let root = egraph.add_expr(&expr, &ctx).unwrap();
    let id_x1 = egraph.add_expr(&CanonicalExpr::Var(x1), &ctx).unwrap();

    // 1. نمط يطابق متغير مادي x0 مع متغير حر ?w: LiteralVar(x0) + Wildcard(0)
    let pat_match = Pattern::add(vec![Pattern::literal_var(x0), Pattern::wildcard(0)]);
    let matches = RelationalMatcher::find_matches(&egraph, &pat_match, None);
    assert_eq!(matches.len(), 1);
    assert_eq!(matches[0].root, root);
    assert_eq!(
        matches[0].subst.get(0).unwrap(),
        egraph.find(id_x1)
    );

    // 2. نمط يتطلب متغيراً مادياً غير موجود x99: LiteralVar(x99) + Wildcard(0)
    let x99 = VariableId(99);
    let pat_no_match = Pattern::add(vec![Pattern::literal_var(x99), Pattern::wildcard(0)]);
    let matches_fail = RelationalMatcher::find_matches(&egraph, &pat_no_match, None);
    assert!(matches_fail.is_empty());
}

#[test]
fn test_apriori_reachability_farkas_pruning() {
    let x0 = VariableId(0);
    let x1 = VariableId(1);

    // التعبير الابتدائي: x0
    let start = CanonicalExpr::Var(x0);
    // التعبير المستهدف: x0 + x1 (يتضمن متغيراً جديداً x1 لا تولده أي قاعدة)
    let target = CanonicalExpr::Add(vec![CanonicalExpr::Var(x0), CanonicalExpr::Var(x1)]);

    let diffs = vec![SpectralVector::from_expr(&CanonicalExpr::Const(Rational::zero()))];
    let filter = APrioriReachabilityFilter::new(diffs);

    // استبعاد فوري في O(1) لأن x1 غير قابل للتوليد
    assert!(!filter.is_reachable(&start, &target));

    // التحول العكسي: من (x0 + 0) إلى x0 ممكن ومحقق
    let start_expr = CanonicalExpr::Add(vec![
        CanonicalExpr::Var(x0),
        CanonicalExpr::Const(Rational::zero()),
    ]);
    let target_expr = CanonicalExpr::Var(x0);
    let reachable_filter = APrioriReachabilityFilter::new(vec![SpectralVector {
        op_add: -1,
        const_count: -1,
        ..Default::default()
    }]);

    assert!(reachable_filter.is_reachable(&start_expr, &target_expr));
}

#[test]
fn test_canonical_reduction_and_early_exit() {
    let mut egraph = TransactionalEGraph::new();
    let ctx = DimensionalContext::mathematical();

    let x = VariableId(0);

    // LHS = x * 1
    let expr_lhs = CanonicalExpr::Mul(vec![
        CanonicalExpr::Var(x),
        CanonicalExpr::Const(Rational::one()),
    ]);
    let id_lhs = egraph.add_expr(&expr_lhs, &ctx).unwrap();

    // RHS = x
    let expr_rhs = CanonicalExpr::Var(x);
    let id_rhs = egraph.add_expr(&expr_rhs, &ctx).unwrap();

    assert_ne!(egraph.find(id_lhs), egraph.find(id_rhs));

    let rules = standard_algebraic_ruleset();
    let deficit = EmptyDeficitContext;

    let config = SaturationConfig {
        max_iterations: 10,
        node_limit: 1000,
        early_exit_target: Some((id_lhs, id_rhs)),
        roadmap_plan: None,
    };

    let engine = SaturationEngine::new(config);
    let report = engine.run(&mut egraph, &ctx, &rules, &deficit).unwrap();

    // تحقق البرهان بالخروج المبكر في O(1)
    assert!(report.proved_equivalence);
    assert_eq!(egraph.find(id_lhs), egraph.find(id_rhs));
    assert!(report.proof_trace.contains(&"mul_one"));
}

#[test]
fn test_speculative_ledger_macaulay_rollback() {
    let mut egraph = TransactionalEGraph::new();
    let ctx = DimensionalContext::mathematical();

    let x = VariableId(0);
    let id_x = egraph.add_expr(&CanonicalExpr::Var(x), &ctx).unwrap();

    // قاعدة توسعية تنتج تضخماً كبيراً
    // x -> (x + x)
    let x_pat = Pattern::wildcard(0);
    let rule_expand = RewriteRule::new(
        "expand_double",
        RuleKind::DemandExpansion,
        x_pat.clone(),
        Pattern::add(vec![x_pat.clone(), x_pat]),
    );

    let initial_nodes = egraph.node_count();

    // سقف ماكولاي مقيد جداً: bound = 0 يمنع أي زيادة
    let deficit = SimpleDeficitContext::new(1, vec![id_x], 0);

    let config = SaturationConfig {
        max_iterations: 5,
        node_limit: 50,
        early_exit_target: None,
        roadmap_plan: None,
    };

    let engine = SaturationEngine::new(config);
    let res = engine.run(&mut egraph, &ctx, &[rule_expand], &deficit);

    // يجب أن يفشل بتناقض كمي ويعود بالذاكرة لنفس الحالة الأولى 100% (Rollback)
    assert!(matches!(res, Err(RewritingError::QuantitativeContradiction { .. })));
    assert_eq!(egraph.node_count(), initial_nodes);
}

#[test]
fn test_hypergraph_dijkstra_mdl_extractor() {
    let mut egraph = TransactionalEGraph::new();
    let ctx = DimensionalContext::mathematical();

    let x = VariableId(0);

    // صيغة معقدة: (x * 1) + 0
    let complex_expr = CanonicalExpr::Add(vec![
        CanonicalExpr::Mul(vec![
            CanonicalExpr::Var(x),
            CanonicalExpr::Const(Rational::one()),
        ]),
        CanonicalExpr::Const(Rational::zero()),
    ]);
    let root = egraph.add_expr(&complex_expr, &ctx).unwrap();

    // تشغيل قواعد الاختزال الكنسي
    let rules = standard_algebraic_ruleset();
    let deficit = EmptyDeficitContext;
    let engine = SaturationEngine::new(SaturationConfig::default());
    let report = engine.run(&mut egraph, &ctx, &rules, &deficit).unwrap();

    // استخلاص شجرة التعبير الأبسط وفق نصل أوكام
    let extractor = AstExtractor::new(&egraph);
    let extracted = extractor.extract(root, report.proof_trace).unwrap();

    // يجب أن تكون الصيغة المستخلصة هي x حصراً بحجم 1!
    assert_eq!(extracted.ast, CanonicalExpr::Var(x));
    assert_eq!(extracted.cost.size, 1);
    assert_eq!(extracted.cost.degree, 1);
    assert!(extracted.is_provably_minimal);
    assert!(!extracted.proof_trace.is_empty());
}

#[test]
fn test_two_phase_distributivity_saturation() {
    let mut egraph = TransactionalEGraph::new();
    let ctx = DimensionalContext::mathematical();

    let a = VariableId(0);
    let b = VariableId(1);
    let c = VariableId(2);

    // a * (b + c)
    let expr1 = CanonicalExpr::Mul(vec![
        CanonicalExpr::Var(a),
        CanonicalExpr::Add(vec![CanonicalExpr::Var(b), CanonicalExpr::Var(c)]),
    ]);
    let id1 = egraph.add_expr(&expr1, &ctx).unwrap();

    // (a * b) + (a * c)
    let expr2 = CanonicalExpr::Add(vec![
        CanonicalExpr::Mul(vec![CanonicalExpr::Var(a), CanonicalExpr::Var(b)]),
        CanonicalExpr::Mul(vec![CanonicalExpr::Var(a), CanonicalExpr::Var(c)]),
    ]);
    let id2 = egraph.add_expr(&expr2, &ctx).unwrap();

    assert_ne!(egraph.find(id1), egraph.find(id2));

    let rules = standard_algebraic_ruleset();
    // عجز موجه للربط بينهما
    let deficit = SimpleDeficitContext::new(1, vec![id1, id2], 10);

    let config = SaturationConfig {
        max_iterations: 10,
        node_limit: 1000,
        early_exit_target: Some((id1, id2)),
        roadmap_plan: None,
    };

    let engine = SaturationEngine::new(config);
    let report = engine.run(&mut egraph, &ctx, &rules, &deficit).unwrap();

    assert!(report.proved_equivalence);
    assert_eq!(egraph.find(id1), egraph.find(id2));
}

#[test]
fn test_formal_cycle_contradiction_detection() {
    let mut egraph = TransactionalEGraph::new();

    // إنشاء فئة دائرية غير مؤسسة دون أي عقدة أرضية (Ungrounded Cycle)
    let dummy_id = egraph.union_find.make_set();
    let cycle_node = aletheia_egraph::ENode::Neg(dummy_id);
    let mut class = aletheia_egraph::EClass::new(dummy_id, None);
    class.nodes.push(cycle_node);
    egraph.classes.insert(dummy_id, class);

    let extractor = AstExtractor::new(&egraph);
    let res = extractor.extract(dummy_id, Vec::new());

    // يجب أن ترفض الخوارزمية إنتاج تعبير لانهائي وتطلق FormalCycleContradiction
    assert!(matches!(
        res,
        Err(RewritingError::FormalCycleContradiction(_))
    ));
}

#[test]
fn test_commutative_zero_matching_with_inverted_ids() {
    let mut egraph = TransactionalEGraph::new();
    let ctx = DimensionalContext::mathematical();

    // إضافة الثابت 0 أولاً ليحصل على معرف أصغر في الذاكرة
    let id_zero = egraph
        .add_expr(&CanonicalExpr::Const(Rational::zero()), &ctx)
        .unwrap();

    // إضافة المتغير x ثانياً ليحصل على معرف أكبر
    let x = VariableId(42);
    let id_x = egraph.add_expr(&CanonicalExpr::Var(x), &ctx).unwrap();

    // في الذاكرة: المعرفات id_zero < id_x
    assert!(id_zero.0 < id_x.0);

    // إضافة (0 + x) - سيفرزها الـ E-Graph كنسياً إلى Add([id_zero, id_x])
    let expr_add = CanonicalExpr::Add(vec![
        CanonicalExpr::Const(Rational::zero()),
        CanonicalExpr::Var(x),
    ]);
    let id_add = egraph.add_expr(&expr_add, &ctx).unwrap();

    // قاعدة add_zero الكنسية: (?x + 0) -> ?x
    let rules = standard_algebraic_ruleset();
    let deficit = EmptyDeficitContext;

    let config = SaturationConfig {
        max_iterations: 5,
        node_limit: 100,
        early_exit_target: Some((id_add, id_x)),
        roadmap_plan: None,
    };

    let engine = SaturationEngine::new(config);
    let report = engine.run(&mut egraph, &ctx, &rules, &deficit).unwrap();

    // يجب أن تنجح المطابقة التبادلية ويُثبت التكافؤ (0 + x) == x
    assert!(report.proved_equivalence);
    assert_eq!(egraph.find(id_add), egraph.find(id_x));
}

#[test]
fn test_n_ary_slice_reduction() {
    let mut egraph = TransactionalEGraph::new();
    let ctx = DimensionalContext::mathematical();

    let a = VariableId(10);
    let b = VariableId(11);

    // التعبير متعدد المعاملات (N-Ary): a + b + 0
    let expr_nary = CanonicalExpr::Add(vec![
        CanonicalExpr::Var(a),
        CanonicalExpr::Var(b),
        CanonicalExpr::Const(Rational::zero()),
    ]);
    let id_nary = egraph.add_expr(&expr_nary, &ctx).unwrap();

    // التعبير المتوقع بعد الاختزال مع إعادة بناء السياق: a + b
    let expr_ab = CanonicalExpr::Add(vec![CanonicalExpr::Var(a), CanonicalExpr::Var(b)]);
    let id_ab = egraph.add_expr(&expr_ab, &ctx).unwrap();

    // التعبير الخاطئ الذي كان سينتج لو مُحي السياق: b
    let id_b = egraph.add_expr(&CanonicalExpr::Var(b), &ctx).unwrap();

    assert_ne!(egraph.find(id_nary), egraph.find(id_ab));
    assert_ne!(egraph.find(id_nary), egraph.find(id_b));

    let rules = standard_algebraic_ruleset();
    let deficit = EmptyDeficitContext;

    let config = SaturationConfig {
        max_iterations: 5,
        node_limit: 200,
        early_exit_target: Some((id_nary, id_ab)),
        roadmap_plan: None,
    };

    let engine = SaturationEngine::new(config);
    let report = engine.run(&mut egraph, &ctx, &rules, &deficit).unwrap();

    // 1. تحقق اختزال (a + b + 0) إلى (a + b)
    assert!(report.proved_equivalence);
    assert_eq!(egraph.find(id_nary), egraph.find(id_ab));

    // 2. التحقق الحاسم من عدم محو السياق: التعبير لا يساوي b بمفردها
    assert_ne!(egraph.find(id_nary), egraph.find(id_b));
}

#[test]
fn test_speculative_ledger_net_growth_with_preexisting_nodes() {
    let mut egraph = TransactionalEGraph::new();
    let ctx = DimensionalContext::mathematical();

    // زرع 40 عقدة مستقلة سابقة في الـ E-Graph لمحاكاة بيئة بحث معقدة
    for i in 100..140 {
        let v = VariableId(i);
        egraph.add_expr(&CanonicalExpr::Var(v), &ctx).unwrap();
    }
    assert!(egraph.node_count() >= 40);

    let x = VariableId(1);
    let id_x = egraph.add_expr(&CanonicalExpr::Var(x), &ctx).unwrap();

    // قاعدة توسعية: x -> (x + x)
    let x_pat = Pattern::wildcard(0);
    let rule_expand = RewriteRule::new(
        "expand_double",
        RuleKind::DemandExpansion,
        x_pat.clone(),
        Pattern::add(vec![x_pat.clone(), x_pat]),
    );

    // سقف ماكولاي يسمح بنمو صافٍ مقداره 3 أضعاف الحجم المحلي
    let deficit = SimpleDeficitContext::new(1, vec![id_x], 3);

    let config = SaturationConfig {
        max_iterations: 3,
        node_limit: 200,
        early_exit_target: None,
        roadmap_plan: None,
    };

    let engine = SaturationEngine::new(config);
    let res = engine.run(&mut egraph, &ctx, &[rule_expand], &deficit);

    // يجب أن تنجح العملية ولا يطلق دفتر الأستاذ تناقضاً كمياً زائفاً
    assert!(res.is_ok());
}

#[test]
fn test_macro_rule_synthesis() {
    let mut egraph = TransactionalEGraph::new();
    let ctx = DimensionalContext::mathematical();

    let a = VariableId(0);
    let b = VariableId(1);
    let c = VariableId(2);

    // الهدف 1: a * (b + c)
    let expr1 = CanonicalExpr::Mul(vec![
        CanonicalExpr::Var(a),
        CanonicalExpr::Add(vec![CanonicalExpr::Var(b), CanonicalExpr::Var(c)]),
    ]);
    let id1 = egraph.add_expr(&expr1, &ctx).unwrap();

    // الهدف 2: (a * b) + (a * c)
    let expr2 = CanonicalExpr::Add(vec![
        CanonicalExpr::Mul(vec![CanonicalExpr::Var(a), CanonicalExpr::Var(b)]),
        CanonicalExpr::Mul(vec![CanonicalExpr::Var(a), CanonicalExpr::Var(c)]),
    ]);
    let id2 = egraph.add_expr(&expr2, &ctx).unwrap();

    let rules = standard_algebraic_ruleset();
    let deficit = SimpleDeficitContext::new(1, vec![id1, id2], 10);

    let config = SaturationConfig {
        max_iterations: 10,
        node_limit: 1000,
        early_exit_target: Some((id1, id2)),
        roadmap_plan: None,
    };

    let engine = SaturationEngine::new(config);
    let report = engine.run(&mut egraph, &ctx, &rules, &deficit).unwrap();

    // إثبات التكافؤ وتركيب قاعدة عليا O(1) لعبور الهضبة
    assert!(report.proved_equivalence);
    assert!(!report.synthesized_macro_rules.is_empty());
    let macro_rule = &report.synthesized_macro_rules[0];
    assert!(macro_rule.name.starts_with("Macro_PlateauShortcut"));
}

#[test]
fn test_koszul_parity_guard_in_rewriting() {
    let mut egraph = TransactionalEGraph::new();
    let ctx = DimensionalContext::mathematical();

    let a = VariableId(0);
    let b = VariableId(1);

    // a * b
    let expr = CanonicalExpr::Mul(vec![CanonicalExpr::Var(a), CanonicalExpr::Var(b)]);
    let _id = egraph.add_expr(&expr, &ctx).unwrap();

    let x = Pattern::wildcard(0);
    let y = Pattern::wildcard(1);

    // 1. محاولة تطبيق تبادل بوزوني (+1) على عنصرين فرميونيين (درجة 1 ودرجة 1)
    // إشارة كوزول الحقيقية هي (-1)^(1*1) = -1
    let invalid_swap_rule = RewriteRule::new(
        "invalid_bosonic_swap_on_fermions",
        RuleKind::CanonicalReduction,
        Pattern::mul(vec![x.clone(), y.clone()]),
        Pattern::mul(vec![y.clone(), x.clone()]),
    ).with_guard(RuleGuard::koszul(0, 1, 1, 1, 1)); // يتوقع +1 لكن الحقيقة -1

    let matches = RelationalMatcher::find_matches(&egraph, &invalid_swap_rule.lhs, None);
    assert!(!matches.is_empty());
    // الحارس يرفض التطبيق لكافة تباديل المطابقة لحماية التناظر الفيزيائي من الانهيار
    for m in &matches {
        assert!(!invalid_swap_rule.check_guards(&egraph, &m.subst));
    }

    // 2. قاعدة متطابقة مع إشارة كوزول (-1): x * y -> -(y * x)
    let valid_fermionic_rule = RewriteRule::new(
        "valid_fermionic_anticommutation",
        RuleKind::CanonicalReduction,
        Pattern::mul(vec![x.clone(), y.clone()]),
        Pattern::neg(Pattern::mul(vec![y.clone(), x.clone()])),
    ).with_guard(RuleGuard::koszul(0, 1, 1, 1, -1)); // يتوقع -1 وإشارة كوزول -1

    for m in &matches {
        assert!(valid_fermionic_rule.check_guards(&egraph, &m.subst));
    }
}

#[test]
fn test_roadmap_plan_guided_saturation() {
    use aletheia_rewriting::LyapunovAStarPlanner;

    let mut egraph = TransactionalEGraph::new();
    let ctx = DimensionalContext::mathematical();

    let x = VariableId(10);
    // start: x + 0
    let start_expr = CanonicalExpr::Add(vec![
        CanonicalExpr::Var(x),
        CanonicalExpr::Const(Rational::zero()),
    ]);
    // target: x
    let target_expr = CanonicalExpr::Var(x);

    let rules = standard_algebraic_ruleset();
    let deficit = EmptyDeficitContext;

    let planner = LyapunovAStarPlanner::new(10, 1000);
    let plan_res = planner
        .plan_equivalence(&mut egraph, &ctx, &start_expr, &target_expr, &rules, &deficit)
        .unwrap();

    assert!(plan_res.success);
    assert_eq!(plan_res.final_energy, Rational::zero());
}

#[test]
fn test_lyapunov_astar_and_bidirectional() {
    use aletheia_rewriting::BidirectionalMeetInMiddle;

    let mut egraph = TransactionalEGraph::new();
    let ctx = DimensionalContext::mathematical();

    let a = VariableId(1);
    let b = VariableId(2);

    // LHS: (a + b) + 0
    let lhs = CanonicalExpr::Add(vec![
        CanonicalExpr::Add(vec![CanonicalExpr::Var(a), CanonicalExpr::Var(b)]),
        CanonicalExpr::Const(Rational::zero()),
    ]);
    // RHS: a + b
    let rhs = CanonicalExpr::Add(vec![CanonicalExpr::Var(a), CanonicalExpr::Var(b)]);

    let rules = standard_algebraic_ruleset();
    let deficit = EmptyDeficitContext;

    let bidi = BidirectionalMeetInMiddle::new(10, 1000);
    let res = bidi
        .search_intersection(&mut egraph, &ctx, &lhs, &rhs, &rules, None, &deficit)
        .unwrap();

    assert!(res.success);
}



