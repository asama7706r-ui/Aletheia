use crate::logic::{AuditTarget, EpistemicStatus, GatekeeperMode};
use crate::receipt::EpistemicAuditRecord;
use crate::seal_anchoring::{AnchoringSieve, NoetherRegistry};
use crate::seal_bridge::{BridgeRegistry, BridgeSieve, DomainTag};
use crate::seal_dimensional::DimensionalSieve;
use crate::seal_residual::ResidualSieve;
use aletheia_egraph::TransactionalEGraph;
use aletheia_lattice::DimensionalContext;

/// الحارس الإبستمولوجي المركزي لبوابات الحقيقة الرباعية (Epistemic Gatekeeper)
#[derive(Clone, Debug)]
pub struct EpistemicGatekeeper {
    pub bridge_registry: BridgeRegistry,
    pub noether_registry: NoetherRegistry,
    pub dimensional_context: DimensionalContext,
}

impl Default for EpistemicGatekeeper {
    fn default() -> Self {
        Self::new()
    }
}

impl EpistemicGatekeeper {
    pub fn new() -> Self {
        Self {
            bridge_registry: BridgeRegistry::new(),
            noether_registry: NoetherRegistry::standard_physics(),
            dimensional_context: DimensionalContext::new(),
        }
    }

    /// تسجيل بُعد متغير في سياق الأبعاد الفيزيائية للبوابة
    pub fn bind_variable(&mut self, var: aletheia_algebra::VariableId, dim: aletheia_lattice::DimensionVector) {
        self.dimensional_context.bind(var, dim);
    }

    /// تنفيذ تدقيق شامل للهدف عبر بوابات الحقيقة وفق نمط التشغيل المختار
    pub fn evaluate(
        &self,
        target: &AuditTarget,
        mode: GatekeeperMode,
        from_domain: DomainTag,
        to_domain: DomainTag,
        referenced_invariants: &[String],
        egraph_opt: Option<&mut TransactionalEGraph>,
    ) -> EpistemicAuditRecord {
        let candidate_id = target.candidate_id();

        match mode {
            // النمط الأول: المجس التشخيصي (Axis 6) - فحص كامل دون قطع فوري O(1)
            GatekeeperMode::DiagnosticScanner => {
                let mut receipts = Vec::with_capacity(4);

                // 1. القفل 1
                let r1 = ResidualSieve::verify(target);
                let d1 = if r1.passed { 0 } else { 1 };
                receipts.push(r1);

                // 2. القفل 2
                let r2 = DimensionalSieve::verify(target, &self.dimensional_context, None);
                let d2 = if r2.passed { 0 } else { 1 };
                receipts.push(r2);

                // 3. القفل 3
                let r3 = BridgeSieve::verify(&self.bridge_registry, from_domain, to_domain, None, None);
                let d3 = if r3.passed { 0 } else { 1 };
                receipts.push(r3);

                // 4. القفل 4
                let (solution, expr_opt) = match target {
                    AuditTarget::ConstraintSystem { solution, .. } => (Some(solution), None),
                    AuditTarget::SovereignCandidate(cand) => (None, Some(&cand.ast)),
                };
                let r4 = AnchoringSieve::verify(
                    &self.noether_registry,
                    referenced_invariants,
                    egraph_opt,
                    solution,
                    expr_opt,
                );
                let d4 = if r4.passed { 0 } else { 1 };
                receipts.push(r4);

                let diag = [d1, d2, d3, d4];
                let overall_status = if diag == [0, 0, 0, 0] {
                    EpistemicStatus::Proven
                } else {
                    EpistemicStatus::Uncertain
                };

                EpistemicAuditRecord::new(
                    candidate_id,
                    mode,
                    receipts,
                    overall_status,
                    Some(diag),
                )
            }

            // النمط الثاني: الحارس السيادي (Axis 7) - قطع فوري عند أول تعثر مع تحويل نزاع القفل 4
            GatekeeperMode::SovereignGate => {
                let mut receipts = Vec::new();

                // 1. فحص القفل 1
                let r1 = ResidualSieve::verify(target);
                let p1 = r1.passed;
                receipts.push(r1);
                if !p1 {
                    return EpistemicAuditRecord::new(
                        candidate_id,
                        mode,
                        receipts,
                        EpistemicStatus::Refuted,
                        None,
                    );
                }

                // 2. فحص القفل 2
                let r2 = DimensionalSieve::verify(target, &self.dimensional_context, None);
                let p2 = r2.passed;
                receipts.push(r2);
                if !p2 {
                    return EpistemicAuditRecord::new(
                        candidate_id,
                        mode,
                        receipts,
                        EpistemicStatus::Refuted,
                        None,
                    );
                }

                // 3. فحص القفل 3
                let r3 = BridgeSieve::verify(&self.bridge_registry, from_domain, to_domain, None, None);
                let p3 = r3.passed;
                receipts.push(r3);
                if !p3 {
                    return EpistemicAuditRecord::new(
                        candidate_id,
                        mode,
                        receipts,
                        EpistemicStatus::Refuted,
                        None,
                    );
                }

                // 4. فحص القفل 4
                let (solution, expr_opt) = match target {
                    AuditTarget::ConstraintSystem { solution, .. } => (Some(solution), None),
                    AuditTarget::SovereignCandidate(cand) => (None, Some(&cand.ast)),
                };
                let r4 = AnchoringSieve::verify(
                    &self.noether_registry,
                    referenced_invariants,
                    egraph_opt,
                    solution,
                    expr_opt,
                );
                let p4 = r4.passed;
                let details = r4.details.clone();
                receipts.push(r4);

                let overall_status = if p4 {
                    EpistemicStatus::Proven
                } else if details.contains("DISPUTE") {
                    // تحويل التعارض مع قاعدة قائمة في الشجرة إلى نزاع إبستمولوجي وليس إعداماً
                    EpistemicStatus::Disputed
                } else {
                    EpistemicStatus::Refuted
                };

                EpistemicAuditRecord::new(
                    candidate_id,
                    mode,
                    receipts,
                    overall_status,
                    None,
                )
            }
        }
    }
}
