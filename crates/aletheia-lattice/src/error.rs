use thiserror::Error;

/// شجرة استثناءات الشبكيات والأبعاد الكونية (Lattice Errors)
/// تفرض الاتساق الدلالي وتطلق تراجعاً معاملاتياً فورياً عند خرق التجانس
#[derive(Error, Debug, Clone, PartialEq, Eq)]
pub enum LatticeError {
    #[error("Dimensional incompatibility in additive operation: expected {expected}, got {actual}")]
    IncompatibleDimensions { expected: String, actual: String },

    #[error("Transcendental function argument must be dimensionless [1], got dimension: {0}")]
    TranscendentalArgumentNotDimensionless(String),

    #[error("Dimension not found in registry: {0}")]
    DimensionNotFound(String),

    #[error("Variable x{0} has no physical dimension registered in DimensionalContext")]
    VariableDimensionMissing(u32),

    #[error("Linear dependence error during orthogonal base extension: {0}")]
    LinearDependence(String),

    #[error("Contradictory E-Graph equivalence class merge attempted: {0}")]
    ContradictoryMerge(String),

    #[error("General lattice contradiction: {0}")]
    General(String),
}
