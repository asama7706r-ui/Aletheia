use crate::error::RewritingError;
use crate::planner::ProofPlanResult;
use crate::reachability::RoadmapPlan;
use crate::rule::RewriteRule;
use crate::saturation::{DeficitContext, SaturationConfig, SaturationEngine};
use aletheia_algebra::{CanonicalExpr, Rational};
use aletheia_egraph::TransactionalEGraph;
use aletheia_lattice::DimensionalContext;

/// محرك البحث ثنائي الاتجاه والالتقاء في المنتصف (Bidirectional Meet-in-the-Middle)
/// يقلص تعقيد فضاء البحث من O(b^d) إلى O(2 * b^(d/2))
pub struct BidirectionalMeetInMiddle {
    pub max_step_budget: usize,
    pub node_limit: usize,
}

impl Default for BidirectionalMeetInMiddle {
    fn default() -> Self {
        Self {
            max_step_budget: 20,
            node_limit: 10_000,
        }
    }
}

impl BidirectionalMeetInMiddle {
    pub fn new(max_step_budget: usize, node_limit: usize) -> Self {
        Self {
            max_step_budget,
            node_limit,
        }
    }

    /// تنفيذ البحث المتوازي/المتناوب من الطرفين (LHS و RHS) حتى تقاطع فئات التكافؤ
    pub fn search_intersection(
        &self,
        egraph: &mut TransactionalEGraph,
        ctx: &DimensionalContext,
        start_expr: &CanonicalExpr,
        target_expr: &CanonicalExpr,
        rules: &[RewriteRule],
        roadmap: Option<&RoadmapPlan>,
        deficit: &impl DeficitContext,
    ) -> Result<ProofPlanResult, RewritingError> {
        let checkpoint = egraph.checkpoint();

        // 1. إضافة الطرفين إلى الـ EGraph كجبهتي بداية
        let forward_root = egraph.add_expr(start_expr, ctx)?;
        let backward_root = egraph.add_expr(target_expr, ctx)?;

        // فحص الالتقاء اللحظي المسبق
        if egraph.find(forward_root) == egraph.find(backward_root) {
            return Ok(ProofPlanResult {
                success: true,
                proof_trace: Vec::new(),
                synthesized_macro_rules: Vec::new(),
                initial_energy: Rational::zero(),
                final_energy: Rational::zero(),
                iterations: 0,
                total_applied_rules: 0,
            });
        }

        // 2. إعداد تكوين التشبع مع هدف الخروج المبكر عند التقاطع
        let config = SaturationConfig {
            max_iterations: self.max_step_budget,
            node_limit: self.node_limit,
            early_exit_target: Some((forward_root, backward_root)),
            roadmap_plan: roadmap.cloned(),
        };

        let engine = SaturationEngine::new(config);
        let report = engine.run(egraph, ctx, rules, deficit)?;

        // 3. التحقق من التقاطع في المنتصف (Meet-in-the-Middle)
        let intersected = egraph.find(forward_root) == egraph.find(backward_root);

        if intersected {
            egraph.commit(checkpoint);
            Ok(ProofPlanResult {
                success: true,
                proof_trace: report.proof_trace,
                synthesized_macro_rules: report.synthesized_macro_rules,
                initial_energy: Rational::from_i64(report.initial_node_count as i64),
                final_energy: Rational::zero(),
                iterations: report.iterations,
                total_applied_rules: report.applied_rules,
            })
        } else {
            // التراجع الآمن عن المعاملة عند عدم الالتقاء
            egraph.rollback(checkpoint);
            Ok(ProofPlanResult {
                success: false,
                proof_trace: report.proof_trace,
                synthesized_macro_rules: Vec::new(),
                initial_energy: Rational::from_i64(report.initial_node_count as i64),
                final_energy: Rational::from_i64(report.final_node_count as i64),
                iterations: report.iterations,
                total_applied_rules: report.applied_rules,
            })
        }
    }
}
