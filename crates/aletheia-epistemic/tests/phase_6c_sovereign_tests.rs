use aletheia_algebra::{CanonicalExpr, Rational, VariableId};
use aletheia_egraph::TransactionalEGraph;
use aletheia_epistemic::{
    DNA_MAGIC_HEADER, DomainTag, EGraphPurgeEngine,
    EpistemicSovereigntyEngine, LawDescriptor, LawStatus, LockReceipt, LockType,
    SovereignDnaPayload, SovereignReceipt, SovereigntyOutcome,
};
use aletheia_lattice::DimensionVector;
use aletheia_rewriting::Cost;
use aletheia_yoneda::{AsymptoticLimitCertificate, CandidateSovereignLawAST};
use std::collections::HashSet;

#[test]
fn test_sovereign_receipt_issuance_and_blake3_merkle_chain() {
    let law_id = "maxwell_ampere_extended";
    let canonical_id = [42u8; 32];
    let ast = CanonicalExpr::Var(VariableId(0));
    let domain = DomainTag::Electromagnetism;
    let dimension = DimensionVector::from_integers(&[1, 1, -2, -1]);
    let cost = Cost {
        size: 10,
        degree: 1,
        bit_complexity: 20,
        transcendental: 0,
    };
    let proof_chain = vec![[1u8; 32], [2u8; 32], [3u8; 32]];
    let lock_receipts = vec![
        LockReceipt::new(LockType::ResidualSieve, "Residual", true, "Residual zero", None),
        LockReceipt::new(LockType::DimensionalLattice, "Dimensional", true, "Homogeneous", None),
        LockReceipt::new(LockType::DomainIsolationBridge, "Bridge", true, "Domain isolated", None),
        LockReceipt::new(LockType::OntologicalAnchor, "Anchor", true, "Gedankenexperiment passed", None),
    ];

    // 1. إصدار صك سيادي لبديهية نشطة
    let active_receipt = SovereignReceipt::issue_active(
        law_id,
        canonical_id,
        ast.clone(),
        domain,
        dimension.clone(),
        cost,
        proof_chain.clone(),
        lock_receipts.clone(),
        None,
        1,
        1000,
    );

    assert_eq!(active_receipt.status, LawStatus::ActiveAxiom);
    assert!(active_receipt.validity_regime.is_none());
    assert!(active_receipt.parent_law_id.is_none());

    // التحقق من أن بصمة الصك مطابقة لإعادة الحوسبة
    let expected_hash = SovereignReceipt::compute_receipt_id(
        law_id,
        &canonical_id,
        LawStatus::ActiveAxiom,
        None,
        None,
        domain,
        &dimension,
        &cost,
        &proof_chain,
        None,
        1,
        1000,
    );
    assert_eq!(active_receipt.receipt_id, expected_hash);

    // 2. إصدار صك سيادي لقانون مخفض كحالة حدية تقاربية
    let conditional_receipt = SovereignReceipt::issue_conditional_limit(
        "coulomb_electrostatics",
        [99u8; 32],
        ast,
        domain,
        dimension.clone(),
        cost,
        "v << c (Static Regime)",
        "maxwell_ampere_extended",
        proof_chain,
        lock_receipts,
        Some([77u8; 32]),
        1,
        1001,
    );

    assert_eq!(conditional_receipt.status, LawStatus::ConditionalLimit);
    assert_eq!(
        conditional_receipt.validity_regime.as_deref(),
        Some("v << c (Static Regime)")
    );
    assert_eq!(
        conditional_receipt.parent_law_id.as_deref(),
        Some("maxwell_ampere_extended")
    );
    assert_eq!(conditional_receipt.asymptotic_reduction, Some([77u8; 32]));
}

#[test]
fn test_cascade_purge_invalidates_overthrown_rules_and_cleans_egraph() {
    let mut purge_engine = EGraphPurgeEngine::new();

    // ربط قواعد بالقانون القديم "phlogiston_theory"
    purge_engine.register_law_rule("phlogiston_theory", "rule_phlogiston_release");
    purge_engine.register_law_rule("phlogiston_theory", "rule_calcination_weight_loss");

    // ربط قواعد بنظرية مشتقة "caloric_fluid_theorem"
    purge_engine.register_law_rule("caloric_fluid_theorem", "rule_heat_substance_flow");

    // ربط قاعدة بقانون مستقل غير متأثر
    purge_engine.register_law_rule("newton_gravity", "rule_inverse_square");

    assert!(purge_engine.is_rule_active("rule_phlogiston_release"));
    assert!(purge_engine.is_rule_active("rule_calcination_weight_loss"));
    assert!(purge_engine.is_rule_active("rule_heat_substance_flow"));
    assert!(purge_engine.is_rule_active("rule_inverse_square"));
    assert_eq!(purge_engine.get_active_rules().len(), 4);

    // تنفيذ التطهير المتتالي عند خلع نظرية الفلوجستون لصالح أكسدة لافوازييه
    let invalidated = purge_engine.purge_hierarchy(
        "phlogiston_theory",
        &["caloric_fluid_theorem".to_string()],
        "lavoisier_oxygen_combustion",
        "Overthrown by Occam MDL simplicity in combustion chemistry",
        5,
    );

    // التحقق من إبطال القواعد التابعة وشطبها من القواعد النشطة
    assert_eq!(invalidated.len(), 3);
    assert!(!purge_engine.is_rule_active("rule_phlogiston_release"));
    assert!(!purge_engine.is_rule_active("rule_calcination_weight_loss"));
    assert!(!purge_engine.is_rule_active("rule_heat_substance_flow"));

    // القاعدة المستقلة يجب أن تظل نشطة 100%
    assert!(purge_engine.is_rule_active("rule_inverse_square"));
    assert_eq!(purge_engine.get_active_rules().len(), 1);

    // التحقق من أرشيف السحب التاريخي
    assert_eq!(purge_engine.retraction_archive.len(), 2);
    assert_eq!(purge_engine.retraction_archive[0].law_id, "phlogiston_theory");
    assert_eq!(purge_engine.retraction_archive[1].law_id, "caloric_fluid_theorem");

    // اختبار إعادة بناء E-Graph نظيف
    let clean_receipt = SovereignReceipt::issue_active(
        "lavoisier_oxygen",
        [12u8; 32],
        CanonicalExpr::Var(VariableId(5)),
        DomainTag::ClassicalMechanics,
        DimensionVector::dimensionless(),
        Cost::default(),
        vec![],
        vec![],
        None,
        5,
        2000,
    );

    let clean_egraph = EGraphPurgeEngine::rebuild_clean_egraph(&[&clean_receipt]);
    assert!(clean_egraph.is_ok(), "Clean E-Graph rebuild should succeed");
}

#[test]
fn test_dna_payload_serialization_magic_header_and_tamper_detection() {
    let r1 = SovereignReceipt::issue_active(
        "einstein_field_equations",
        [101u8; 32],
        CanonicalExpr::Var(VariableId(1)),
        DomainTag::Relativity,
        DimensionVector::from_integers(&[1, -1, -2]),
        Cost {
            size: 20,
            degree: 2,
            bit_complexity: 40,
            transcendental: 1,
        },
        vec![[1u8; 32], [2u8; 32]],
        vec![],
        None,
        2,
        3000,
    );

    let r2 = SovereignReceipt::issue_conditional_limit(
        "newton_universal_gravitation",
        [102u8; 32],
        CanonicalExpr::Var(VariableId(2)),
        DomainTag::ClassicalMechanics,
        DimensionVector::from_integers(&[1, -1, -2]),
        Cost {
            size: 5,
            degree: 1,
            bit_complexity: 10,
            transcendental: 0,
        },
        "v/c << 1 and weak gravitational field",
        "einstein_field_equations",
        vec![[3u8; 32]],
        vec![],
        Some([88u8; 32]),
        2,
        3001,
    );

    let payload = SovereignDnaPayload::package(vec![r1.clone(), r2.clone()], 2)
        .expect("Payload packaging should succeed");

    // 1. التسلسل إلى بايتات خام
    let bytes = payload.to_bytes().expect("Serialization to bytes must succeed");

    // التحقق من الترويسة السحرية في البداية (8 بايت)
    assert_eq!(&bytes[0..8], DNA_MAGIC_HEADER);

    // 2. استرجاع الجينوم وفك التسلسل مع التحقق من جذر ميركل
    let recovered = SovereignDnaPayload::from_bytes(&bytes)
        .expect("Deserialization and Merkle validation must succeed");

    assert_eq!(recovered.version, payload.version);
    assert_eq!(recovered.epoch, payload.epoch);
    assert_eq!(recovered.genome_merkle_root, payload.genome_merkle_root);
    assert_eq!(recovered.sovereign_receipts.len(), 2);
    assert_eq!(recovered.sovereign_receipts[0].law_id, "einstein_field_equations");
    assert_eq!(recovered.sovereign_receipts[1].law_id, "newton_universal_gravitation");
    assert_eq!(
        recovered.sovereign_receipts[1].validity_regime.as_deref(),
        Some("v/c << 1 and weak gravitational field")
    );

    // 3. فحص كشف التلاعب (Tamper Detection)
    // التلاعب ببايت واحد في منتصف البايتات المشفرة
    let mut corrupted_bytes = bytes.clone();
    let corrupt_idx = corrupted_bytes.len() - 10;
    corrupted_bytes[corrupt_idx] ^= 0xFF; // قلب البتات

    let tamper_res = SovereignDnaPayload::from_bytes(&corrupted_bytes);
    assert!(
        tamper_res.is_err(),
        "Tampered genome bytes must be rejected by Merkle root integrity check"
    );
}

#[test]
fn test_integrated_sovereignty_engine_subsumption_pipeline() {
    let mut engine = EpistemicSovereigntyEngine::new();

    // تسجيل قانون نيوتن مسبقاً في المحرك كبديهية نشطة
    let newton_receipt = SovereignReceipt::issue_active(
        "newton_mechanics",
        [1u8; 32],
        CanonicalExpr::Var(VariableId(0)),
        DomainTag::ClassicalMechanics,
        DimensionVector::from_integers(&[1, 1, -2]),
        Cost {
            size: 5,
            degree: 1,
            bit_complexity: 8,
            transcendental: 0,
        },
        vec![],
        vec![],
        None,
        1,
        500,
    );
    engine.arbitrator.register_law("newton_mechanics", LawStatus::ActiveAxiom);
    engine.sovereign_receipts.insert("newton_mechanics".to_string(), newton_receipt);

    // مرشح أينشتاين القادم من الحجر الصحي مع شهادة انكماش معتمدة
    let cert = AsymptoticLimitCertificate::issue(
        [99u8; 32],
        "v/c",
        Rational::zero(),
        vec![Rational::one()],
        vec![Rational::one()],
        Some(3),
        true, // smooth
        true, // jacobi
        vec!["Inönü-Wigner Lie algebra contraction".into()],
        1,
    );

    let einstein_candidate = CandidateSovereignLawAST {
        canonical_id: [2u8; 32],
        ast: CanonicalExpr::Var(VariableId(1)),
        dim: DimensionVector::from_integers(&[1, 1, -2]),
        cost: Cost {
            size: 15,
            degree: 2,
            bit_complexity: 32,
            transcendental: 1,
        },
        proof_trace: vec!["Relativistic invariance proven".into()],
        asymptotic_certificate: Some(cert),
        sovereignty_epoch: 1,
    };

    let competing_desc = LawDescriptor::new(
        "newton_mechanics",
        "Newton's Second Law",
        CanonicalExpr::Var(VariableId(0)),
        DomainTag::ClassicalMechanics,
        DimensionVector::from_integers(&[1, 1, -2]),
        Rational::zero(),
        Cost {
            size: 5,
            degree: 1,
            bit_complexity: 8,
            transcendental: 0,
        },
        HashSet::from(["LinearMomentumConservation".into()]),
    );

    // محاكاة تجربة فكرية في الـ E-Graph
    let mut egraph = TransactionalEGraph::new();

    let outcome = engine
        .evaluate_and_crown_law(
            einstein_candidate,
            DomainTag::Relativity,
            &["LinearMomentumConservation".to_string()],
            Some(&competing_desc),
            Some(&mut egraph),
        )
        .expect("Subsumption pipeline should succeed");

    match outcome {
        SovereigntyOutcome::SubsumptionVictorious(einstein_rcpt) => {
            assert_eq!(einstein_rcpt.status, LawStatus::ActiveAxiom);
            // التحقق من خفض رتبة قانون نيوتن في سجل الصكوك
            let old_rcpt = engine.sovereign_receipts.get("newton_mechanics").unwrap();
            assert_eq!(old_rcpt.status, LawStatus::ConditionalLimit);
            assert!(old_rcpt.validity_regime.is_some());
            assert_eq!(old_rcpt.parent_law_id.as_deref(), Some(einstein_rcpt.law_id.as_str()));
        }
        _ => panic!("Expected SubsumptionVictorious outcome"),
    }

    // تصدير الجينوم والتأكد من احتوائه على الصكين
    let dna_payload = engine.export_dna_payload().expect("DNA export should succeed");
    assert_eq!(dna_payload.sovereign_receipts.len(), 2);
}

#[test]
fn test_integrated_sovereignty_engine_overthrow_cascade_pipeline() {
    let mut engine = EpistemicSovereigntyEngine::new();

    // تسجيل الفلوجستون مع قواعد في محرك التطهير
    engine.purge_engine.register_law_rule("phlogiston_core", "rule_phlog_1");
    engine.purge_engine.register_law_rule("phlogiston_lemma_combust", "rule_phlog_2");
    engine.arbitrator.register_dependency("phlogiston_core", "phlogiston_lemma_combust");
    engine.arbitrator.register_law("phlogiston_core", LawStatus::ActiveAxiom);
    engine.arbitrator.register_law("phlogiston_lemma_combust", LawStatus::ActiveAxiom);

    let phlog_receipt = SovereignReceipt::issue_active(
        "phlogiston_core",
        [55u8; 32],
        CanonicalExpr::Var(VariableId(0)),
        DomainTag::ClassicalMechanics,
        DimensionVector::from_integers(&[1, 1, -2]),
        Cost {
            size: 60,
            degree: 3,
            bit_complexity: 100,
            transcendental: 2,
        },
        vec![],
        vec![],
        None,
        1,
        100,
    );
    engine.sovereign_receipts.insert("phlogiston_core".to_string(), phlog_receipt);

    // مرشح لافوازييه للأكسدة بتكلفة أقل بنصل أوكام
    let lavoisier_candidate = CandidateSovereignLawAST {
        canonical_id: [77u8; 32],
        ast: CanonicalExpr::Var(VariableId(1)),
        dim: DimensionVector::from_integers(&[1, 1, -2]),
        cost: Cost {
            size: 12,
            degree: 1,
            bit_complexity: 20,
            transcendental: 0,
        },
        proof_trace: vec!["Mass conservation confirmed in combustion".into()],
        asymptotic_certificate: None,
        sovereignty_epoch: 2,
    };

    let competing_phlog = LawDescriptor::new(
        "phlogiston_core",
        "Phlogiston Escape Theory",
        CanonicalExpr::Var(VariableId(0)),
        DomainTag::ClassicalMechanics,
        DimensionVector::from_integers(&[1, 1, -2]),
        Rational::zero(),
        Cost {
            size: 60,
            degree: 3,
            bit_complexity: 100,
            transcendental: 2,
        },
        HashSet::from(["EnergyConservation".into()]),
    );

    let outcome = engine
        .evaluate_and_crown_law(
            lavoisier_candidate,
            DomainTag::ClassicalMechanics,
            &["EnergyConservation".to_string()],
            Some(&competing_phlog),
            None,
        )
        .expect("Overthrow pipeline should succeed");

    match outcome {
        SovereigntyOutcome::OverthrowVictorious(new_rcpt, retracted_laws) => {
            assert_eq!(new_rcpt.status, LawStatus::ActiveAxiom);
            assert!(retracted_laws.contains(&"rule_phlog_1".to_string()));
            assert!(retracted_laws.contains(&"rule_phlog_2".to_string()));

            // تأكيد سحب الفلوجستون من السجل النشط
            assert!(!engine.sovereign_receipts.contains_key("phlogiston_core"));
            assert!(engine.sovereign_receipts.contains_key(&new_rcpt.law_id));

            // تأكيد إلغاء تنشيط القواعد في محرك التطهير
            assert!(!engine.purge_engine.is_rule_active("rule_phlog_1"));
            assert!(!engine.purge_engine.is_rule_active("rule_phlog_2"));
        }
        _ => panic!("Expected OverthrowVictorious outcome"),
    }
}

#[test]
fn test_sovereignty_engine_rejects_unquenched_or_disputed_candidates() {
    let mut engine = EpistemicSovereigntyEngine::new();

    // 1. مرشح يشير إلى تناظر غير معتمد رسمياً في نويثر
    let bad_cand = CandidateSovereignLawAST {
        canonical_id: [123u8; 32],
        ast: CanonicalExpr::Var(VariableId(0)),
        dim: DimensionVector::dimensionless(),
        cost: Cost::default(),
        proof_trace: vec![],
        asymptotic_certificate: None,
        sovereignty_epoch: 1,
    };

    let uncertified_inv = vec!["ImaginaryDarkEnergySymmetry".to_string()];
    let res = engine.evaluate_and_crown_law(
        bad_cand,
        DomainTag::Cosmology,
        &uncertified_inv,
        None,
        None,
    );
    assert!(res.is_err(), "Uncertified Noether invariant must be rejected");

    // 2. فرضيتان متكافئتان دون حسم بأوكام => تفعيل الإبوخيه والتعليق
    let cand_a = CandidateSovereignLawAST {
        canonical_id: [201u8; 32],
        ast: CanonicalExpr::Var(VariableId(1)),
        dim: DimensionVector::dimensionless(),
        cost: Cost {
            size: 25,
            degree: 2,
            bit_complexity: 50,
            transcendental: 1,
        },
        proof_trace: vec![],
        asymptotic_certificate: None,
        sovereignty_epoch: 1,
    };

    let competing_same_cost = LawDescriptor::new(
        "model_b",
        "Competitor Model B",
        CanonicalExpr::Var(VariableId(2)),
        DomainTag::Cosmology,
        DimensionVector::dimensionless(),
        Rational::zero(),
        Cost {
            size: 25,
            degree: 2,
            bit_complexity: 50,
            transcendental: 1,
        },
        HashSet::new(),
    );

    let dispute_outcome = engine
        .evaluate_and_crown_law(
            cand_a,
            DomainTag::Cosmology,
            &[],
            Some(&competing_same_cost),
            None,
        )
        .expect("Evaluation should succeed with quarantine outcome");

    assert_eq!(dispute_outcome, SovereigntyOutcome::DualSuspensionQuarantined);
}
