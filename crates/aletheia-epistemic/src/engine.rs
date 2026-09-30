use crate::anti_ptolemaic::AntiPtolemaicSieve;
use crate::arbitration::{ArbitrationPath, EpistemicArbitrator, LawDescriptor, LawStatus};
use crate::cascade_purge::EGraphPurgeEngine;
use crate::dna_handshake::SovereignDnaPayload;
use crate::error::EpistemicError;
use crate::gatekeeper::EpistemicGatekeeper;
use crate::logic::{AuditTarget, EpistemicStatus, GatekeeperMode};
use crate::meta_admission::{CandidateBridge, MetaAdmissionProtocol};
use crate::seal_anchoring::NoetherRegistry;
use crate::seal_bridge::{BridgeRegistry, DomainBridge, DomainTag};
use crate::sovereign_receipt::SovereignReceipt;
use aletheia_algebra::{CanonicalExpr, Rational};
use aletheia_egraph::TransactionalEGraph;
use aletheia_lattice::DimensionVector;
use aletheia_yoneda::CandidateSovereignLawAST;
use std::collections::{HashMap, HashSet};

/// نتيجة تقييم وتتويج القانون في المحرك الشامل
#[derive(Clone, Debug, PartialEq)]
pub enum SovereigntyOutcome {
    /// تتويج مباشر بعد اجتياز الأقفال الأربعة بنجاح مطلق دون نزاع
    DirectlyCrowned(SovereignReceipt),
    /// انتصار في الاستيعاب التقاربي وتتويج كـ ActiveAxiom مع خفض رتبة القديم
    SubsumptionVictorious(SovereignReceipt),
    /// انقلاب معرفي جذري: خلع القديم وإسقاط شجرة النظريات التابعة وتتويج الجديد
    OverthrowVictorious(SovereignReceipt, Vec<String>),
    /// ترسيم حدود أنطولوجية بين مجالين مستقلين
    DemarcatedBoundary(SovereignReceipt),
    /// عجز في معادلة حفظ: إحالة النزاع لمحرك دمج النيوترينو
    NeutrinoDeficitQuarantined(String),
    /// تعليق إبستمولوجي (Epoché) وحجز الطرفين في الحجر
    DualSuspensionQuarantined,
}

/// المحرك الشامل الموحد لحوكمة السيادة المعرفية (Epistemic Sovereignty Engine)
/// ينسق تدفق الفرضيات من بوابات الحقيقة إلى المحكم والتطهير المتتالي وحتى الجينوم المعرفي
#[derive(Clone, Debug)]
pub struct EpistemicSovereigntyEngine {
    pub gatekeeper: EpistemicGatekeeper,
    pub bridge_registry: BridgeRegistry,
    pub noether_registry: NoetherRegistry,
    pub arbitrator: EpistemicArbitrator,
    pub purge_engine: EGraphPurgeEngine,
    pub sovereign_receipts: HashMap<String, SovereignReceipt>,
    pub current_epoch: u64,
}

impl EpistemicSovereigntyEngine {
    pub fn new() -> Self {
        Self {
            gatekeeper: EpistemicGatekeeper::new(),
            bridge_registry: BridgeRegistry::new(),
            noether_registry: NoetherRegistry::standard_physics(),
            arbitrator: EpistemicArbitrator::new(),
            purge_engine: EGraphPurgeEngine::new(),
            sovereign_receipts: HashMap::new(),
            current_epoch: 1,
        }
    }

    /// ربط بعد فيزيائي لمتغير في بوابة السيادة
    pub fn bind_variable(&mut self, var: aletheia_algebra::VariableId, dim: aletheia_lattice::DimensionVector) {
        self.gatekeeper.bind_variable(var, dim);
    }

    /// البحث عن صك سيادي بالبصمة الكنسية BLAKE3
    pub fn find_sovereign_by_canonical_id(&self, canonical_id: &[u8; 32]) -> Option<&SovereignReceipt> {
        self.sovereign_receipts.values().find(|r| &r.canonical_id == canonical_id)
    }

    /// التحقق الهيكلي مما إذا كان التعبير أو المعادلة مسجلة كبديهية سيادية مسبقاً
    pub fn find_structurally_sovereign(
        &self,
        lhs: &CanonicalExpr,
        lhs_dim: &DimensionVector,
        rhs: &CanonicalExpr,
        deficit: &DimensionVector,
    ) -> Option<&SovereignReceipt> {
        let canonical_id = SovereignReceipt::compute_canonical_ast_hash(lhs, lhs_dim);
        let eq_canonical_id = SovereignReceipt::compute_canonical_equation_hash(lhs, rhs, deficit);

        self.sovereign_receipts.values().find(|r| {
            r.canonical_id == canonical_id
                || r.canonical_id == eq_canonical_id
                || (r.ast == *lhs && r.dimension == *lhs_dim)
        })
    }

    /// استخراج البديهيات السيادية القائمة كقواعد مرشحة لحل العجز مع استبعاد القانون الحالي هيكلياً
    pub fn get_sovereign_basis_candidates(
        &self,
        exclude_canonical_id: &[u8; 32],
        exclude_eq_id: &[u8; 32],
    ) -> Vec<(String, DimensionVector, Option<CanonicalExpr>)> {
        let mut bases = Vec::new();
        for (law_id, receipt) in &self.sovereign_receipts {
            if !receipt.dimension.is_dimensionless()
                && receipt.canonical_id != *exclude_canonical_id
                && receipt.canonical_id != *exclude_eq_id
            {
                bases.push((
                    format!("Axiom({})", law_id),
                    receipt.dimension.clone(),
                    Some(receipt.ast.clone()),
                ));
            }
        }
        bases
    }

    /// استخراج جسور الاقتران وثوابت الطبيعة المسجلة كقواعد مرشحة لحل العجز البعدي (C_known)
    pub fn get_bridge_basis_candidates(&self) -> Vec<(String, DimensionVector, Option<CanonicalExpr>)> {
        let mut bases = Vec::new();
        for bridge in self.bridge_registry.bridges() {
            if !bridge.coupling_dimension.is_dimensionless() {
                bases.push((
                    bridge.name.clone(),
                    bridge.coupling_dimension.clone(),
                    None,
                ));
            }
        }
        bases
    }

    /// تقييم مرشح سيادي قادم من الحجر الصحي وحسم مصيره الدستوري وتتويجه
    pub fn evaluate_and_crown_law(
        &mut self,
        candidate: CandidateSovereignLawAST,
        domain: DomainTag,
        referenced_invariants: &[String],
        competing_law: Option<&LawDescriptor>,
        egraph_opt: Option<&mut TransactionalEGraph>,
    ) -> Result<SovereigntyOutcome, EpistemicError> {
        // 1. غربال مناهضة بطليموس: التحقق من تناظرات نويثر المعلنة
        AntiPtolemaicSieve::verify_noether_invariants(referenced_invariants, &self.noether_registry)?;

        let law_name = format!("law_{}", hex_encode_4(&candidate.canonical_id));

        // 2. الفحص عبر بوابات الحقيقة الرباعية بنمط حارس السيادة الصارم
        let target = AuditTarget::sovereign(candidate.clone());
        let audit_record = self.gatekeeper.evaluate(
            &target,
            GatekeeperMode::SovereignGate,
            domain,
            domain,
            referenced_invariants,
            egraph_opt,
        );

        match audit_record.overall_status {
            EpistemicStatus::Proven if competing_law.is_none() => {
                // إجماع الأقفال الأربعة بنسبة 100% دون منافس: تتويج مباشر
                let receipt = SovereignReceipt::issue_active(
                    law_name.clone(),
                    candidate.canonical_id,
                    candidate.ast.clone(),
                    domain,
                    candidate.dim.clone(),
                    candidate.cost,
                    vec![audit_record.audit_hash],
                    audit_record.receipts,
                    candidate.asymptotic_certificate.map(|c| c.certificate_id),
                    self.current_epoch,
                    1000,
                );

                self.arbitrator.register_law(&law_name, LawStatus::ActiveAxiom);
                self.sovereign_receipts.insert(law_name, receipt.clone());

                Ok(SovereigntyOutcome::DirectlyCrowned(receipt))
            }
            EpistemicStatus::Proven | EpistemicStatus::Disputed => {
                // وجود قوانين منافسة قائمة أو نزاع إبستمولوجي: استدعاء المحكم الإبستمولوجي عبر كافة القوانين المعارضة
                let incumbents: Vec<LawDescriptor> = if let Some(existing) = competing_law {
                    vec![existing.clone()]
                } else {
                    // استخراج كافة القوانين النشطة القائمة في نفس المجال المعرفي
                    self.sovereign_receipts
                        .values()
                        .filter(|r| r.domain == domain && r.status == LawStatus::ActiveAxiom)
                        .map(|r| {
                            LawDescriptor::new(
                                r.law_id.clone(),
                                r.law_id.clone(),
                                r.ast.clone(),
                                r.domain,
                                r.dimension.clone(),
                                Rational::zero(),
                                r.cost,
                                HashSet::new(),
                            )
                        })
                        .collect()
                };

                if incumbents.is_empty() {
                    return Ok(SovereigntyOutcome::DualSuspensionQuarantined);
                }

                let candidate_desc = LawDescriptor::new(
                    law_name.clone(),
                    format!("Candidate {}", law_name),
                    candidate.ast.clone(),
                    domain,
                    candidate.dim.clone(),
                    Rational::zero(),
                    candidate.cost,
                    referenced_invariants.iter().cloned().collect(),
                );

                // مصفوفة حسم النزاعات التراكمية عبر كافة القوانين المتنازعة
                let mut all_retracted = Vec::new();
                let mut any_overthrow = false;
                let mut any_subsumption = false;
                let mut any_demarcation = false;
                let mut any_neutrino = None;

                for existing in &incumbents {
                    let verdict = self.arbitrator.adjudicate(
                        existing,
                        &candidate_desc,
                        candidate.asymptotic_certificate.as_ref(),
                    )?;

                    match verdict.path {
                        ArbitrationPath::Overthrow => {
                            any_overthrow = true;
                            let retracted = self.purge_engine.purge_hierarchy(
                                &existing.law_id,
                                &verdict.retracted_dependencies,
                                &law_name,
                                &verdict.rationale,
                                self.current_epoch,
                            );

                            self.sovereign_receipts.remove(&existing.law_id);
                            for dep in &verdict.retracted_dependencies {
                                self.sovereign_receipts.remove(dep);
                            }
                            all_retracted.extend(retracted);
                        }
                        ArbitrationPath::Subsumption => {
                            any_subsumption = true;
                            if let Some(old_receipt) = self.sovereign_receipts.get_mut(&existing.law_id) {
                                old_receipt.status = LawStatus::ConditionalLimit;
                                let regime = candidate
                                    .asymptotic_certificate
                                    .as_ref()
                                    .map(|c| format!("{} -> {}", c.parameter_name, c.limit_point))
                                    .unwrap_or_else(|| "AsymptoticLimit".to_string());
                                old_receipt.validity_regime = Some(regime);
                                old_receipt.parent_law_id = Some(law_name.clone());
                            }
                        }
                        ArbitrationPath::DomainDemarcation => {
                            any_demarcation = true;
                            if let Some(old_receipt) = self.sovereign_receipts.get_mut(&existing.law_id) {
                                old_receipt.status = LawStatus::DemarcatedBoundary;
                            }
                        }
                        ArbitrationPath::NeutrinoDeficit => {
                            if any_neutrino.is_none() {
                                any_neutrino = verdict.reconciled_variable;
                            }
                        }
                        ArbitrationPath::DualSuspension => {}
                    }
                }

                if any_overthrow {
                    let receipt = SovereignReceipt::issue_active(
                        law_name.clone(),
                        candidate.canonical_id,
                        candidate.ast.clone(),
                        domain,
                        candidate.dim.clone(),
                        candidate.cost,
                        vec![audit_record.audit_hash],
                        audit_record.receipts,
                        None,
                        self.current_epoch,
                        1000,
                    );

                    self.sovereign_receipts.insert(law_name, receipt.clone());
                    Ok(SovereigntyOutcome::OverthrowVictorious(receipt, all_retracted))
                } else if any_subsumption {
                    let receipt = SovereignReceipt::issue_active(
                        law_name.clone(),
                        candidate.canonical_id,
                        candidate.ast.clone(),
                        domain,
                        candidate.dim.clone(),
                        candidate.cost,
                        vec![audit_record.audit_hash],
                        audit_record.receipts,
                        candidate.asymptotic_certificate.map(|c| c.certificate_id),
                        self.current_epoch,
                        1000,
                    );

                    self.sovereign_receipts.insert(law_name, receipt.clone());
                    Ok(SovereigntyOutcome::SubsumptionVictorious(receipt))
                } else if any_demarcation {
                    let receipt = SovereignReceipt::issue(
                        law_name.clone(),
                        candidate.canonical_id,
                        candidate.ast.clone(),
                        domain,
                        candidate.dim.clone(),
                        candidate.cost,
                        LawStatus::DemarcatedBoundary,
                        None,
                        None,
                        vec![audit_record.audit_hash],
                        audit_record.receipts,
                        None,
                        self.current_epoch,
                        1000,
                    );
                    self.sovereign_receipts.insert(law_name, receipt.clone());
                    Ok(SovereigntyOutcome::DemarcatedBoundary(receipt))
                } else if let Some(hidden_var) = any_neutrino {
                    Ok(SovereigntyOutcome::NeutrinoDeficitQuarantined(hidden_var))
                } else {
                    Ok(SovereigntyOutcome::DualSuspensionQuarantined)
                }
            }
            EpistemicStatus::Refuted => Err(EpistemicError::FormalContradiction(
                "تم نقض المرشح السيادي ببرهان رياضي صلب من بوابات الحقيقة".to_string(),
            )),
            EpistemicStatus::Uncertain => Err(EpistemicError::PtolemaicOverfitting(
                "المرشح السيادي غير مكتمل القيود وله درجات حرية غير مصفّرة".to_string(),
            )),
        }
    }

    /// تصدير كبسولة الجينوم المعرفي المعتمدة لحساب المحور الثامن (kernel.dna)
    pub fn export_dna_payload(&self) -> Result<SovereignDnaPayload, EpistemicError> {
        let receipts: Vec<SovereignReceipt> = self.sovereign_receipts.values().cloned().collect();
        SovereignDnaPayload::package(receipts, self.current_epoch)
    }

    /// جلب قائمة الصكوك السيادية النشطة
    pub fn get_active_receipts(&self) -> Vec<&SovereignReceipt> {
        self.sovereign_receipts
            .values()
            .filter(|r| r.status == LawStatus::ActiveAxiom)
            .collect()
    }

    /// تدشين جسر أنطولوجي جديد عبر الأقفال الأربعة الميتا-معرفية واعتماده في السجل وبوابة السيادة
    pub fn admit_bridge(
        &mut self,
        candidate: &CandidateBridge,
        source_dim: Option<&DimensionVector>,
        target_dim: Option<&DimensionVector>,
        egraph_opt: Option<&mut TransactionalEGraph>,
    ) -> Result<DomainBridge, EpistemicError> {
        let bridge = MetaAdmissionProtocol::admit_bridge(
            &self.bridge_registry,
            candidate,
            source_dim,
            target_dim,
            egraph_opt,
        )?;
        self.bridge_registry.register_bridge(bridge.clone());
        self.gatekeeper.bridge_registry.register_bridge(bridge.clone());
        Ok(bridge)
    }
}

impl Default for EpistemicSovereigntyEngine {
    fn default() -> Self {
        Self::new()
    }
}

fn hex_encode_4(bytes: &[u8]) -> String {
    let mut s = String::with_capacity(8);
    for b in &bytes[0..4.min(bytes.len())] {
        s.push_str(&format!("{:02x}", b));
    }
    s
}
