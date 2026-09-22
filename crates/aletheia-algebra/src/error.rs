use thiserror::Error;

/// شجرة الاستثناءات التأسيسية للنواة المعرفية
/// تُرفع عند أي خرق للبديهيات الصرفة وتُطلق تراجعاً معاملاتياً فورياً
#[derive(Error, Debug, Clone, PartialEq, Eq)]
pub enum FormalContradictionError {
    #[error("Axiom violated: Division by zero in field Q")]
    DivisionByZero,

    #[error("Macaulay degree ceiling exceeded: max {max_degree}, got {actual}")]
    DegreeBudgetExceeded { max_degree: u32, actual: u32 },

    #[error("Computational step budget exhausted in Gröbner reduction: {budget} steps")]
    StepBudgetExceeded { budget: usize },

    #[error("Koszul graded parity violation: {0}")]
    ParityViolation(String),

    #[error("Contradictory equation in ideal: 1 = 0 ({0})")]
    ContradictoryEquation(String),

    #[error("Invalid canonical expression structure: {0}")]
    InvalidExpression(String),

    #[error("General axiomatic contradiction: {0}")]
    General(String),
}
