use aletheia_algebra::{CanonicalExpr, Rational, VariableId};
use aletheia_core::{AletheiaRuntime, DimensionVector};
use std::fs;

#[test]
fn test_idempotent_ingestion_and_quarantine_eviction_on_persistent_dna() {
    let temp_dir = std::env::temp_dir();
    let dna_path = temp_dir.join(format!("test_idempotent_kernel_{}.dna", std::process::id()));
    if dna_path.exists() {
        let _ = fs::remove_file(&dna_path);
    }
    let q_path = dna_path.with_extension("quarantine.bin");
    if q_path.exists() {
        let _ = fs::remove_file(&q_path);
    }

    // 1. Initial boot with fresh persistent DNA file at rank 7
    {
        let mut runtime = AletheiaRuntime::boot_or_create(Some(&dna_path), 7).expect("Boot runtime");
        assert_eq!(runtime.dna_engine.evolution_engine.storage.header.total_axioms, 0);

        // Define two incomplete laws that require a coupling carrier (Planck constant ħ: [2, 1, -1])
        let e1 = CanonicalExpr::Var(VariableId(101)); // E
        let w1 = CanonicalExpr::Var(VariableId(102)); // omega
        let dim_e = DimensionVector::from_integers(&[2, 1, -2]); // Energy [L^2 M T^-2]
        let dim_w = DimensionVector::from_integers(&[0, 0, -1]); // Frequency [T^-1]
        runtime.dim_context.bind(VariableId(101), dim_e.clone());
        runtime.dim_context.bind(VariableId(102), dim_w.clone());

        runtime.inject_incomplete_law("planck_einstein", &e1, &dim_e, &w1, &dim_w).expect("Inject 1");

        let j2 = CanonicalExpr::Var(VariableId(103)); // Angular momentum / action
        let dim_j = DimensionVector::from_integers(&[2, 1, -1]); // Action [L^2 M T^-1]
        let num2 = CanonicalExpr::Const(Rational::one());
        let dim_num = DimensionVector::dimensionless();
        runtime.dim_context.bind(VariableId(103), dim_j.clone());

        runtime.inject_incomplete_law("bohr_quantization", &j2, &dim_j, &num2, &dim_num).expect("Inject 2");

        // Both laws are initially quarantined in RAM
        assert_eq!(runtime.quarantine.len(), 2);

        // Discover constant
        let discoveries = runtime.discover_and_consolidate_constants().expect("Discover");
        assert!(!discoveries.is_empty(), "Must discover coupling constant");
        let disc = &discoveries[0];

        // Stress test and crown
        runtime.set_constant_naming_hook(|_rep| {
            ("ReducedPlanckConstant".to_string(), "hbar".to_string())
        });

        let summary = runtime.stress_test_discovered_constant(disc).expect("Stress test");
        assert!(summary.all_laws_passed);
        assert_eq!(summary.ingested_axioms_count, 2);

        // Verify Axis 6: Laws were evicted from quarantine and hypergraph
        assert_eq!(runtime.quarantine.len(), 0, "Crowned laws must be evicted from quarantine");

        // Verify Axis 7: Bridge admitted via MetaAdmissionProtocol into bridge registry
        let bridges = runtime.sovereignty_engine.bridge_registry.bridges();
        assert!(bridges.iter().any(|b| b.name == "ReducedPlanckConstant"));

        // Verify Axis 8: Ingested into DNA storage
        let initial_axioms = runtime.dna_engine.evolution_engine.storage.header.total_axioms;
        assert_eq!(initial_axioms, 2, "DNA storage must have 2 sovereign axioms");
    }

    // 2. Re-open runtime from the SAME persistent DNA file (Second run / re-ingestion)
    {
        let mut runtime = AletheiaRuntime::boot_or_create(Some(&dna_path), 7).expect("Re-boot runtime");
        let axioms_on_reboot = runtime.dna_engine.evolution_engine.storage.header.total_axioms;
        assert_eq!(axioms_on_reboot, 2, "Re-booted runtime must preserve exact axiom count");

        // Sovereign receipts were hydrated into the engine
        assert!(runtime.sovereignty_engine.sovereign_receipts.contains_key("planck_einstein"));
        assert!(runtime.sovereignty_engine.sovereign_receipts.contains_key("bohr_quantization"));

        // Quarantine must be empty
        assert_eq!(runtime.quarantine.len(), 0);

        // Now try injecting the SAME laws again
        let e1 = CanonicalExpr::Var(VariableId(101));
        let w1 = CanonicalExpr::Var(VariableId(102));
        let dim_e = DimensionVector::from_integers(&[2, 1, -2]);
        let dim_w = DimensionVector::from_integers(&[0, 0, -1]);

        let report = runtime.inject_incomplete_law("planck_einstein", &e1, &dim_e, &w1, &dim_w).expect("Re-inject");
        // Must be recognized as already sovereign without creating deficits or putting in quarantine!
        assert!(report.law_name == "planck_einstein");
        assert_eq!(runtime.quarantine.len(), 0, "Already sovereign laws must never enter quarantine");

        // Running discover_and_consolidate_constants() must find 0 candidates because quarantine is clean!
        let discoveries = runtime.discover_and_consolidate_constants().expect("Discover");
        assert_eq!(discoveries.len(), 0, "No spurious discovery on clean quarantine");

        // Verify total axioms in DNA did NOT increase
        assert_eq!(
            runtime.dna_engine.evolution_engine.storage.header.total_axioms, 2,
            "Total axioms in DNA must remain strictly idempotent and unchanged"
        );
    }

    // Clean up
    let _ = fs::remove_file(&dna_path);
    let _ = fs::remove_file(&q_path);
}

#[test]
fn test_constant_bridge_deduplication_and_no_redundant_prompt() {
    use std::sync::atomic::{AtomicUsize, Ordering};
    use std::sync::Arc;
    use aletheia_epistemic::DomainTag;

    let mut runtime = AletheiaRuntime::boot_or_create(None, 7).expect("Boot runtime");

    // Hook call counter to verify user is not prompted more than once
    let hook_call_count = Arc::new(AtomicUsize::new(0));
    let hook_counter_clone = Arc::clone(&hook_call_count);

    runtime.set_constant_naming_hook(move |_rep| {
        hook_counter_clone.fetch_add(1, Ordering::SeqCst);
        ("SpeedOfLight".to_string(), "c".to_string())
    });

    // 1. Inject collinear and homologous relativistic laws
    let e = CanonicalExpr::Var(VariableId(201)); // E [L^2 M T^-2]
    let p = CanonicalExpr::Var(VariableId(202)); // p [L M T^-1]
    let m = CanonicalExpr::Var(VariableId(203)); // m [M]
    let x = CanonicalExpr::Var(VariableId(204)); // x [L]
    let t = CanonicalExpr::Var(VariableId(205)); // t [T]

    let dim_e = DimensionVector::from_integers(&[2, 1, -2]);
    let dim_p = DimensionVector::from_integers(&[1, 1, -1]);
    let dim_m = DimensionVector::from_integers(&[0, 1, 0]);
    let dim_x = DimensionVector::from_integers(&[1, 0, 0]);
    let dim_t = DimensionVector::from_integers(&[0, 0, 1]);

    runtime.dim_context.bind(VariableId(201), dim_e.clone());
    runtime.dim_context.bind(VariableId(202), dim_p.clone());
    runtime.dim_context.bind(VariableId(203), dim_m.clone());
    runtime.dim_context.bind(VariableId(204), dim_x.clone());
    runtime.dim_context.bind(VariableId(205), dim_t.clone());

    runtime.inject_incomplete_law("photon_momentum_energy", &e, &dim_e, &p, &dim_p).expect("Inject 1");
    runtime.inject_incomplete_law("lightcone_wavefront", &x, &dim_x, &t, &dim_t).expect("Inject 2");
    runtime.inject_incomplete_law("einstein_mass_energy", &e, &dim_e, &m, &dim_m).expect("Inject 3");

    assert_eq!(runtime.quarantine.len(), 3);

    // 2. Discover constants: Must consolidate into a SINGLE report for carrier [1, 0, -1]
    let reports = runtime.discover_and_consolidate_constants().expect("Discover");
    assert_eq!(reports.len(), 1, "Must merge all collinear/homologous laws into 1 report");
    assert_eq!(reports[0].carrier_dimension, DimensionVector::from_integers(&[1, 0, -1]));
    assert_eq!(reports[0].freed_laws.len(), 3, "All 3 laws must be freed under carrier c");

    // 3. Stress test: Must invoke naming hook exactly ONCE
    let stress_summary = runtime.stress_test_discovered_constant(&reports[0]).expect("Stress test");
    assert!(stress_summary.all_laws_passed);
    assert_eq!(hook_call_count.load(Ordering::SeqCst), 1, "Hook must be called exactly once");

    // 4. Verify bridges in BridgeRegistry: exactly 1 bridge registered, targeting Relativity
    let bridges = runtime.sovereignty_engine.bridge_registry.bridges();
    assert_eq!(bridges.len(), 1, "Exactly 1 bridge must be registered");
    assert_eq!(bridges[0].name, "SpeedOfLight");
    assert_eq!(bridges[0].target, DomainTag::Relativity, "Target domain must be correctly inferred as Relativity");

    // 5. Try discovering or stress-testing again with the same dimension: Must NOT prompt or duplicate
    let second_discovery_rep = runtime.discover_coupling_constant(
        "another_rel_law",
        "E = p",
        DimensionVector::from_integers(&[1, 0, -1]),
        None,
        None,
        "c",
        "SpeedOfLight",
    ).expect("Discover constant");

    assert_eq!(second_discovery_rep.chosen_name, "SpeedOfLight");
    assert_eq!(hook_call_count.load(Ordering::SeqCst), 1, "Hook must NOT be called again for existing constant");
    assert_eq!(runtime.sovereignty_engine.bridge_registry.bridges().len(), 1, "Bridge registry must not duplicate");
}

