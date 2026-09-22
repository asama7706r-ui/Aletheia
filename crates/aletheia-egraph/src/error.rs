use crate::id::EClassId;
use aletheia_lattice::LatticeError;
use thiserror::Error;

/// شجرة أخطاء واستثناءات الـ E-Graph المعاملاتي
#[derive(Error, Debug, Clone, PartialEq, Eq)]
pub enum EGraphError {
    #[error("Dimensional lattice clash during e-class merge: {0}")]
    Lattice(#[from] LatticeError),

    #[error("Axiomatic contradiction in E-Graph: {0}")]
    Contradiction(String),

    #[error("E-Class {0} not found in arena")]
    ClassNotFound(EClassId),

    #[error("General E-Graph error: {0}")]
    General(String),
}
