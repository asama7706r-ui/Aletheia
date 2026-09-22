use crate::error::RewritingError;
use crate::extractor::{AstExtractor, Cost};
use crate::pattern::Pattern;
use crate::rule::{MacroRule, RewriteRule, RuleKind};
use crate::triejoin::{ENodeKind, RelationalMatcher};
use aletheia_egraph::{EClassId, ENode, TransactionalEGraph};
use aletheia_lattice::DimensionalContext;
use smallvec::SmallVec;
use std::collections::HashSet;

/// واجهة مجردة لسياق العجز الهيكلي وسقف ماكولاي (Deficit Context Interface)
/// تفصل المحور 5 دستورياً عن التبعية المباشرة للمحور 6 (فضاء يونييدا السالب)
pub trait DeficitContext {
    /// عدد درجات الحرية المتبقية للعجز الهيكلي
    fn remaining_dof(&self) -> usize;

    /// فئات التكافؤ المستهدفة بالعجز لتوجيه قواعد التوسع حصراً إليها
    fn target_classes(&self) -> &[EClassId];

    /// سقف ماكولاي المشتق برهانياً من درجات كثيرات الحدود ورتبة العجز
    fn macaulay_bound(&self) -> usize;
}

/// سياق عجز فارغ افتراضي للاستخدام العام عندما لا يوجد عجز هيكلي
#[derive(Clone, Debug, Default)]
pub struct EmptyDeficitContext;

impl DeficitContext for EmptyDeficitContext {
    fn remaining_dof(&self) -> usize {
        0
    }
    fn target_classes(&self) -> &[EClassId] {
        &[]
    }
    fn macaulay_bound(&self) -> usize {
        1
    }
}

/// سياق عجز مخصص ومرن للاختبارات والعمليات الموجهة
#[derive(Clone, Debug)]
pub struct SimpleDeficitContext {
    pub dof: usize,
    pub targets: Vec<EClassId>,
    pub bound: usize,
}

impl SimpleDeficitContext {
    pub fn new(dof: usize, targets: Vec<EClassId>, bound: usize) -> Self {
        Self {
            dof,
            targets,
            bound,
        }
    }
}

impl DeficitContext for SimpleDeficitContext {
    fn remaining_dof(&self) -> usize {
        self.dof
    }
    fn target_classes(&self) -> &[EClassId] {
        &self.targets
    }
    fn macaulay_bound(&self) -> usize {
        self.bound
    }
}

/// إعدادات وضوابط محرك التشبع (Saturation Configuration)
#[derive(Clone, Debug)]
pub struct SaturationConfig {
    pub max_iterations: usize,
    pub node_limit: usize,
    pub early_exit_target: Option<(EClassId, EClassId)>,
}

impl Default for SaturationConfig {
    fn default() -> Self {
        Self {
            max_iterations: 30,
            node_limit: 10_000,
            early_exit_target: None,
        }
    }
}

/// تقرير إنجاز دورة التشبع ومخرجاتها
#[derive(Clone, Debug)]
pub struct SaturationReport {
    pub iterations: usize,
    pub applied_rules: usize,
    pub proved_equivalence: bool,
    pub proof_trace: Vec<&'static str>,
    pub synthesized_macro_rules: Vec<MacroRule>,
    pub initial_node_count: usize,
    pub final_node_count: usize,
}

/// دفتر الأستاذ الرمزي وسقف ماكولاي البرهاني (The Speculative Ledger)
pub struct SpeculativeLedger {
    pub initial_local_cost: Cost,
    pub initial_total_nodes: usize,
    pub max_allowed_growth: u64,
}

impl SpeculativeLedger {
    pub fn new(initial_local_cost: Cost, initial_total_nodes: usize, macaulay_multiplier: usize) -> Self {
        // الحد الأدنى لحجم التكلفة الابتدائية 1 لمنع تصفير سقف النمو المسموح به
        let base_size = initial_local_cost.size.max(1);
        let max_allowed_growth = base_size.saturating_mul(macaulay_multiplier as u64);
        Self {
            initial_local_cost,
            initial_total_nodes,
            max_allowed_growth,
        }
    }

    /// فحص ما إذا كان التوسع ضمن الحدود الهيكلية المسموح بها (قياس صافي نمو العقد)
    pub fn check_growth(&self, current_total_nodes: usize) -> Result<(), RewritingError> {
        let net_growth = current_total_nodes.saturating_sub(self.initial_total_nodes) as u64;
        if net_growth > self.max_allowed_growth {
            Err(RewritingError::QuantitativeContradiction {
                current_cost: net_growth.to_string(),
                ceiling: self.max_allowed_growth.to_string(),
            })
        } else {
            Ok(())
        }
    }

    /// توافق خلفي مع فحص الميزانية
    pub fn check_budget(&self, current_total_nodes: usize) -> Result<(), RewritingError> {
        self.check_growth(current_total_nodes)
    }
}

/// محرك التشبع المتناوب ثنائي الطور (Two-Phase Equivalence Saturation Engine)
pub struct SaturationEngine {
    config: SaturationConfig,
}

impl SaturationEngine {
    pub fn new(config: SaturationConfig) -> Self {
        Self { config }
    }

    /// تشغيل دورة التشبع المتناوبة
    pub fn run(
        &self,
        egraph: &mut TransactionalEGraph,
        ctx: &DimensionalContext,
        rules: &[RewriteRule],
        deficit: &impl DeficitContext,
    ) -> Result<SaturationReport, RewritingError> {
        let initial_node_count = egraph.node_count();
        let checkpoint = egraph.checkpoint();

        // قياس الشجرة الابتدائية لكلا الهدفين قبل أي دمج لدعم تركيب القواعد العليا (Macro-Rules)
        let initial_lhs_ast = if let Some((lhs, _)) = self.config.early_exit_target {
            AstExtractor::new(egraph).extract(lhs, Vec::new()).ok()
        } else {
            None
        };
        let initial_rhs_ast = if let Some((_, rhs)) = self.config.early_exit_target {
            AstExtractor::new(egraph).extract(rhs, Vec::new()).ok()
        } else {
            None
        };

        let initial_cost = if let Some(ref l_ast) = initial_lhs_ast {
            l_ast.cost
        } else {
            Cost { size: (initial_node_count as u64).max(1), ..Default::default() }
        };

        let ledger = SpeculativeLedger::new(initial_cost, initial_node_count, deficit.macaulay_bound());

        let mut total_applied = 0;
        let mut proof_trace = Vec::new();
        let mut synthesized_macro_rules = Vec::new();
        let mut proved = false;
        let mut iter = 0;

        // فصل القواعد إلى اختزالية كنسية وتوسعية موجهة
        let canonical_rules: Vec<&RewriteRule> = rules
            .iter()
            .filter(|r| r.kind == RuleKind::CanonicalReduction)
            .collect();
        let expansion_rules: Vec<&RewriteRule> = rules
            .iter()
            .filter(|r| r.kind == RuleKind::DemandExpansion)
            .collect();

        while iter < self.config.max_iterations {
            iter += 1;
            let mut iter_applied = 0;

            // =========================================================================
            // الطور 1: الاختزال الكنسي حتى نقطة الثبات المحلية (Canonical Normalization)
            // =========================================================================
            loop {
                let mut can_step_applied = 0;
                let mut batch_unions = Vec::new();

                for rule in &canonical_rules {
                    let matches = RelationalMatcher::find_matches(egraph, &rule.lhs, None);
                    for m in matches {
                        if rule.check_guards(egraph, &m.subst) {
                            let raw_rhs = rule.rhs.instantiate(egraph, &m.subst, ctx)?;
                            // إعادة بناء السياق (Context Reconstruction) للعمليات متعددة المعاملات N-ary
                            let final_rhs = match m.n_ary_context {
                                Some((kind, ref remaining)) => {
                                    let mut ops = SmallVec::with_capacity(remaining.len() + 1);
                                    ops.extend(remaining.iter().copied());
                                    ops.push(raw_rhs);
                                    if ops.len() == 1 {
                                        ops[0]
                                    } else {
                                        let root_canon = egraph.find(m.root);
                                        let root_data = egraph.classes.get(&root_canon).and_then(|c| c.data.clone());
                                        let node = match kind {
                                            ENodeKind::Add => ENode::Add(ops),
                                            ENodeKind::Mul => ENode::Mul(ops),
                                        };
                                        egraph.add_node(node, root_data)
                                    }
                                }
                                None => raw_rhs,
                            };

                            let lhs_id = m.root;
                            if egraph.find(lhs_id) != egraph.find(final_rhs) {
                                batch_unions.push((lhs_id, final_rhs, rule.name));
                            }
                        }
                    }
                }

                if batch_unions.is_empty() {
                    break; // وصلنا لنقطة الثبات القياسية (Normal Form)
                }

                // تطبيق دفعي مجمع مع إعادة بناء وحيدة (Batched Amortized Rebuild)
                for (lhs_id, rhs_id, rule_name) in batch_unions {
                    if egraph.union(lhs_id, rhs_id)? {
                        can_step_applied += 1;
                        proof_trace.push(rule_name);
                    }
                }

                egraph.rebuild()?;
                iter_applied += can_step_applied;
                total_applied += can_step_applied;
            }

            // فحص الخروج المبكر في O(1) عند إثبات التكافؤ المستهدف
            if let Some((lhs_target, rhs_target)) = self.config.early_exit_target {
                if egraph.find(lhs_target) == egraph.find(rhs_target) {
                    // تركيب قاعدة عليا كاختصار لعبور الهضاب إن وُجد مسار اشتقاقي مركب
                    if let (Some(ref l_ast), Some(ref r_ast)) = (&initial_lhs_ast, &initial_rhs_ast) {
                        if l_ast.ast != r_ast.ast && !proof_trace.is_empty() {
                            let (from_ast, to_ast) = if l_ast.cost >= r_ast.cost {
                                (&l_ast.ast, &r_ast.ast)
                            } else {
                                (&r_ast.ast, &l_ast.ast)
                            };
                            synthesized_macro_rules.push(MacroRule::new(
                                format!("Macro_PlateauShortcut_{}", synthesized_macro_rules.len() + 1),
                                Pattern::from_canonical_expr(from_ast),
                                Pattern::from_canonical_expr(to_ast),
                            ));
                        }
                    }

                    egraph.commit(checkpoint);
                    return Ok(SaturationReport {
                        iterations: iter,
                        applied_rules: total_applied,
                        proved_equivalence: true,
                        proof_trace,
                        synthesized_macro_rules,
                        initial_node_count,
                        final_node_count: egraph.node_count(),
                    });
                }
            }

            // إذا لم يكن هناك عجز هيكلي متبقٍ، ولم تنطبق أي قاعدة، انتهى التشبع
            if deficit.remaining_dof() == 0 && iter_applied == 0 {
                break;
            }

            // =========================================================================
            // الطور 2: التوسع الهيكلي الموجه بالعجز (Demand-Driven Deficit Expansion)
            // =========================================================================
            if deficit.remaining_dof() > 0 && !expansion_rules.is_empty() {
                let mut exp_applied = 0;
                let mut batch_unions = Vec::new();

                let targets = deficit.target_classes();
                let dirty_set: Option<HashSet<EClassId>> = if targets.is_empty() {
                    None
                } else {
                    Some(targets.iter().copied().collect())
                };

                for rule in &expansion_rules {
                    let matches = RelationalMatcher::find_matches(egraph, &rule.lhs, dirty_set.as_ref());
                    for m in matches {
                        if rule.check_guards(egraph, &m.subst) {
                            let raw_rhs = rule.rhs.instantiate(egraph, &m.subst, ctx)?;
                            // إعادة بناء السياق (Context Reconstruction) للعمليات متعددة المعاملات N-ary
                            let final_rhs = match m.n_ary_context {
                                Some((kind, ref remaining)) => {
                                    let mut ops = SmallVec::with_capacity(remaining.len() + 1);
                                    ops.extend(remaining.iter().copied());
                                    ops.push(raw_rhs);
                                    if ops.len() == 1 {
                                        ops[0]
                                    } else {
                                        let root_canon = egraph.find(m.root);
                                        let root_data = egraph.classes.get(&root_canon).and_then(|c| c.data.clone());
                                        let node = match kind {
                                            ENodeKind::Add => ENode::Add(ops),
                                            ENodeKind::Mul => ENode::Mul(ops),
                                        };
                                        egraph.add_node(node, root_data)
                                    }
                                }
                                None => raw_rhs,
                            };

                            let lhs_id = m.root;
                            if egraph.find(lhs_id) != egraph.find(final_rhs) {
                                batch_unions.push((lhs_id, final_rhs, rule.name));
                            }
                        }
                    }
                }

                for (lhs_id, rhs_id, rule_name) in batch_unions {
                    if egraph.union(lhs_id, rhs_id)? {
                        exp_applied += 1;
                        proof_trace.push(rule_name);
                    }
                }

                if exp_applied > 0 {
                    egraph.rebuild()?;
                    iter_applied += exp_applied;
                    total_applied += exp_applied;

                    // فحص دفتر الأستاذ وسقف ماكولاي: قياس صافي نمو العقد مع سقف أدنى للتكلفة
                    if let Err(e) = ledger.check_growth(egraph.node_count()) {
                        egraph.rollback(checkpoint);
                        return Err(e);
                    }
                }
            }

            // فحص سقف العقد العام لمنع الانفجار
            if egraph.node_count() > self.config.node_limit {
                egraph.rollback(checkpoint);
                return Err(RewritingError::BudgetExceeded);
            }

            if iter_applied == 0 {
                break; // نقطة ثبات شاملة
            }
        }

        // فحص نهائي للهدف
        if let Some((lhs_target, rhs_target)) = self.config.early_exit_target {
            if egraph.find(lhs_target) == egraph.find(rhs_target) {
                proved = true;
                if let (Some(ref l_ast), Some(ref r_ast)) = (&initial_lhs_ast, &initial_rhs_ast) {
                    if l_ast.ast != r_ast.ast && !proof_trace.is_empty() {
                        let (from_ast, to_ast) = if l_ast.cost >= r_ast.cost {
                            (&l_ast.ast, &r_ast.ast)
                        } else {
                            (&r_ast.ast, &l_ast.ast)
                        };
                        synthesized_macro_rules.push(MacroRule::new(
                            format!("Macro_PlateauShortcut_{}", synthesized_macro_rules.len() + 1),
                            Pattern::from_canonical_expr(from_ast),
                            Pattern::from_canonical_expr(to_ast),
                        ));
                    }
                }
            }
        }

        egraph.commit(checkpoint);

        Ok(SaturationReport {
            iterations: iter,
            applied_rules: total_applied,
            proved_equivalence: proved,
            proof_trace,
            synthesized_macro_rules,
            initial_node_count,
            final_node_count: egraph.node_count(),
        })
    }
}

