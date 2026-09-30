use aletheia_core::runtime::AletheiaRuntime;
use aletheia_core::parser::{parse_equation, parse_variable_bindings};
use aletheia_core::SymbolTable;
use aletheia_core::DimensionVector;
use aletheia_lattice::SemanticGuard;

#[test]
fn test_compton_reproduction() {
    let mut runtime = AletheiaRuntime::boot_or_create(None, 7).expect("boot failed");

    let default_candidate_bases = vec![
        ("c (Speed of Light)".to_string(), DimensionVector::from_integers(&[1, 0, -1])),
        ("G (Gravitational Constant)".to_string(), DimensionVector::from_integers(&[3, -1, -2])),
        ("ħ (Reduced Planck Constant)".to_string(), DimensionVector::from_integers(&[2, 1, -1])),
    ];
    let candidate_refs: Vec<(&str, DimensionVector)> = default_candidate_bases
        .iter()
        .map(|(n, d)| (n.as_str(), d.clone()))
        .collect();

    let mut symbols = SymbolTable::new();
    let (lhs, rhs) = parse_equation("lambda * m = 1", &mut symbols).expect("parse eq failed");
    let bindings = parse_variable_bindings("lambda: L, m: M", &mut symbols).expect("parse vars failed");
    for (vid, d) in bindings {
        runtime.dim_context.bind(vid, d);
    }
    let lhs_dim = SemanticGuard::infer_dimension(&lhs, &runtime.dim_context).expect("lhs dim");
    let rhs_dim = SemanticGuard::infer_dimension(&rhs, &runtime.dim_context).expect("rhs dim");

    let rep = runtime.resolve_incomplete_law("compton", &lhs, &lhs_dim, &rhs, &rhs_dim, &candidate_refs).expect("resolve failed");
    assert_eq!(rep.law_name, "compton");
    assert_eq!(rep.deficit_vector, DimensionVector::from_integers(&[1, 1, 0]));
    assert_eq!(rep.candidate_solutions.len(), 2);
    // Solution is c^-1 * ħ^1 = ħ / c
    assert_eq!(rep.candidate_solutions[0].1, aletheia_core::Rational::from_i64(-1));
    assert_eq!(rep.candidate_solutions[1].1, aletheia_core::Rational::from_i64(1));
    assert!(matches!(rep.outcome, aletheia_core::ResolutionOutcome::ExactEntityResolved { .. }));
}
