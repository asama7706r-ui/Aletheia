use aletheia_algebra::{CanonicalExpr, Rational, VariableId};
use aletheia_epistemic::{
    AntiPtolemaicSieve, ArbitrationPath, BridgeRegistry, CandidateBridge, CandidateDimension,
    DimensionRegistry, DomainBridge, DomainTag, EpistemicArbitrator, LawDescriptor, LawStatus,
    MetaAdmissionProtocol, NoetherRegistry,
};
use aletheia_lattice::DimensionVector;
use aletheia_rewriting::Cost;
use aletheia_yoneda::AsymptoticLimitCertificate;
use std::collections::HashSet;

#[test]
fn test_meta_admission_candidate_bridge_functor_commutativity() {
    let mut registry = BridgeRegistry::new();

    // D1 (ClassicalMechanics) -> D2 (StatisticalMechanics) بمقياس 2/3 وبعد [1, 0, 0]
    let bridge_12 = DomainBridge::new(
        "Bridge_12",
        DomainTag::ClassicalMechanics,
        DomainTag::StatisticalMechanics,
        DimensionVector::from_integers(&[1, 0, 0]),
        Rational::new(2, 3).unwrap(),
    );
    registry.register_bridge(bridge_12);

    // D2 (StatisticalMechanics) -> D3 (Thermodynamics) بمقياس 9/4 وبعد [0, 1, 0]
    let bridge_23 = DomainBridge::new(
        "Bridge_23",
        DomainTag::StatisticalMechanics,
        DomainTag::Thermodynamics,
        DimensionVector::from_integers(&[0, 1, 0]),
        Rational::new(9, 4).unwrap(),
    );
    registry.register_bridge(bridge_23);

    // المسار المباشر D1 -> D3 يجب أن يكون بمقياس (2/3) * (9/4) = 3/2 وبعد [1, 1, 0]
    let valid_candidate = CandidateBridge::new(
        "Direct_Bridge_13_Valid",
        DomainTag::ClassicalMechanics,
        DomainTag::Thermodynamics,
        DimensionVector::from_integers(&[1, 1, 0]),
        Rational::new(3, 2).unwrap(),
    );

    // التدشين يجب أن ينجح لأن التوافق الفانكتوري متطابق بنسبة 100%
    let admitted = MetaAdmissionProtocol::admit_bridge(&registry, &valid_candidate, None, None, None);
    assert!(admitted.is_ok(), "Expected valid direct bridge to be admitted");

    // مرشح آخر بمقياس مخالف (مثلاً 5/2 بدلاً من 3/2)
    let invalid_candidate = CandidateBridge::new(
        "Direct_Bridge_13_Invalid_Scale",
        DomainTag::ClassicalMechanics,
        DomainTag::Thermodynamics,
        DimensionVector::from_integers(&[1, 1, 0]),
        Rational::new(5, 2).unwrap(),
    );

    let rejected = MetaAdmissionProtocol::admit_bridge(&registry, &invalid_candidate, None, None, None);
    assert!(
        rejected.is_err(),
        "Expected bridge with non-commuting scale to be rejected by Lock 3"
    );

    // مرشح بقناة اقتران متعامدة (بُعد مختلف [0, 0, 1]) بين نفس المجالين: يجب قبوله دون تعارض
    let orthogonal_candidate = CandidateBridge::new(
        "Direct_Bridge_13_Orthogonal_Channel",
        DomainTag::ClassicalMechanics,
        DomainTag::Thermodynamics,
        DimensionVector::from_integers(&[0, 0, 1]),
        Rational::new(7, 1).unwrap(),
    );

    let admitted_ortho = MetaAdmissionProtocol::admit_bridge(&registry, &orthogonal_candidate, None, None, None);
    assert!(
        admitted_ortho.is_ok(),
        "Expected orthogonal bridge channel with different dimension to be admitted"
    );
}

#[test]
fn test_meta_admission_candidate_dimension_linear_independence() {
    let mut dim_reg = DimensionRegistry::standard_si();
    assert_eq!(dim_reg.basis.len(), 7);

    // 1. تجربة بُعد مشتق وغير مستقل خطياً (مثلاً حاصل ضرب السرعة والتسارع [2, 0, -3, 0, 0, 0, 0])
    let dependent_vec = DimensionVector::from_integers(&[2, 0, -3, 0, 0, 0, 0]);
    assert!(
        !dim_reg.is_linearly_independent(&dependent_vec),
        "Dependent vector should be recognized as linearly dependent"
    );

    let dependent_cand = CandidateDimension::new("KinematicComposite", "m2_s3", dependent_vec);
    let adm_res = MetaAdmissionProtocol::admit_dimension(&mut dim_reg, &dependent_cand);
    assert!(
        adm_res.is_err(),
        "Linearly dependent dimension must be rejected"
    );

    // 2. تجربة بُعد جديد مستقل خطياً يشغل الإحداثي الثامن e_8
    let independent_vec = DimensionVector::unit_basis(7, 8);
    assert!(
        dim_reg.is_linearly_independent(&independent_vec),
        "Novel orthogonal basis vector must be recognized as independent"
    );

    let independent_cand = CandidateDimension::new("InformationEntropy", "nat", independent_vec);
    let new_idx = MetaAdmissionProtocol::admit_dimension(&mut dim_reg, &independent_cand)
        .expect("Linearly independent dimension must be admitted");

    assert_eq!(new_idx, 7);
    assert_eq!(dim_reg.basis.len(), 8);
    assert_eq!(dim_reg.dimensions[7].0, "InformationEntropy");
}

#[test]
fn test_arbitration_path1_subsumption_einstein_newton() {
    let mut arbitrator = EpistemicArbitrator::new();

    let newton_law = LawDescriptor::new(
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
    arbitrator.register_law("newton_mechanics", LawStatus::ActiveAxiom);

    let einstein_law = LawDescriptor::new(
        "einstein_relativity",
        "Special Relativity Energy-Momentum",
        CanonicalExpr::Var(VariableId(1)),
        DomainTag::Relativity,
        DimensionVector::from_integers(&[1, 1, -2]),
        Rational::zero(),
        Cost {
            size: 15,
            degree: 2,
            bit_complexity: 32,
            transcendental: 1,
        },
        HashSet::from(["LorentzInvariance".into(), "EnergyConservation".into()]),
    );

    // شهادة انكماش معتمدة من المحور الخامس (v/c -> 0)
    let cert = AsymptoticLimitCertificate::issue(
        [1u8; 32],
        "v/c",
        Rational::zero(),
        vec![Rational::one()],
        vec![Rational::one()],
        Some(3),
        true, // is_smooth_reduction
        true, // jacobi_verified
        vec!["Inönü-Wigner contraction from so(3,1) to iso(3)".into()],
        1,
    );

    let verdict = arbitrator
        .adjudicate(&newton_law, &einstein_law, Some(&cert))
        .expect("Adjudication should succeed");

    assert_eq!(verdict.path, ArbitrationPath::Subsumption);
    assert_eq!(verdict.new_status_victorious, Some(LawStatus::ActiveAxiom));
    assert_eq!(verdict.new_status_demoted, Some(LawStatus::ConditionalLimit));
    assert!(verdict.retracted_dependencies.is_empty());

    // التحقق من تحديث السجل الداخلي للمحكم
    assert_eq!(
        arbitrator.get_status("einstein_relativity"),
        Some(LawStatus::ActiveAxiom)
    );
    assert_eq!(
        arbitrator.get_status("newton_mechanics"),
        Some(LawStatus::ConditionalLimit)
    );
}

#[test]
fn test_arbitration_path2_neutrino_deficit_routing() {
    let mut arbitrator = EpistemicArbitrator::new();

    // قانونان في نفس المجال (QuantumMechanics) مع عجز أو درجات حرية غير مصفّرة dof > 0
    let beta_decay_old = LawDescriptor::new(
        "beta_decay_continuous",
        "Continuous Beta Spectrum (Pre-Neutrino)",
        CanonicalExpr::Var(VariableId(0)),
        DomainTag::QuantumMechanics,
        DimensionVector::from_integers(&[2, 1, -2]),
        Rational::new(1, 2).unwrap(), // dof = 1/2 unquenched deficit
        Cost {
            size: 8,
            degree: 1,
            bit_complexity: 12,
            transcendental: 0,
        },
        HashSet::from(["EnergyConservation".into()]),
    );

    let beta_decay_cand = LawDescriptor::new(
        "beta_decay_candidate",
        "Two-body Fermi Proposal",
        CanonicalExpr::Var(VariableId(1)),
        DomainTag::QuantumMechanics,
        DimensionVector::from_integers(&[2, 1, -2]),
        Rational::new(1, 2).unwrap(),
        Cost {
            size: 10,
            degree: 1,
            bit_complexity: 16,
            transcendental: 0,
        },
        HashSet::from(["EnergyConservation".into()]),
    );

    let verdict = arbitrator
        .adjudicate(&beta_decay_old, &beta_decay_cand, None)
        .expect("Adjudication should succeed");

    assert_eq!(verdict.path, ArbitrationPath::NeutrinoDeficit);
    assert!(verdict.victorious_law.is_none());
    assert!(verdict.demoted_law.is_none());
    assert!(verdict.reconciled_variable.is_some());
    let hidden = verdict.reconciled_variable.unwrap();
    assert!(hidden.contains("psi_hidden_beta_decay_continuous_beta_decay_candidate"));
}

#[test]
fn test_arbitration_path3_domain_demarcation_boundary() {
    let mut arbitrator = EpistemicArbitrator::new();

    let quantum_law = LawDescriptor::new(
        "schrodinger_eq",
        "Schrodinger Equation",
        CanonicalExpr::Var(VariableId(0)),
        DomainTag::QuantumMechanics,
        DimensionVector::from_integers(&[2, 1, -1]),
        Rational::zero(),
        Cost {
            size: 12,
            degree: 2,
            bit_complexity: 24,
            transcendental: 0,
        },
        HashSet::from(["EnergyConservation".into()]),
    );

    let thermo_law = LawDescriptor::new(
        "carnot_efficiency",
        "Carnot Cycle Principle",
        CanonicalExpr::Var(VariableId(1)),
        DomainTag::Thermodynamics,
        DimensionVector::dimensionless(),
        Rational::zero(),
        Cost {
            size: 6,
            degree: 1,
            bit_complexity: 10,
            transcendental: 0,
        },
        HashSet::new(),
    );

    let verdict = arbitrator
        .adjudicate(&thermo_law, &quantum_law, None)
        .expect("Adjudication should succeed");

    assert_eq!(verdict.path, ArbitrationPath::DomainDemarcation);
    assert_eq!(
        verdict.new_status_victorious,
        Some(LawStatus::DemarcatedBoundary)
    );
    assert_eq!(
        verdict.new_status_demoted,
        Some(LawStatus::DemarcatedBoundary)
    );
    assert!(verdict.retracted_dependencies.is_empty());

    assert_eq!(
        arbitrator.get_status("schrodinger_eq"),
        Some(LawStatus::DemarcatedBoundary)
    );
    assert_eq!(
        arbitrator.get_status("carnot_efficiency"),
        Some(LawStatus::DemarcatedBoundary)
    );
}

#[test]
fn test_arbitration_path4_paradigm_overthrow_and_transitive_retraction() {
    let mut arbitrator = EpistemicArbitrator::new();

    // القانون القديم: نظرية الفلوجستون مع تكلفة عالية
    let phlogiston = LawDescriptor::new(
        "phlogiston_combustion",
        "Phlogiston Escape Principle",
        CanonicalExpr::Var(VariableId(0)),
        DomainTag::ClassicalMechanics,
        DimensionVector::from_integers(&[1, 1, -2]),
        Rational::zero(),
        Cost {
            size: 80,
            degree: 4,
            bit_complexity: 150,
            transcendental: 2,
        },
        HashSet::new(),
    );
    arbitrator.register_law("phlogiston_combustion", LawStatus::ActiveAxiom);

    // تسجيل اعتماديات متسلسلة مشتقة من الفلوجستون:
    // phlogiston_combustion -> caloric_expansion_lemma -> dephlogisticated_air_corollary
    arbitrator.register_dependency("phlogiston_combustion", "caloric_expansion_lemma");
    arbitrator.register_dependency("caloric_expansion_lemma", "dephlogisticated_air_corollary");
    arbitrator.register_law("caloric_expansion_lemma", LawStatus::ActiveAxiom);
    arbitrator.register_law("dephlogisticated_air_corollary", LawStatus::ActiveAxiom);

    // القانون المرشح الجديد: أكسدة لافوازييه بتكلفة أبسط بكثير وفق نصل أوكام (MDL)
    let lavoisier_oxygen = LawDescriptor::new(
        "lavoisier_oxidation",
        "Oxygen Oxidation Law",
        CanonicalExpr::Var(VariableId(1)),
        DomainTag::ClassicalMechanics,
        DimensionVector::from_integers(&[1, 1, -2]),
        Rational::zero(),
        Cost {
            size: 15,
            degree: 1,
            bit_complexity: 25,
            transcendental: 0,
        },
        HashSet::from(["MassConservation".into()]),
    );

    let verdict = arbitrator
        .adjudicate(&phlogiston, &lavoisier_oxygen, None)
        .expect("Adjudication should succeed");

    assert_eq!(verdict.path, ArbitrationPath::Overthrow);
    assert_eq!(verdict.new_status_victorious, Some(LawStatus::ActiveAxiom));
    assert_eq!(verdict.new_status_demoted, Some(LawStatus::Overthrown));

    // التحقق من التراجع المتتالي لكافة النظريات المشتقة متعدياً
    assert_eq!(verdict.retracted_dependencies.len(), 2);
    assert!(verdict.retracted_dependencies.contains(&"caloric_expansion_lemma".to_string()));
    assert!(verdict.retracted_dependencies.contains(&"dephlogisticated_air_corollary".to_string()));

    // التحقق من تحديث حالات القوانين في المحكم إلى Overthrown
    assert_eq!(
        arbitrator.get_status("phlogiston_combustion"),
        Some(LawStatus::Overthrown)
    );
    assert_eq!(
        arbitrator.get_status("caloric_expansion_lemma"),
        Some(LawStatus::Overthrown)
    );
    assert_eq!(
        arbitrator.get_status("dephlogisticated_air_corollary"),
        Some(LawStatus::Overthrown)
    );
    assert_eq!(
        arbitrator.get_status("lavoisier_oxidation"),
        Some(LawStatus::ActiveAxiom)
    );
}

#[test]
fn test_arbitration_path5_dual_suspension_epoche() {
    let mut arbitrator = EpistemicArbitrator::new();

    // فرضيتان متنافستان في نفس المجال بنفس التكلفة تماماً دون تفوق لأحدهما
    let model_a = LawDescriptor::new(
        "cosmic_inflation_a",
        "Starobinsky Inflation Variant",
        CanonicalExpr::Var(VariableId(0)),
        DomainTag::Cosmology,
        DimensionVector::dimensionless(),
        Rational::zero(),
        Cost {
            size: 20,
            degree: 2,
            bit_complexity: 40,
            transcendental: 1,
        },
        HashSet::new(),
    );

    let model_b = LawDescriptor::new(
        "cosmic_inflation_b",
        "Higgs Inflation Variant",
        CanonicalExpr::Var(VariableId(1)),
        DomainTag::Cosmology,
        DimensionVector::dimensionless(),
        Rational::zero(),
        Cost {
            size: 20,
            degree: 2,
            bit_complexity: 40,
            transcendental: 1,
        },
        HashSet::new(),
    );

    let verdict = arbitrator
        .adjudicate(&model_a, &model_b, None)
        .expect("Adjudication should succeed");

    assert_eq!(verdict.path, ArbitrationPath::DualSuspension);
    assert_eq!(
        verdict.new_status_victorious,
        Some(LawStatus::QuarantinedEpoche)
    );
    assert_eq!(
        verdict.new_status_demoted,
        Some(LawStatus::QuarantinedEpoche)
    );

    assert_eq!(
        arbitrator.get_status("cosmic_inflation_a"),
        Some(LawStatus::QuarantinedEpoche)
    );
    assert_eq!(
        arbitrator.get_status("cosmic_inflation_b"),
        Some(LawStatus::QuarantinedEpoche)
    );
}

#[test]
fn test_anti_ptolemaic_sieve_rejects_free_parameters_and_noether_violation() {
    let registry = NoetherRegistry::standard_physics();

    // 1. فحص رفض درجات الحرية الموجبة
    let dof_positive = Rational::new(1, 3).unwrap();
    let dof_err = AntiPtolemaicSieve::verify_dof_quenched(&dof_positive);
    assert!(dof_err.is_err(), "Non-zero dof must be rejected");

    let dof_zero = Rational::zero();
    assert!(AntiPtolemaicSieve::verify_dof_quenched(&dof_zero).is_ok());

    // 2. فحص تناظرات نويثر
    let valid_invs = vec!["EnergyConservation".to_string(), "CPTSymmetry".to_string()];
    assert!(AntiPtolemaicSieve::verify_noether_invariants(&valid_invs, &registry).is_ok());

    let invalid_invs = vec!["NonExistentArbitraryGaugeSymmetry".to_string()];
    assert!(AntiPtolemaicSieve::verify_noether_invariants(&invalid_invs, &registry).is_err());

    // 3. التقييم الشامل
    let candidate_cost = Cost {
        size: 10,
        degree: 1,
        bit_complexity: 20,
        transcendental: 0,
    };
    let existing_cost = Cost {
        size: 25,
        degree: 2,
        bit_complexity: 50,
        transcendental: 0,
    };

    let eval = AntiPtolemaicSieve::evaluate_candidate(
        &dof_zero,
        &candidate_cost,
        &valid_invs,
        Some(&existing_cost),
        &registry,
    )
    .expect("Evaluation should succeed");

    assert!(eval.dof_zero);
    assert!(eval.noether_compliant);
    assert!(eval.occam_superior);
}
