use crate::error::YonedaError;
use crate::linear_rref::LinearRREFEngine;
use crate::shadow::{CouplingCarrier, LatentShadow};
use crate::spectral_audit::ParallelSpectralAuditor;
use crate::tensorial::{TensorSignature, TensorialEngine};
use crate::toric_ideal::{ToricIdealClassifier, ToricResolutionResult};
use aletheia_algebra::{CanonicalExpr, Rational};
use aletheia_egraph::{EClassId, TransactionalEGraph};
use aletheia_lattice::{DimensionVector, DimensionalContext, SemanticGuard};

/// هدف الفحص والاستدلال للعجز
pub struct DeficitTarget<'a> {
    pub lhs: &'a CanonicalExpr,
    pub rhs: &'a CanonicalExpr,
    pub lhs_sig: TensorSignature,
    pub rhs_sig: TensorSignature,
}

impl<'a> DeficitTarget<'a> {
    pub fn new(
        lhs: &'a CanonicalExpr,
        rhs: &'a CanonicalExpr,
        lhs_sig: TensorSignature,
        rhs_sig: TensorSignature,
    ) -> Self {
        Self {
            lhs,
            rhs,
            lhs_sig,
            rhs_sig,
        }
    }

    pub fn scalar(lhs: &'a CanonicalExpr, rhs: &'a CanonicalExpr) -> Self {
        Self {
            lhs,
            rhs,
            lhs_sig: TensorSignature::scalar(),
            rhs_sig: TensorSignature::scalar(),
        }
    }
}

/// مخرجات محرك فضاء يونيدا لمعالجة العجز
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum ResolutionOutcome {
    /// تم استنتاج الكيان الحتمي بدقة قطعية دون أي خيار حر (dof = 0)
    ExactEntityResolved {
        symbol: String,
        shadow: LatentShadow,
    },
    /// إحالة الفرضية وظلها المعياري إلى الحجر الصحي (dof > 0)
    Quarantined(LatentShadow),
    /// رفض قاتل لتناقض منطقي مستحيل (1 = 0)
    Killed(String),
}

/// منسق حل العجز الهيكلي السالب في فضاء يونيدا (Yoneda Deficit Orchestrator)
pub struct DeficitOrchestrator;

impl DeficitOrchestrator {
    /// معالجة عجز الفرضية عبر المحركات الثلاثة مع تطبيق فك الارتباط التدريجي للمجاهيل
    pub fn resolve_deficit(
        egraph: &TransactionalEGraph,
        ctx: &DimensionalContext,
        target: DeficitTarget<'_>,
        candidate_bases: &[DimensionVector],
        target_classes: Vec<EClassId>,
        origin_law_id: &str,
    ) -> Result<ResolutionOutcome, YonedaError> {
        // 1. الفحص الموازي للأقفال الأربعة
        let audit = ParallelSpectralAuditor::audit_equivalence(egraph, ctx, target.lhs, target.rhs);
        if audit.has_fatal_contradiction() {
            return Ok(ResolutionOutcome::Killed("تناقض منطقي قاتل: 1 = 0".into()));
        }

        // 2. حل العجز التنسوري
        let tensor_gap = TensorialEngine::compute_rank_gap(target.lhs_sig, target.rhs_sig);

        // 3. حل العجز البعدي الخطي وتجانس الحدود
        let dim_lhs = SemanticGuard::infer_dimension(target.lhs, ctx).unwrap_or_else(|_| DimensionVector::dimensionless());
        let dim_rhs = SemanticGuard::infer_dimension(target.rhs, ctx).unwrap_or_else(|_| DimensionVector::dimensionless());
        let target_diff = &dim_lhs - &dim_rhs;

        let linear_res = LinearRREFEngine::solve_linear_system(candidate_bases, &target_diff);

        // 4. تطبيق فك الارتباط التدريجي والتجميد المرحلي (Sequential Decoupling & Partial Shadow Freezing)
        let mut joint_dof = if candidate_bases.is_empty() && !target_diff.is_dimensionless() {
            Rational::from_i64(target_diff.effective_len().max(1) as i64)
        } else if target_diff.is_dimensionless() && audit.d2 > 0 {
            Rational::from_i64(audit.d2 as i64)
        } else {
            linear_res.dof.clone()
        };

        if !candidate_bases.is_empty() && !linear_res.is_consistent {
            // العجز غير خطي؛ استدعاء مصنف المثاليات التوريكية
            let target_exps: Vec<Rational> = (0..target_diff.effective_len())
                .map(|r| target_diff.get_coord(r))
                .collect();
            let candidate_matrix: Vec<Vec<Rational>> = candidate_bases
                .iter()
                .map(|b| (0..target_diff.effective_len()).map(|r| b.get_coord(r)).collect())
                .collect();
            let degrees = vec![2; candidate_bases.len()];
            let toric_res = ToricIdealClassifier::solve_power_law_relation(
                &target_exps,
                &candidate_matrix,
                &degrees,
                100, // سقف الميزانية
            );

            match toric_res {
                ToricResolutionResult::Solved { dof, .. } => {
                    joint_dof = dof;
                }
                ToricResolutionResult::HighComplexitySafeQuarantine { macaulay_degree, budget } => {
                    // حماية استباقية من شلل التعقيد الأسي
                    let canonical_id = LatentShadow::compute_canonical_id(
                        &target_diff,
                        tensor_gap.required_rank,
                        &Rational::one(),
                        macaulay_degree,
                    );
                    let shadow = LatentShadow {
                        shadow_id: canonical_id,
                        origin_law_ids: vec![origin_law_id.to_string()],
                        dim_deficit: target_diff,
                        tensorial_rank: tensor_gap.required_rank,
                        dof: Rational::one(),
                        spectral_audit: audit,
                        coupling_carrier: None,
                        target_classes,
                        macaulay_ceiling: macaulay_degree.max(budget),
                    };
                    return Ok(ResolutionOutcome::Quarantined(shadow));
                }
                ToricResolutionResult::Inconsistent => {
                    joint_dof = Rational::from_i64(target_diff.effective_len().max(1) as i64);
                }
            }
        }

        // 5. فحص ما إذا كان العجز يتطلب حاملاً للاقتران البعدي (CouplingCarrier)
        let coupling_carrier = if !target_diff.is_dimensionless() {
            let symbol = format!("K_{}", origin_law_id);
            Some(CouplingCarrier::new(
                symbol,
                target_diff.clone(),
                aletheia_lattice::SemanticDomain::PhysicalCore,
            ))
        } else {
            None
        };

        // 6. استخراج البصمة الحتمية عبر BLAKE3
        let macaulay_bound = 1;
        let shadow_id = LatentShadow::compute_canonical_id(
            &target_diff,
            tensor_gap.required_rank,
            &joint_dof,
            macaulay_bound,
        );

        let latent_shadow = LatentShadow {
            shadow_id,
            origin_law_ids: vec![origin_law_id.to_string()],
            dim_deficit: target_diff,
            tensorial_rank: tensor_gap.required_rank,
            dof: joint_dof.clone(),
            spectral_audit: audit,
            coupling_carrier,
            target_classes,
            macaulay_ceiling: macaulay_bound,
        };

        // 7. اتخاذ القرار الحتمي وفق مبرهنة الرتبة والإلغاء
        if joint_dof.is_zero() {
            let symbol = format!("Entity_DeficitResolved_{}", hex_prefix(&shadow_id));
            Ok(ResolutionOutcome::ExactEntityResolved {
                symbol,
                shadow: latent_shadow,
            })
        } else {
            Ok(ResolutionOutcome::Quarantined(latent_shadow))
        }
    }

    /// استكشاف العجز الهيكلي عبر المعاملات التخمينية والعقد الشبحية والتخطيط متعدد الخطوات
    pub fn resolve_speculative_with_ghost(
        egraph: &mut TransactionalEGraph,
        ctx: &DimensionalContext,
        target: DeficitTarget,
        candidate_bases: &[DimensionVector],
        origin_law_id: &str,
        rules: &[aletheia_rewriting::RewriteRule],
    ) -> Result<ResolutionOutcome, YonedaError> {
        let checkpoint = egraph.checkpoint();

        // 1. الفحص المبدئي للعجز
        let initial_outcome = Self::resolve_deficit(
            egraph,
            ctx,
            DeficitTarget::new(target.lhs, target.rhs, target.lhs_sig, target.rhs_sig),
            candidate_bases,
            Vec::new(),
            origin_law_id,
        )?;

        match initial_outcome {
            ResolutionOutcome::ExactEntityResolved { .. } | ResolutionOutcome::Killed(_) => {
                egraph.commit(checkpoint);
                Ok(initial_outcome)
            }
            ResolutionOutcome::Quarantined(shadow) => {
                // 2. محاولة سد فجوة العجز dof > 0 عبر عقدة شبحية ومعاملة تخمينية
                let mut ghost_mgr = aletheia_egraph::GhostNodeManager::new();
                let ghost = ghost_mgr.spawn_ghost(
                    egraph,
                    Some(aletheia_lattice::LatticeData::new(
                        shadow.dim_deficit.clone(),
                        aletheia_lattice::SemanticDomain::PhysicalCore,
                    )),
                );

                let id_lhs = egraph.add_expr(target.lhs, ctx)?;
                let id_rhs = egraph.add_expr(target.rhs, ctx)?;

                // 3. تشغيل البحث ثنائي الاتجاه والتخطيط الاستدلالي
                let bidi = aletheia_rewriting::BidirectionalMeetInMiddle::new(15, 2000);
                let deficit_ctx = aletheia_rewriting::SimpleDeficitContext::new(
                    1,
                    vec![id_lhs, id_rhs, ghost.class_id],
                    10,
                );

                let bidi_res = bidi.search_intersection(
                    egraph,
                    ctx,
                    target.lhs,
                    target.rhs,
                    rules,
                    None,
                    &deficit_ctx,
                );

                let solved = if let Ok(ref res) = bidi_res {
                    res.success || egraph.find(id_lhs) == egraph.find(id_rhs)
                } else {
                    egraph.find(id_lhs) == egraph.find(id_rhs)
                };

                if solved {
                    ghost_mgr.materialize_ghost(ghost.ghost_id);
                    egraph.commit(checkpoint);
                    let symbol = format!("Speculative_GhostResolved_{}", hex_prefix(&shadow.shadow_id));
                    Ok(ResolutionOutcome::ExactEntityResolved { symbol, shadow })
                } else {
                    // التراجع التام عند الفشل لإبقاء الـ E-Graph طاهراً 100%
                    egraph.rollback(checkpoint);
                    Ok(ResolutionOutcome::Quarantined(shadow))
                }
            }
        }
    }
}

fn hex_prefix(bytes: &[u8; 32]) -> String {
    let mut s = String::with_capacity(8);
    for b in &bytes[0..4] {
        s.push_str(&format!("{:02x}", b));
    }
    s
}
