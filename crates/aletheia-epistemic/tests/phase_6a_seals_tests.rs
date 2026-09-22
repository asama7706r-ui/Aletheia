use aletheia_algebra::{CanonicalExpr, Rational, VariableId};
use aletheia_egraph::{ENode, TransactionalEGraph};
use aletheia_epistemic::{
    AnchoringSieve, AuditTarget, BridgeRegistry, BridgeSieve, DimensionalSieve, DomainBridge,
    DomainTag, EpistemicGatekeeper, EpistemicStatus, GatekeeperMode, LockType, NoetherRegistry,
    ResidualSieve,
};
use aletheia_lattice::{DimensionVector, DimensionalContext, LatticeData, SemanticDomain};
use aletheia_rewriting::Cost;
use aletheia_yoneda::CandidateSovereignLawAST;
use std::collections::HashMap;

#[test]
fn test_seal1_exact_zero_residual_and_fraction_drift_rejection() {
    let v0 = VariableId(0);
    let v1 = VariableId(1);
    let variables = vec![v0, v1];

    // النظام الخطي:
    // 2 * x0 + 3 * x1 = 7
    // 1 * x0 - 1 * x1 = 1
    let matrix = vec![
        vec![Rational::from_i64(2), Rational::from_i64(3)],
        vec![Rational::from_i64(1), Rational::from_i64(-1)],
    ];
    let rhs = vec![Rational::from_i64(7), Rational::from_i64(1)];

    // الحل الدقيق: x0 = 2, x1 = 1
    let mut exact_solution = HashMap::new();
    exact_solution.insert(v0, Rational::from_i64(2));
    exact_solution.insert(v1, Rational::from_i64(1));

    let valid_target = AuditTarget::ConstraintSystem {
        candidate_id: [1u8; 32],
        matrix: matrix.clone(),
        rhs: rhs.clone(),
        solution: exact_solution,
        variables: variables.clone(),
    };

    let receipt = ResidualSieve::verify(&valid_target);
    assert!(receipt.passed);
    assert_eq!(receipt.violation_metric, Some(Rational::zero()));

    // تعديل طفيف بالحل بمقدار 1/1000 (محاكاة انحراف عائم)
    let mut drifted_solution = HashMap::new();
    drifted_solution.insert(v0, Rational::new(2001, 1000).unwrap());
    drifted_solution.insert(v1, Rational::from_i64(1));

    let drifted_target = AuditTarget::ConstraintSystem {
        candidate_id: [2u8; 32],
        matrix,
        rhs,
        solution: drifted_solution,
        variables,
    };

    let drifted_receipt = ResidualSieve::verify(&drifted_target);
    assert!(!drifted_receipt.passed);
    // 2 * (2001/1000) + 3*1 = 4002/1000 + 3 = 7002/1000 != 7 => الفرق 2/1000 = 1/500
    assert_eq!(drifted_receipt.violation_metric, Some(Rational::new(1, 500).unwrap()));
}

#[test]
fn test_seal2_dimensional_homogeneity_and_transcendental_purity() {
    let mut ctx = DimensionalContext::new();
    let v_len1 = VariableId(10);
    let v_len2 = VariableId(11);
    let v_mass = VariableId(12);

    let len_dim = DimensionVector::from_integers(&[0, 1, 0]); // [L]
    let mass_dim = DimensionVector::from_integers(&[1, 0, 0]); // [M]

    ctx.bind(v_len1, len_dim.clone());
    ctx.bind(v_len2, len_dim.clone());
    ctx.bind(v_mass, mass_dim);

    // 1. تعبير كنسي متجانس: v_len1 + v_len2 = [L]
    let expr_homo = CanonicalExpr::Add(vec![CanonicalExpr::Var(v_len1), CanonicalExpr::Var(v_len2)]);
    let cand_homo = CandidateSovereignLawAST {
        canonical_id: [10u8; 32],
        ast: expr_homo,
        dim: len_dim.clone(),
        cost: Cost::zero(),
        proof_trace: vec![],
        asymptotic_certificate: None,
        sovereignty_epoch: 1,
    };

    let receipt_homo = DimensionalSieve::verify(&AuditTarget::sovereign(cand_homo), &ctx, None);
    assert!(receipt_homo.passed);

    // 2. تعبير غير متجانس: v_len1 + v_mass => [L] + [M] تصادم بعدي
    let expr_clash = CanonicalExpr::Add(vec![CanonicalExpr::Var(v_len1), CanonicalExpr::Var(v_mass)]);
    let cand_clash = CandidateSovereignLawAST {
        canonical_id: [11u8; 32],
        ast: expr_clash,
        dim: len_dim,
        cost: Cost::zero(),
        proof_trace: vec![],
        asymptotic_certificate: None,
        sovereignty_epoch: 1,
    };

    let receipt_clash = DimensionalSieve::verify(&AuditTarget::sovereign(cand_clash), &ctx, None);
    assert!(!receipt_clash.passed);
    assert!(receipt_clash.details.contains("Dimensional incompatibility"));
}

#[test]
fn test_seal3_multi_hop_bfs_and_bidirectional_bridges() {
    let mut registry = BridgeRegistry::new();

    let dim_m = DimensionVector::from_integers(&[1, 0, 0]); // [M]
    let dim_l = DimensionVector::from_integers(&[0, 1, 0]); // [L]

    // الجسر 1: ClassicalMechanics -> Thermodynamics (Scale = 2, Dim = [M])
    let b1 = DomainBridge::new(
        "MechToThermo",
        DomainTag::ClassicalMechanics,
        DomainTag::Thermodynamics,
        dim_m.clone(),
        Rational::from_i64(2),
    );

    // الجسر 2: Thermodynamics -> Electromagnetism (Scale = 3, Dim = [L])
    let b2 = DomainBridge::new(
        "ThermoToEM",
        DomainTag::Thermodynamics,
        DomainTag::Electromagnetism,
        dim_l.clone(),
        Rational::from_i64(3),
    );

    registry.register_bridge(b1);
    registry.register_bridge(b2);

    // 1. فحص المسار المباشر متعدد القفزات: ClassicalMechanics -> Electromagnetism
    // المقياس التراكمي = 2 * 3 = 6
    // البعد التراكمي = [M] + [L]
    let path_result = registry.find_shortest_bridge_path(
        DomainTag::ClassicalMechanics,
        DomainTag::Electromagnetism,
    );
    assert!(path_result.is_some());
    let (path, cum_scale, cum_dim) = path_result.unwrap();
    assert_eq!(path.len(), 2);
    assert_eq!(cum_scale, Rational::from_i64(6));
    assert_eq!(cum_dim, &dim_m + &dim_l);

    // 2. فحص الدعم التلقائي للمسار العكسي: Electromagnetism -> ClassicalMechanics
    // المقياس العكسي = 1/6
    // البعد العكسي = -([M] + [L])
    let inv_result = registry.find_shortest_bridge_path(
        DomainTag::Electromagnetism,
        DomainTag::ClassicalMechanics,
    );
    assert!(inv_result.is_some());
    let (inv_path, inv_scale, inv_dim) = inv_result.unwrap();
    assert_eq!(inv_path.len(), 2);
    assert_eq!(inv_scale, Rational::new(1, 6).unwrap());
    assert_eq!(inv_dim, -(&dim_m + &dim_l));
}

#[test]
fn test_seal3_unmediated_cross_domain_rejected() {
    let registry = BridgeRegistry::new();
    let receipt = BridgeSieve::verify(
        &registry,
        DomainTag::Cosmology,
        DomainTag::QuantumMechanics,
        None,
        None,
    );
    assert!(!receipt.passed);
    assert_eq!(receipt.lock_id, LockType::DomainIsolationBridge);
}

#[test]
fn test_seal4_speculative_gedankenexperiment_atomic_rollback() {
    let mut egraph = TransactionalEGraph::new();
    let noether = NoetherRegistry::standard_physics();

    // حالة ابتدائية في الـ E-Graph
    let base_cid = egraph.add_node(ENode::Const(Rational::from_i64(100)), None);
    let initial_classes = egraph.class_count();
    let initial_nodes = egraph.node_count();

    let mut solution = HashMap::new();
    let v_test = VariableId(99);
    solution.insert(v_test, Rational::from_i64(42));

    // إجراء التجربة الفكرية
    let invariants = vec!["EnergyConservation".to_string()];
    let receipt = AnchoringSieve::verify(
        &noether,
        &invariants,
        Some(&mut egraph),
        Some(&solution),
        None,
    );

    assert!(receipt.passed);
    // التحقق الصارم من التراجع الذري اللحظي بنسبة 100%
    assert_eq!(egraph.class_count(), initial_classes);
    assert_eq!(egraph.node_count(), initial_nodes);
    assert_eq!(egraph.find(base_cid), base_cid);
}

#[test]
fn test_seal4_captures_lattice_contradictory_merge_as_dispute() {
    let mut egraph = TransactionalEGraph::new();

    // 1. إدخال عقدة ذات بعد طول [L] في الـ E-Graph القائم
    let len_dim = DimensionVector::from_integers(&[0, 1, 0]);
    let len_data = LatticeData::new(len_dim, SemanticDomain::PhysicalCore);
    let v0 = VariableId(0);
    let node_v0 = egraph.add_node(ENode::Var(v0), Some(len_data));

    // 2. إدخال عقدة ذات بعد كتلة [M]
    let mass_dim = DimensionVector::from_integers(&[1, 0, 0]);
    let mass_data = LatticeData::new(mass_dim, SemanticDomain::PhysicalCore);
    let v1 = VariableId(1);
    let node_v1 = egraph.add_node(ENode::Var(v1), Some(mass_data));

    // 3. في التجربة الفكرية، محاولة دمج v0 مع v1 (مسافة مع كتلة)
    // هذا سيؤدي لـ ContradictoryMerge في LatticeData
    let cp = egraph.checkpoint();
    let merge_res = egraph.union(node_v0, node_v1);
    assert!(merge_res.is_err()); // تصادم أبعاد فوري
    egraph.rollback(cp);

    // فحص محاكاة تجربة فكرية تؤدي إلى ContradictoryMerge عبر مرشح يحاول دمج مسافة وكتلة
    let mut gatekeeper = EpistemicGatekeeper::new();
    gatekeeper.dimensional_context.bind(v0, DimensionVector::from_integers(&[0, 1, 0]));
    gatekeeper.dimensional_context.bind(v1, DimensionVector::from_integers(&[1, 0, 0]));

    // مرشح سيادي يحاول جمع مسافة مع كتلة (L + M)
    let clash_expr = CanonicalExpr::Add(vec![CanonicalExpr::Var(v0), CanonicalExpr::Var(v1)]);
    let cand = CandidateSovereignLawAST {
        canonical_id: [77u8; 32],
        ast: clash_expr,
        dim: DimensionVector::from_integers(&[0, 1, 0]),
        cost: Cost::zero(),
        proof_trace: vec![],
        asymptotic_certificate: None,
        sovereignty_epoch: 1,
    };

    let target = AuditTarget::sovereign(cand);

    // في نمط SovereignGate، تصادم الأبعاد في القفل الثاني يقطع فوري
    let record = gatekeeper.evaluate(
        &target,
        GatekeeperMode::SovereignGate,
        DomainTag::ClassicalMechanics,
        DomainTag::ClassicalMechanics,
        &["EnergyConservation".to_string()],
        Some(&mut egraph),
    );

    // القفل الثاني قطع الفحص بسبب عدم التجانس
    assert_eq!(record.overall_status, EpistemicStatus::Refuted);
    assert!(!record.is_fully_sovereign());
}

#[test]
fn test_gatekeeper_dual_mode_diagnostic_vs_sovereign() {
    let gatekeeper = EpistemicGatekeeper::new();

    // إعداد فرضية بها عجز في البواقي (تفشل في القفل 1)
    let v0 = VariableId(0);
    let target = AuditTarget::ConstraintSystem {
        candidate_id: [55u8; 32],
        matrix: vec![vec![Rational::from_i64(2)]],
        rhs: vec![Rational::from_i64(5)], // 2 * x = 5
        solution: {
            let mut s = HashMap::new();
            s.insert(v0, Rational::from_i64(1)); // 2 * 1 = 2 != 5 (عجز)
            s
        },
        variables: vec![v0],
    };

    // 1. في نمط المجس التشخيصي (DiagnosticScanner): لا توقف مبكر، تُنفذ الأقفال الأربعة كاملة
    let diag_record = gatekeeper.evaluate(
        &target,
        GatekeeperMode::DiagnosticScanner,
        DomainTag::UniversalAbstract,
        DomainTag::UniversalAbstract,
        &["EnergyConservation".to_string()],
        None,
    );

    assert_eq!(diag_record.overall_status, EpistemicStatus::Uncertain);
    assert_eq!(diag_record.receipts.len(), 4);
    assert_eq!(diag_record.diagnostic_vector, Some([1, 0, 0, 0])); // عجز في القفل الأول فقط
    assert!(!diag_record.is_fully_sovereign());

    // 2. في نمط الحارس السيادي (SovereignGate): توقف فوري عند القفل الأول
    let sov_record = gatekeeper.evaluate(
        &target,
        GatekeeperMode::SovereignGate,
        DomainTag::UniversalAbstract,
        DomainTag::UniversalAbstract,
        &["EnergyConservation".to_string()],
        None,
    );

    assert_eq!(sov_record.overall_status, EpistemicStatus::Refuted);
    assert_eq!(sov_record.receipts.len(), 1); // قطع التنفيذ فوراً بعد القفل 1
    assert!(!sov_record.is_fully_sovereign());
}

#[test]
fn test_blake3_cryptographic_audit_hash_integrity() {
    let gatekeeper = EpistemicGatekeeper::new();
    let v0 = VariableId(0);

    let target = AuditTarget::ConstraintSystem {
        candidate_id: [99u8; 32],
        matrix: vec![vec![Rational::one()]],
        rhs: vec![Rational::one()],
        solution: {
            let mut s = HashMap::new();
            s.insert(v0, Rational::one());
            s
        },
        variables: vec![v0],
    };

    let record = gatekeeper.evaluate(
        &target,
        GatekeeperMode::SovereignGate,
        DomainTag::UniversalAbstract,
        DomainTag::UniversalAbstract,
        &["EnergyConservation".to_string()],
        None,
    );

    assert_eq!(record.overall_status, EpistemicStatus::Proven);
    // التحقق من حساب البصمة التشفيرية
    assert_ne!(record.audit_hash, [0u8; 32]);

    let recomputed_hash = aletheia_epistemic::EpistemicAuditRecord::compute_hash(
        &record.candidate_id,
        record.mode,
        record.overall_status,
        &record.receipts,
        &record.diagnostic_vector,
    );
    assert_eq!(record.audit_hash, recomputed_hash);
}
