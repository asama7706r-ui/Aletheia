pub mod error;
pub mod hypothesis;
pub mod parser;
pub mod runtime;

// Re-exports
pub use error::CoreError;
pub use parser::{
    format_equation, format_expr, parse_candidate_bases, parse_dimension_str,
    parse_dimension_str_with_registry, parse_equation, parse_expr,
    parse_variable_bindings, split_respecting_brackets, split_respecting_brackets_by,
    SymbolTable,
};
pub use hypothesis::{HypothesisInput, HypothesisOutcome};
pub use runtime::{
    AletheiaRuntime, ConstantStressTestSummary, DimensionNamingCallback,
    DomainNamingCallback, DomainSpawningReport, IncompleteLawReport,
    NewDimensionDiscoveryReport, RuntimeStatus, SovereignMetaTheorem,
};

pub use aletheia_algebra::{CanonicalExpr, Rational, VariableId};
pub use aletheia_dna::{OccamProofDag, ParetoLawCandidate};
pub use aletheia_egraph::TransactionalEGraph;
pub use aletheia_epistemic::{DomainBridge, DomainDescriptor, DomainTag, SovereignReceipt};
pub use aletheia_lattice::{DimensionRegistry, DimensionVector, DimensionalContext, SemanticGuard};
pub use aletheia_rewriting::Cost;
pub use aletheia_yoneda::{CouplingCarrier, LatentShadow, ResolutionOutcome};
