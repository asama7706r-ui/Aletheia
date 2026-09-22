//! # aletheia-rewriting
//!
//! محرك التشبع والمطابقة وإعادة الكتابة ومستخلص نصل أوكام (المحور 5 في Notion)
//! - لغة الأنماط الرمزية مع الفصل الدستوري بين Wildcard و LiteralVar
//! - التحقق المسبق في O(1) عبر قانون انحفاظ البنية الطيفية ومبرهنة فاركاس (A-Priori Reachability)
//! - محرك المطابقة العلائقية Leapfrog Triejoin (Worst-Case Optimal / AGM Bound)
//! - دورة التشبع المتناوبة ثنائية الطور (Two-Phase Saturation) مع واجهة DeficitContext
//! - دفتر الأستاذ الرمزي وسقف ماكولاي البرهاني والتناقض الكمي والتراجع الذري
//! - مستخلص نصل أوكام في حقل Q عبر استرخاء ديكسترا على الرسوم الفائقة (Hypergraph Dijkstra)

pub mod error;
pub mod extractor;
pub mod pattern;
pub mod reachability;
pub mod rule;
pub mod ruleset;
pub mod saturation;
pub mod triejoin;

pub use error::RewritingError;
pub use extractor::{AstExtractor, Cost, ExtractedLawAST};
pub use pattern::{Pattern, Subst};
pub use reachability::{APrioriReachabilityFilter, SpectralVector};
pub use rule::{KoszulParityGuard, RewriteRule, RuleGuard, RuleKind};
pub use ruleset::standard_algebraic_ruleset;
pub use saturation::{
    DeficitContext, EmptyDeficitContext, SaturationConfig, SaturationEngine, SaturationReport,
    SimpleDeficitContext, SpeculativeLedger,
};
pub use triejoin::{leapfrog_intersect, LeapfrogSliceIterator, MatchResult, RelationalMatcher};
