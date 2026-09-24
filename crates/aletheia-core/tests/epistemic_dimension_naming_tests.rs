use aletheia_algebra::{CanonicalExpr, Rational, VariableId};
use aletheia_core::{
    format_equation, parse_dimension_str,
    parse_dimension_str_with_registry, parse_variable_bindings, AletheiaRuntime,
    DimensionVector, SymbolTable,
};
use aletheia_lattice::DimensionId;

#[test]
fn test_pure_dimensional_recognition_strictly_enforced() {
    // 1. Direct coordinate vectors [L, M, T, ...]
    let dim_coords = parse_dimension_str("[2, 1, -2]").expect("Must parse coordinate vector");
    assert_eq!(dim_coords.get_coord(0), Rational::from_i64(2));
    assert_eq!(dim_coords.get_coord(1), Rational::from_i64(1));
    assert_eq!(dim_coords.get_coord(2), Rational::from_i64(-2));

    // 2. Bracketed keyed coordinate notation
    let dim_keyed = parse_dimension_str("[L: 2, M: 1, T: -2]").expect("Must parse keyed vector");
    assert_eq!(dim_coords, dim_keyed);

    // 3. Pure base dimension algebraic expressions
    let dim_alg = parse_dimension_str("L^2 * M / T^2").expect("Must parse algebraic expression");
    assert_eq!(dim_coords, dim_alg);

    // 4. Kinematic and derived expressions in base dimensions
    let vel_alg = parse_dimension_str("L / T").expect("Must parse L/T");
    let vel_vec = parse_dimension_str("[1, 0, -1]").expect("Must parse [1, 0, -1]");
    assert_eq!(vel_alg, vel_vec);

    let force_alg = parse_dimension_str("L * M / T^2").expect("Must parse force dimension");
    let force_vec = parse_dimension_str("[1, 1, -2]").expect("Must parse force vector");
    assert_eq!(force_alg, force_vec);

    // 5. Dimensionless scalars
    assert!(parse_dimension_str("1").expect("1 is dimensionless").is_dimensionless());
    assert!(parse_dimension_str("[1]").expect("[1] is dimensionless").is_dimensionless());
    assert!(parse_dimension_str("dimensionless").expect("keyword dimensionless").is_dimensionless());

    // 6. Strict rejection of colloquial physical names (only dimensional invariants allowed!)
    assert!(parse_dimension_str("energy").is_err());
    assert!(parse_dimension_str("force").is_err());
    assert!(parse_dimension_str("viscosity").is_err());
    assert!(parse_dimension_str("pressure").is_err());
    assert!(parse_dimension_str("c").is_err());
    assert!(parse_dimension_str("G").is_err());

    // 7. Variable dimension bindings using pure dimensions
    let mut symbols = SymbolTable::new();
    let bindings = parse_variable_bindings("F: L * M / T^2, m: M, a: L / T^2", &mut symbols)
        .expect("Must parse pure dimension bindings");
    assert_eq!(bindings.len(), 3);

    // 8. Mathematical unparsing
    let f_var = CanonicalExpr::Var(VariableId(1));
    let m_var = CanonicalExpr::Var(VariableId(2));
    let a_var = CanonicalExpr::Var(VariableId(3));
    let ma_expr = CanonicalExpr::Mul(vec![m_var, a_var]);
    let eq_str = format_equation(&f_var, &ma_expr, &symbols);
    assert_eq!(eq_str, "F = m * a");
}

#[test]
fn test_new_dimension_discovery_epistemic_trajectory_and_human_naming() {
    let mut runtime = AletheiaRuntime::boot_or_create(None, 7).expect("Boot runtime at rank 7");
    assert_eq!(runtime.dim_registry.dimension_count(), 7);

    // Setup hooks allowing the human to inspect the derivation trajectory and assign custom symbols/names
    runtime.set_dimension_naming_hook({
        move |report| {
            // Verify epistemic derivation trajectory fields
            assert_eq!(report.dimension_index, 7);
            assert_eq!(report.existing_subspace_rank, 7);
            assert!(report.derivation_trail.contains("shannon_capacity_1") || report.derivation_trail.contains("shannon_capacity_2"));
            assert!(report.independence_proof.contains("Algebraic independence verified"));
            assert_eq!(report.suggested_symbol, "D7");
            assert_eq!(report.suggested_name, "Dimension_7");

            // Sovereign human decision: name the dimension "InformationEntropy" with symbol "B"
            ("InformationEntropy".to_string(), "B".to_string())
        }
    });

    runtime.set_domain_naming_hook({
        move |dom_report| {
            // Verify domain spawning report fields
            assert_eq!(dom_report.basis_dimension_index, 7);
            assert_eq!(dom_report.dimension_symbol, "B");
            assert!(dom_report.suggested_domain_name.contains("InformationEntropy"));

            // Sovereign human decision: name the domain "InformationDynamics"
            "InformationDynamics".to_string()
        }
    });

    // Inject two incomplete laws exhibiting an identical dimensional deficit in an 8th orthogonal dimension:
    // Deficit vector has non-zero coordinate at index 7 (e_7): [0, 0, -1, 0, 0, 0, 0, 1] (Bit per second)
    let b1 = CanonicalExpr::Var(VariableId(801));
    let t1 = CanonicalExpr::Var(VariableId(802));
    let rhs1 = CanonicalExpr::Div(Box::new(b1), Box::new(t1));
    let dim_b = DimensionVector::unit_basis(7, 8); // [0, 0, 0, 0, 0, 0, 0, 1]
    let dim_t = DimensionVector::from_integers(&[0, 0, 1]); // Time [T]
    let dim_rhs1 = &dim_b - &dim_t; // [0, 0, -1, 0, 0, 0, 0, 1]

    let rate1 = CanonicalExpr::Var(VariableId(803));
    let dim_rate1 = DimensionVector::dimensionless(); // Uncalibrated rate

    runtime.dim_context.bind(VariableId(801), dim_b.clone());
    runtime.dim_context.bind(VariableId(802), dim_t.clone());
    runtime.dim_context.bind(VariableId(803), dim_rate1.clone());

    let rep1 = runtime.inject_incomplete_law("shannon_capacity_1", &rate1, &dim_rate1, &rhs1, &dim_rhs1)
        .expect("Inject law 1");
    assert_eq!(rep1.deficit_vector.get_coord(7), Rational::from_i64(-1));

    let rate2 = CanonicalExpr::Var(VariableId(804));
    let rhs2 = CanonicalExpr::Var(VariableId(805));
    runtime.dim_context.bind(VariableId(804), dim_rate1);
    runtime.dim_context.bind(VariableId(805), dim_rhs1.clone());

    let rep2 = runtime.inject_incomplete_law("shannon_capacity_2", &rate2, &DimensionVector::dimensionless(), &rhs2, &dim_rhs1)
        .expect("Inject law 2");
    assert_eq!(rep2.deficit_vector.get_coord(7), Rational::from_i64(-1));

    // Consolidate via neutrino consolidation
    let reports = runtime.discover_and_consolidate_constants().expect("Consolidate constants");
    assert_eq!(reports.len(), 1, "Expected shared invariant carrier to be discovered");

    // Stress test and trigger autonomous orthogonal extension with human naming
    let stress_summary = runtime.stress_test_discovered_constant(&reports[0]).expect("Stress test");
    assert!(stress_summary.all_laws_passed);
    assert_eq!(stress_summary.spawned_dimensions.len(), 1);
    assert_eq!(stress_summary.spawned_dimensions[0], "InformationEntropy [B]");

    // Verify reports
    assert_eq!(stress_summary.spawned_dimension_reports.len(), 1);
    let dim_rep = &stress_summary.spawned_dimension_reports[0];
    assert_eq!(dim_rep.dimension_index, 7);
    assert_eq!(dim_rep.chosen_name, "InformationEntropy");
    assert_eq!(dim_rep.chosen_symbol, "B");
    assert_eq!(dim_rep.deficit_vector.get_coord(7), Rational::from_i64(-1));

    assert_eq!(stress_summary.spawned_domain_reports.len(), 1);
    let dom_rep = &stress_summary.spawned_domain_reports[0];
    assert_eq!(dom_rep.chosen_domain_name, "InformationDynamics");
    assert_eq!(dom_rep.dimension_symbol, "B");

    // Verify that the new dimension is fully functional in the DimensionRegistry
    assert_eq!(runtime.dim_registry.dimension_count(), 8);
    assert_eq!(runtime.dim_registry.get_symbol(DimensionId(7)).unwrap(), "B");
    assert_eq!(runtime.dim_registry.get_name(DimensionId(7)).unwrap(), "InformationEntropy");
    assert_eq!(runtime.dim_registry.find_by_symbol("B"), Some(DimensionId(7)));

    // Verify that the parser can now parse expressions with the new symbol "B"
    let parsed_with_b = parse_dimension_str_with_registry("B / T", &runtime.dim_registry)
        .expect("Must parse expression with newly discovered dimension symbol B");
    assert_eq!(parsed_with_b.get_coord(7), Rational::from_i64(1));
    assert_eq!(parsed_with_b.get_coord(2), Rational::from_i64(-1));

    // Verify that DimensionRegistry formats vectors using the new symbol
    let formatted_vec = runtime.dim_registry.format_vector(&parsed_with_b);
    assert!(formatted_vec.contains("[B]"));
    assert!(formatted_vec.contains("[T]^(-1)"));

    // Verify that DNA storage header rank expanded from 7 to 8
    assert_eq!(runtime.dna_engine.evolution_engine.storage.header.dimension_rank(), 8);
}
