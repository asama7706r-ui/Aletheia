//! # aletheia-dna
//!
//! المحور الدستوري 8 في Notion: غربال باريتو، والتطور المعرفي، وركيزة الـ DNA الثنائية mmap
//!
//! يمثل هذا الكريت الركيزة الفيزيائية الختامية للنواة المعرفية:
//! 1. خريطة الذاكرة المباشرة Zero-Copy mmap لملف `kernel.dna` في زمن شبه معدوم (< 3 ms).
//! 2. البذرة الجينية المدمجة في ثنائي البرنامج (`.rodata section`).
//! 3. التمدد البعدي الصفري ($\mathbb{Q}^N \to \mathbb{Q}^{N+1}$) وزرع ثوابت الاقتران كعقد مصمتة في الـ Arena.
//! 4. مصفوفة التوجيه الطوبولوجي المباشر في الذاكرة العشوائية للاستعلام في $O(1)$.
//! 5. استيعاب كبسولة صكوك السيادة القادمة من المحور السابع (`SovereignDnaPayload`).

pub mod anti_unification;
pub mod compactor;
pub mod embedded_seed;
pub mod engine;
pub mod error;
pub mod header;
pub mod hydration;
pub mod macro_sealer;
pub mod mmap_engine;
pub mod occam_extractor;
pub mod packed_enode;
pub mod pareto_sieve;
pub mod record;
pub mod spawner;

pub use anti_unification::{AntiUnifier, MetaTheorem};
pub use compactor::{safe_atomic_replace, CompactionReport, PhysicalCompactor};
pub use embedded_seed::{generate_canonical_seed, get_embedded_seed};
pub use engine::AletheiaDnaEngine;
pub use error::DnaError;
pub use macro_sealer::MacroRuleSealer;
pub use header::{
    PackedDNAHeader, DIMENSION_RANK_MASK, FLAG_COMPACTED, FLAG_LITTLE_ENDIAN, FLAG_SEED_MODE,
    HEADER_SIZE, MAGIC_KDNA,
};
pub use hydration::InstantHydrationPipeline;
pub use mmap_engine::{DnaStorageEngine, INITIAL_PREALLOCATION_SIZE};
pub use occam_extractor::{OccamHypergraphExtractor, OccamProofDag, OccamProofStep};
pub use packed_enode::{
    OpCode, PackedENode, ENODE_SIZE, FLAG_ASSOCIATIVE, FLAG_COMMUTATIVE, FLAG_IMMUTABLE_CONST,
};
pub use pareto_sieve::{pareto_dominates, ParetoLawCandidate, ParetoSieve};
pub use record::{
    UniversalRecordPrefix, MAGIC_RECD, RECORD_PREFIX_SIZE, RECORD_STATUS_ACTIVE,
    RECORD_STATUS_CONDITIONAL, RECORD_STATUS_TOMBSTONE, RECORD_TYPE_BRIDGE_DEF,
    RECORD_TYPE_CONGRUENCE_EDGE, RECORD_TYPE_DOMAIN_ENTRY, RECORD_TYPE_SOVEREIGN_AXIOM,
    RECORD_TYPE_TOMBSTONE_MASK,
};
pub use spawner::{
    verify_algebraic_independence, AutonomousEvolutionEngine, DirectBridgeRoutingMatrix,
    SpawnedDomainDescriptor,
};

