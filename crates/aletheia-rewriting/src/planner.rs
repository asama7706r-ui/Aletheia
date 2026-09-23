use crate::error::RewritingError;
use crate::reachability::{APrioriReachabilityFilter, SpectralVector};
use crate::rule::{MacroRule, RewriteRule};
use crate::saturation::{DeficitContext, SaturationConfig, SaturationEngine};
use aletheia_algebra::{CanonicalExpr, Rational};
use aletheia_egraph::TransactionalEGraph;
use aletheia_lattice::DimensionalContext;

/// تقرير نتيجة التخطيط الاستدلالي متعدد الخطوات
#[derive(Clone, Debug)]
pub struct ProofPlanResult {
    pub success: bool,
    pub proof_trace: Vec<&'static str>,
    pub synthesized_macro_rules: Vec<MacroRule>,
    pub initial_energy: Rational,
    pub final_energy: Rational,
    pub iterations: usize,
    pub total_applied_rules: usize,
}

/// موجه التخطيط الاستدلالي متعدد الخطوات بخوارزمية A* المقولاتية ودالة انكماش لياكونوف
pub struct LyapunovAStarPlanner {
    pub max_iterations: usize,
    pub node_limit: usize,
}

impl Default for LyapunovAStarPlanner {
    fn default() -> Self {
        Self {
            max_iterations: 30,
            node_limit: 10_000,
        }
    }
}

impl LyapunovAStarPlanner {
    pub fn new(max_iterations: usize, node_limit: usize) -> Self {
        Self {
            max_iterations,
            node_limit,
        }
    }

    /// حساب طاقة لياكونوف الإبستمولوجية V(s) كدالة مسافة متفائلة ومقبولة (Admissible Heuristic)
    /// V(s) = ||S(target) - S(current)||_1
    pub fn compute_lyapunov_energy(current: &CanonicalExpr, target: &CanonicalExpr) -> Rational {
        let s_cur = SpectralVector::from_expr(current);
        let s_tar = SpectralVector::from_expr(target);
        let diff = s_tar.diff(&s_cur);

        let mut spectral_norm: i64 = 0;
        for &count in diff.var_counts.values() {
            spectral_norm += count.abs();
        }
        spectral_norm += diff.op_add.abs();
        spectral_norm += diff.op_mul.abs();
        spectral_norm += diff.op_div.abs();
        spectral_norm += diff.op_pow.abs();
        spectral_norm += diff.op_neg.abs();
        spectral_norm += diff.const_count.abs();

        Rational::from_i64(spectral_norm)
    }

    /// تنفيذ التخطيط الاستدلالي الموجه لإثبات التكافؤ بين تعبيرين
    pub fn plan_equivalence(
        &self,
        egraph: &mut TransactionalEGraph,
        ctx: &DimensionalContext,
        start_expr: &CanonicalExpr,
        target_expr: &CanonicalExpr,
        rules: &[RewriteRule],
        deficit: &impl DeficitContext,
    ) -> Result<ProofPlanResult, RewritingError> {
        let initial_energy = Self::compute_lyapunov_energy(start_expr, target_expr);

        // 1. فحص خارطة الطريق الاستباقية M_R * k = Delta S
        let reachability_filter = APrioriReachabilityFilter::from_rules(rules);
        let roadmap = reachability_filter.extract_roadmap_plan(start_expr, target_expr);

        // إذا أثبتت مصفوفة الوقوع استحالة الوصول قطيعة، ننهي البحث فوراً في O(1)
        if roadmap.is_none() && start_expr != target_expr {
            return Ok(ProofPlanResult {
                success: false,
                proof_trace: Vec::new(),
                synthesized_macro_rules: Vec::new(),
                initial_energy: initial_energy.clone(),
                final_energy: initial_energy,
                iterations: 0,
                total_applied_rules: 0,
            });
        }

        // 2. إدخال التعبيرين إلى الـ EGraph
        let start_id = egraph.add_expr(start_expr, ctx)?;
        let target_id = egraph.add_expr(target_expr, ctx)?;

        if egraph.find(start_id) == egraph.find(target_id) {
            return Ok(ProofPlanResult {
                success: true,
                proof_trace: Vec::new(),
                synthesized_macro_rules: Vec::new(),
                initial_energy: initial_energy.clone(),
                final_energy: Rational::zero(),
                iterations: 0,
                total_applied_rules: 0,
            });
        }

        // 3. تشغيل التشبع الموجه مع مرشح القواعد النشطة ومراقبة دالة لياكونوف
        let config = SaturationConfig {
            max_iterations: self.max_iterations,
            node_limit: self.node_limit,
            early_exit_target: Some((start_id, target_id)),
            roadmap_plan: roadmap,
        };

        let engine = SaturationEngine::new(config);
        let checkpoint = egraph.checkpoint();
        let report = engine.run(egraph, ctx, rules, deficit)?;

        let proved = egraph.find(start_id) == egraph.find(target_id);
        if proved {
            egraph.commit(checkpoint);
            Ok(ProofPlanResult {
                success: true,
                proof_trace: report.proof_trace,
                synthesized_macro_rules: report.synthesized_macro_rules,
                initial_energy,
                final_energy: Rational::zero(),
                iterations: report.iterations,
                total_applied_rules: report.applied_rules,
            })
        } else {
            // التراجع عند عدم اكتمال البرهان لحفظ نقاء الـ EGraph
            egraph.rollback(checkpoint);
            Ok(ProofPlanResult {
                success: false,
                proof_trace: report.proof_trace,
                synthesized_macro_rules: Vec::new(),
                initial_energy: initial_energy.clone(),
                final_energy: initial_energy,
                iterations: report.iterations,
                total_applied_rules: report.applied_rules,
            })
        }
    }
}
