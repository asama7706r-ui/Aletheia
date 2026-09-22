use aletheia_algebra::{CanonicalExpr, Rational, VariableId};
use aletheia_dna::{
    pareto_dominates, AletheiaDnaEngine, AntiUnifier, CompactionReport, DnaStorageEngine,
    OccamHypergraphExtractor, ParetoLawCandidate, ParetoSieve, PhysicalCompactor,
    UniversalRecordPrefix, RECORD_PREFIX_SIZE, RECORD_STATUS_TOMBSTONE,
};
use aletheia_epistemic::{
    DomainTag, LockReceipt, LockType, SovereignDnaPayload, SovereignReceipt,
};
use aletheia_lattice::DimensionVector;
use aletheia_rewriting::Cost;
use std::fs;
use std::path::PathBuf;

fn get_test_scratch_dir() -> PathBuf {
    let dir = std::env::temp_dir().join("aletheia_dna_8b_tests");
    let _ = fs::create_dir_all(&dir);
    dir
}

#[test]
fn test_pareto_cost_sieve_bi_objective_skyline() {
    let dummy_expr = CanonicalExpr::Var(VariableId(1));

    // مرشح A: كلفة MDL منخفضة (10) وانحراف تجريبي مرتفع (5/1)
    let cand_a = ParetoLawCandidate::new(
        "cand_A_simple_inaccurate",
        dummy_expr.clone(),
        Cost {
            size: 4,
            degree: 1,
            bit_complexity: 4,
            transcendental: 0,
        }, // 4 + 2*1 + 4 = 10
        Rational::new(5, 1).unwrap(),
        1,
        1,
    );

    // مرشح B: كلفة MDL مرتفعة (20) وانحراف تجريبي دقيق جداً (1/1)
    let cand_b = ParetoLawCandidate::new(
        "cand_B_complex_accurate",
        dummy_expr.clone(),
        Cost {
            size: 10,
            degree: 2,
            bit_complexity: 6,
            transcendental: 0,
        }, // 10 + 2*2 + 6 = 20
        Rational::new(1, 1).unwrap(),
        1,
        1,
    );

    // مرشح C: مهيمن عليه بالكامل من A و B (MDL = 25، Residual = 6)
    let cand_c = ParetoLawCandidate::new(
        "cand_C_dominated_by_both",
        dummy_expr.clone(),
        Cost {
            size: 15,
            degree: 2,
            bit_complexity: 6,
            transcendental: 0,
        }, // 15 + 4 + 6 = 25
        Rational::new(6, 1).unwrap(),
        1,
        1,
    );

    // مرشح D: مهيمن عليه من B (MDL = 22، Residual = 2)
    let cand_d = ParetoLawCandidate::new(
        "cand_D_dominated_by_B",
        dummy_expr,
        Cost {
            size: 12,
            degree: 2,
            bit_complexity: 6,
            transcendental: 0,
        }, // 12 + 4 + 6 = 22
        Rational::new(2, 1).unwrap(),
        1,
        1,
    );

    assert!(pareto_dominates(&cand_a, &cand_c));
    assert!(pareto_dominates(&cand_b, &cand_c));
    assert!(pareto_dominates(&cand_b, &cand_d));
    assert!(!pareto_dominates(&cand_a, &cand_b));
    assert!(!pareto_dominates(&cand_b, &cand_a));

    let candidates = vec![cand_a, cand_b, cand_c, cand_d];
    let frontier = ParetoSieve::extract_frontier(&candidates);

    // جبهة باريتو غير المهيمنة يجب أن تحتوي حصراً على A و B
    assert_eq!(frontier.len(), 2);
    let ids: Vec<&str> = frontier.iter().map(|c| c.candidate_id.as_str()).collect();
    assert!(ids.contains(&"cand_A_simple_inaccurate"));
    assert!(ids.contains(&"cand_B_complex_accurate"));

    // الترتيب وفق كلفة أوكام J = 1/2 * MDL + 1/2 * Res
    let alpha = Rational::new(1, 2).unwrap();
    let beta = Rational::new(1, 2).unwrap();
    let ranked = ParetoSieve::rank_frontier(&candidates, alpha, beta);

    assert_eq!(ranked.len(), 2);
    // كلفة A: 1/2 * 10 + 1/2 * 5 = 15/2 = 7.5
    // كلفة B: 1/2 * 20 + 1/2 * 1 = 21/2 = 10.5
    assert_eq!(ranked[0].0.candidate_id, "cand_A_simple_inaccurate");
    assert_eq!(ranked[0].1, Rational::new(15, 2).unwrap());
    assert_eq!(ranked[1].0.candidate_id, "cand_B_complex_accurate");
    assert_eq!(ranked[1].1, Rational::new(21, 2).unwrap());
}

#[test]
fn test_occam_hypergraph_minimal_proof_extractor() {
    let mut extractor = OccamHypergraphExtractor::new();

    // مسار 1: 1 -> 2 -> 3 (كلفة 5 + 5 = 10، اقتران 2 * 3 = 6)
    extractor.add_transition(
        1,
        2,
        "Newton_to_Euler",
        Rational::new(2, 1).unwrap(),
        Rational::new(5, 1).unwrap(),
    );
    extractor.add_transition(
        2,
        3,
        "Euler_to_Lagrange",
        Rational::new(3, 1).unwrap(),
        Rational::new(5, 1).unwrap(),
    );

    // مسار 2 بديل عالي الكلفة: 1 -> 4 -> 3 (كلفة 20 + 20 = 40، اقتران 10 * 1 = 10)
    extractor.add_transition(
        1,
        4,
        "Alternative_High_Cost_1",
        Rational::new(10, 1).unwrap(),
        Rational::new(20, 1).unwrap(),
    );
    extractor.add_transition(
        4,
        3,
        "Alternative_High_Cost_2",
        Rational::new(1, 1).unwrap(),
        Rational::new(20, 1).unwrap(),
    );

    let dag = extractor
        .extract_minimal_proof(1, 3)
        .expect("Minimal proof DAG must be found");

    assert_eq!(dag.source_class, 1);
    assert_eq!(dag.target_class, 3);
    assert_eq!(dag.steps.len(), 2);
    assert_eq!(dag.steps[0].rule_name, "Newton_to_Euler");
    assert_eq!(dag.steps[1].rule_name, "Euler_to_Lagrange");
    assert_eq!(dag.cumulative_coupling, Rational::new(6, 1).unwrap());
    assert_eq!(dag.total_cost, Rational::new(10, 1).unwrap());

    // التحقق من المسار العكسي التلقائي 3 -> 1
    let inv_dag = extractor
        .extract_minimal_proof(3, 1)
        .expect("Inverse proof DAG must be found");
    assert_eq!(inv_dag.steps.len(), 2);
    assert_eq!(inv_dag.cumulative_coupling, Rational::new(1, 6).unwrap());
    assert_eq!(inv_dag.total_cost, Rational::new(10, 1).unwrap());
}

#[test]
fn test_tombstone_physical_compaction_and_atomic_swap() {
    let test_dir = get_test_scratch_dir();
    let dna_path = test_dir.join("compaction_test_kernel.dna");
    let _ = fs::remove_file(&dna_path);

    // 1. إنشاء ملف DNA وحقن سجلات نشطة وشواهد قبور
    {
        let mut storage = DnaStorageEngine::open_or_create(&dna_path, 3).unwrap();

        // إلحاق سجل نشط 1: تعريف مجال
        let p_active1 = UniversalRecordPrefix::new_domain(1, 10, 100);
        let off1 = storage.header.offset_lineage as usize + storage.header.lineage_size as usize;
        storage.ensure_capacity(off1 + RECORD_PREFIX_SIZE).unwrap();
        storage.buffer_mut().unwrap()[off1..off1 + RECORD_PREFIX_SIZE]
            .copy_from_slice(&p_active1.to_bytes());
        storage.header.lineage_size += RECORD_PREFIX_SIZE as u32;

        // إلحاق سجل شاهد قبر 2: قانون مبطل (Tombstone)
        let mut p_tombstone = UniversalRecordPrefix::new_axiom(16, 1, 0x1234, 1);
        p_tombstone.status = RECORD_STATUS_TOMBSTONE;
        let off2 = storage.header.offset_lineage as usize + storage.header.lineage_size as usize;
        storage.ensure_capacity(off2 + RECORD_PREFIX_SIZE + 16).unwrap();
        storage.buffer_mut().unwrap()[off2..off2 + RECORD_PREFIX_SIZE]
            .copy_from_slice(&p_tombstone.to_bytes());
        storage.buffer_mut().unwrap()[off2 + RECORD_PREFIX_SIZE..off2 + RECORD_PREFIX_SIZE + 16]
            .copy_from_slice(b"DEAD_TOMBSTONE_1");
        storage.header.lineage_size += (RECORD_PREFIX_SIZE + 16) as u32;

        // إلحاق سجل نشط 3: جسر
        let payload3 = b"2:1";
        let crc3 = UniversalRecordPrefix::compute_crc(payload3);
        let p_active3 = UniversalRecordPrefix::new_bridge(1, 2, payload3.len() as u32, crc3);
        let off3 = storage.header.offset_lineage as usize + storage.header.lineage_size as usize;
        let l3 = RECORD_PREFIX_SIZE + payload3.len();
        storage.ensure_capacity(off3 + l3).unwrap();
        storage.buffer_mut().unwrap()[off3..off3 + RECORD_PREFIX_SIZE]
            .copy_from_slice(&p_active3.to_bytes());
        storage.buffer_mut().unwrap()[off3 + RECORD_PREFIX_SIZE..off3 + l3]
            .copy_from_slice(payload3);
        storage.header.lineage_size += l3 as u32;

        storage.flush().unwrap();
    }

    // 2. تشغيل محرك التطهير المادي
    let report: CompactionReport = PhysicalCompactor::compact_file(&dna_path)
        .expect("Physical compaction must succeed");

    assert_eq!(report.pruned_tombstone_records, 1);
    assert_eq!(report.remaining_active_records, 2);

    // 3. إعادة فتح الملف والتأكد من نقائه واحتوائه على راية FLAG_COMPACTED
    let compacted_storage = DnaStorageEngine::open_read_only(&dna_path)
        .expect("Reopening compacted file must succeed");
    assert!(compacted_storage.header.is_compacted());
    assert_eq!(
        compacted_storage.header.state_checksum,
        compacted_storage.header.compute_checksum()
    );
    assert_eq!(compacted_storage.header.total_axioms, 2);

    let _ = fs::remove_file(&dna_path);
}

#[test]
fn test_plotkin_anti_unification_gravity_coulomb_meta_theorem() {
    let r_var = CanonicalExpr::Var(VariableId(99)); // نصف القطر المشترك r
    let r_squared = CanonicalExpr::Pow(Box::new(r_var), 2);

    // 1. قانون نيوتن للجاذبية: F_g = (G * m1 * m2) / r^2
    let g_const = CanonicalExpr::Var(VariableId(10));
    let m1 = CanonicalExpr::Var(VariableId(11));
    let m2 = CanonicalExpr::Var(VariableId(12));
    let num_gravity = CanonicalExpr::Mul(vec![g_const.clone(), m1.clone(), m2.clone()]);
    let gravity_expr = CanonicalExpr::Div(Box::new(num_gravity), Box::new(r_squared.clone()));

    // 2. قانون كولوم للكهرباء الساكنة: F_e = (k_e * q1 * q2) / r^2
    let k_const = CanonicalExpr::Var(VariableId(20));
    let q1 = CanonicalExpr::Var(VariableId(21));
    let q2 = CanonicalExpr::Var(VariableId(22));
    let num_coulomb = CanonicalExpr::Mul(vec![k_const.clone(), q1.clone(), q2.clone()]);
    let coulomb_expr = CanonicalExpr::Div(Box::new(num_coulomb), Box::new(r_squared.clone()));

    // 3. استقراء النظرية الفوقية (Inverse Square Meta-Law)
    let meta = AntiUnifier::synthesize_meta_theorem(
        "universal_inverse_square_meta_law",
        "newton_gravity",
        1,
        &gravity_expr,
        "coulomb_electrostatics",
        2,
        &coulomb_expr,
    );

    assert_eq!(meta.meta_id, "universal_inverse_square_meta_law");
    assert_eq!(meta.source_laws.len(), 2);

    // الهيكل الناتج يجب أن يكون Div وبسطه Mul ومقامه Pow(r, 2)
    match &meta.generalized_expr {
        CanonicalExpr::Div(num, den) => {
            assert_eq!(**den, r_squared);
            match &**num {
                CanonicalExpr::Mul(args) => {
                    assert_eq!(args.len(), 3);
                    // المتغيرات الفوقية الثلاثة
                    let v0 = match &args[0] {
                        CanonicalExpr::Var(v) => *v,
                        _ => panic!("Expected generalized Var"),
                    };
                    let v1 = match &args[1] {
                        CanonicalExpr::Var(v) => *v,
                        _ => panic!("Expected generalized Var"),
                    };
                    let v2 = match &args[2] {
                        CanonicalExpr::Var(v) => *v,
                        _ => panic!("Expected generalized Var"),
                    };

                    // التحقق من تعيينات الإسقاط (Substitutions)
                    assert_eq!(meta.left_substitution.get(&v0), Some(&g_const));
                    assert_eq!(meta.left_substitution.get(&v1), Some(&m1));
                    assert_eq!(meta.left_substitution.get(&v2), Some(&m2));

                    assert_eq!(meta.right_substitution.get(&v0), Some(&k_const));
                    assert_eq!(meta.right_substitution.get(&v1), Some(&q1));
                    assert_eq!(meta.right_substitution.get(&v2), Some(&q2));
                }
                _ => panic!("Numerator must be Mul"),
            }
        }
        _ => panic!("Generalized expression must be Div"),
    }
}

#[test]
fn test_unified_aletheia_dna_engine_full_lifecycle() {
    let test_dir = get_test_scratch_dir();
    let dna_path = test_dir.join("unified_engine_kernel.dna");
    let _ = fs::remove_file(&dna_path);

    // 1. الإقلاع عبر المحرك الموحد
    let storage = DnaStorageEngine::open_or_create(&dna_path, 3).unwrap();
    let mut engine = AletheiaDnaEngine::new(storage);

    // 2. استيعاب صك سيادي من المحور السابع
    let dummy_receipt = SovereignReceipt::issue_active(
        "planck_quantum_action",
        [42u8; 32],
        CanonicalExpr::Var(VariableId(0)),
        DomainTag::QuantumMechanics,
        DimensionVector::from_integers(&[1, 2, -1, 0]),
        Cost {
            size: 5,
            degree: 1,
            bit_complexity: 10,
            transcendental: 0,
        },
        vec![[9u8; 32]],
        vec![LockReceipt::new(
            LockType::DimensionalLattice,
            "Dimensional Homogeneity",
            true,
            "Quenched",
            None,
        )],
        None,
        1,
        1000,
    );
    let payload = SovereignDnaPayload::package(vec![dummy_receipt], 1).unwrap();
    let count = engine.ingest_sovereign_payload(&payload).unwrap();
    assert_eq!(count, 1);

    // 3. زرع جسور فيزيائية ومسارات
    let bridge_class = engine
        .materialize_bridge(
            1,
            5,
            Rational::new(1054571817, 1000000000000000000).unwrap(), // hbar scale
            Rational::new(1, 1).unwrap(),
        )
        .unwrap();
    assert_eq!(bridge_class, 0);

    // 4. استخراج برهان أوكام
    let proof = engine
        .extract_proof(1, 5)
        .expect("Proof between domain 1 and 5 must exist");
    assert_eq!(proof.steps.len(), 1);

    // 5. غربال باريتو
    let candidates = vec![
        ParetoLawCandidate::new(
            "law_a",
            CanonicalExpr::Var(VariableId(1)),
            Cost {
                size: 2,
                degree: 1,
                bit_complexity: 4,
                transcendental: 0,
            },
            Rational::zero(),
            1,
            1,
        ),
        ParetoLawCandidate::new(
            "law_b",
            CanonicalExpr::Var(VariableId(2)),
            Cost {
                size: 8,
                degree: 2,
                bit_complexity: 16,
                transcendental: 0,
            },
            Rational::new(1, 2).unwrap(),
            1,
            1,
        ),
    ];
    let ranked = engine.sieve_pareto_candidates(
        &candidates,
        Rational::new(1, 2).unwrap(),
        Rational::new(1, 2).unwrap(),
    );
    assert_eq!(ranked.len(), 1); // law_a dominates law_b because size is smaller and residual is 0!
    assert_eq!(ranked[0].0.candidate_id, "law_a");

    // 6. التطهير المادي الشامل (Physical Compaction)
    let reloaded_engine = engine
        .compact_storage()
        .expect("Engine compaction and reload must succeed");
    assert!(reloaded_engine.evolution_engine.storage.header.is_compacted());

    let _ = fs::remove_file(&dna_path);
}
