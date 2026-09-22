use crate::anti_unification::{AntiUnifier, MetaTheorem};
use crate::compactor::PhysicalCompactor;
use crate::error::DnaError;
use crate::mmap_engine::DnaStorageEngine;
use crate::occam_extractor::{OccamHypergraphExtractor, OccamProofDag};
use crate::pareto_sieve::{ParetoLawCandidate, ParetoSieve};
use crate::spawner::AutonomousEvolutionEngine;
use aletheia_algebra::{CanonicalExpr, Rational};
use aletheia_epistemic::SovereignDnaPayload;

/// المحرك السيادي الموحد لركيزة الـ DNA والتطور الأنطولوجي (Aletheia Unified DNA Engine)
pub struct AletheiaDnaEngine {
    pub evolution_engine: AutonomousEvolutionEngine,
    pub occam_extractor: OccamHypergraphExtractor,
}

impl AletheiaDnaEngine {
    pub fn new(storage: DnaStorageEngine) -> Self {
        Self {
            evolution_engine: AutonomousEvolutionEngine::new(storage),
            occam_extractor: OccamHypergraphExtractor::new(),
        }
    }

    /// استيعاب حمولة المحور السابع وتثبيتها كسجلات سيادية في الـ DNA
    pub fn ingest_sovereign_payload(
        &mut self,
        payload: &SovereignDnaPayload,
    ) -> Result<usize, DnaError> {
        self.evolution_engine.ingest_sovereign_payload(payload)
    }

    /// زرع جسر اقتران فيزيائي مادي في الـ DNA وتحديث مصفوفة التوجيه ومستخلص البراهين
    pub fn materialize_bridge(
        &mut self,
        source_domain: u16,
        target_domain: u16,
        scale: Rational,
        step_cost: Rational,
    ) -> Result<u32, DnaError> {
        let class_id = self.evolution_engine.materialize_bridge_constant(
            source_domain,
            target_domain,
            scale.clone(),
        )?;

        // إضافة الانتقال إلى مستخلص براهين أوكام
        self.occam_extractor.add_transition(
            source_domain as u32,
            target_domain as u32,
            format!("Bridge_{}_{}", source_domain, target_domain),
            scale,
            step_cost,
        );
        self.evolution_engine.routing_matrix.recompute_all_known_pairs();

        Ok(class_id)
    }

    /// التمدد البعدي الفيزيائي الكنسي
    pub fn spawn_dimension(&mut self, name: &str) -> Result<u16, DnaError> {
        self.evolution_engine.spawn_dimension(name)
    }

    /// التمدد البعدي الفيزيائي مع فحص غربال الاستقلال الجبري الحتمي فوق Q
    pub fn spawn_dimension_checked(
        &mut self,
        name: &str,
        proposed_vector: &aletheia_lattice::DimensionVector,
        existing_basis: &[aletheia_lattice::DimensionVector],
    ) -> Result<u16, DnaError> {
        self.evolution_engine
            .spawn_dimension_checked(name, proposed_vector, existing_basis)
    }

    /// تسجيل مجال معرفي مستقل في ركيزة الـ DNA
    pub fn materialize_domain(
        &mut self,
        domain_id: u16,
        group_id: u16,
        basis_id: u32,
    ) -> Result<(), DnaError> {
        self.evolution_engine
            .materialize_domain(domain_id, group_id, basis_id)
    }

    /// تسجيل مجال معرفي مستقل في ركيزة الـ DNA مع وصف نصي
    pub fn materialize_domain_with_descriptor(
        &mut self,
        domain_id: u16,
        group_id: u16,
        basis_id: u32,
        name: &str,
    ) -> Result<(), DnaError> {
        self.evolution_engine
            .materialize_domain_with_descriptor(domain_id, group_id, basis_id, name)
    }

    /// استرجاع مسار التحويل وثابت الاقتران التراكمي في زمن O(1)
    pub fn query_bridge_path(
        &self,
        source_domain: u16,
        target_domain: u16,
    ) -> (Vec<u16>, Rational) {
        self.evolution_engine.query_bridge_path(source_domain, target_domain)
    }

    /// تصفية وترتيب القوانين المرشحة بجبهة باريتو الموزونة بكلفة أوكام في Q
    pub fn sieve_pareto_candidates(
        &self,
        candidates: &[ParetoLawCandidate],
        alpha: Rational,
        beta: Rational,
    ) -> Vec<(ParetoLawCandidate, Rational)> {
        ParetoSieve::rank_frontier(candidates, alpha, beta)
    }

    /// استخراج برهان أوكام الأصغري (Minimal Proof DAG) للتحويل بين صنفين
    pub fn extract_proof(&self, source_class: u32, target_class: u32) -> Option<OccamProofDag> {
        self.occam_extractor.extract_minimal_proof(source_class, target_class)
    }

    /// استقراء وصياغة نظرية فوقية (Meta-Theorem) عبر التوحيد العكسي (Plotkin's LGG)
    #[allow(clippy::too_many_arguments)]
    pub fn synthesize_meta_theorem(
        &self,
        meta_id: &str,
        law_a: &str,
        domain_a: u16,
        expr_a: &CanonicalExpr,
        law_b: &str,
        domain_b: u16,
        expr_b: &CanonicalExpr,
    ) -> MetaTheorem {
        AntiUnifier::synthesize_meta_theorem(
            meta_id, law_a, domain_a, expr_a, law_b, domain_b, expr_b,
        )
    }

    /// تنفيذ التطهير المادي الشامل للملف وإسقاط شواهد القبور وإعادة تحميل المحرك
    pub fn compact_storage(self) -> Result<Self, DnaError> {
        let compacted_storage = PhysicalCompactor::compact_engine(self.evolution_engine.storage)?;
        Ok(Self {
            evolution_engine: AutonomousEvolutionEngine::new(compacted_storage),
            occam_extractor: self.occam_extractor,
        })
    }
}
