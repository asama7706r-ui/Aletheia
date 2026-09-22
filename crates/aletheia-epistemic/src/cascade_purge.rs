use crate::error::EpistemicError;
use crate::sovereign_receipt::SovereignReceipt;
use aletheia_egraph::TransactionalEGraph;
use aletheia_lattice::DimensionalContext;
use std::collections::{HashMap, HashSet};

/// سجل أرشفة تاريخي للقوانين المخلوعة والنظريات المسحوبة
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct RetractedLawRecord {
    pub law_id: String,
    pub retracted_at_epoch: u64,
    pub reason: String,
    pub overthrown_by: String,
    pub invalidated_rules: Vec<String>,
}

/// محرك التراجع المتتالي وتطهير الـ E-Graph الحي (E-Graph Purge & Retraction Engine)
/// يمنع تسرب المعرفة المخلوعة في الذاكرة الحية ومحركات التبسيط عند وقوع ثورة علمية
#[derive(Clone, Debug, Default)]
pub struct EGraphPurgeEngine {
    /// ربط كل قانون بمجموعة القواعد المشتقة منه (Law ID -> Set of Rule IDs)
    pub rule_associations: HashMap<String, HashSet<String>>,
    /// القواعد النشطة المعتمدة في محرك التبسيط والاشتقاق
    pub active_rules: HashSet<String>,
    /// أرشيف السحب التراجعي التاريخي
    pub retraction_archive: Vec<RetractedLawRecord>,
}

impl EGraphPurgeEngine {
    pub fn new() -> Self {
        Self {
            rule_associations: HashMap::new(),
            active_rules: HashSet::new(),
            retraction_archive: Vec::new(),
        }
    }

    /// ربط قاعدة إعادة كتابة بقانونها المصدري
    pub fn register_law_rule(
        &mut self,
        law_id: impl Into<String>,
        rule_id: impl Into<String>,
    ) {
        let l_id = law_id.into();
        let r_id = rule_id.into();
        self.active_rules.insert(r_id.clone());
        self.rule_associations
            .entry(l_id)
            .or_default()
            .insert(r_id);
    }

    /// تنشيط قاعدة يدوياً
    pub fn activate_rule(&mut self, rule_id: impl Into<String>) {
        self.active_rules.insert(rule_id.into());
    }

    /// إبطال قاعدة يدوياً
    pub fn deactivate_rule(&mut self, rule_id: &str) {
        self.active_rules.remove(rule_id);
    }

    /// فحص ما إذا كانت القاعدة نشطة
    pub fn is_rule_active(&self, rule_id: &str) -> bool {
        self.active_rules.contains(rule_id)
    }

    /// جلب كافة القواعد النشطة
    pub fn get_active_rules(&self) -> &HashSet<String> {
        &self.active_rules
    }

    /// تنفيذ التطهير المتتالي لهيكل القانون المخلوع وكافة النظريات التابعة في الـ DAG
    pub fn purge_hierarchy(
        &mut self,
        root_overthrown_id: &str,
        transitive_dependents: &[String],
        overthrown_by: &str,
        reason: &str,
        epoch: u64,
    ) -> Vec<String> {
        let mut all_to_retract = Vec::with_capacity(1 + transitive_dependents.len());
        all_to_retract.push(root_overthrown_id.to_string());
        all_to_retract.extend_from_slice(transitive_dependents);

        let mut total_invalidated_rules = Vec::new();

        for law_id in all_to_retract {
            let rules_for_this_law: Vec<String> = if let Some(rules) = self.rule_associations.remove(&law_id) {
                for r in &rules {
                    self.active_rules.remove(r);
                }
                rules.into_iter().collect()
            } else {
                Vec::new()
            };

            total_invalidated_rules.extend(rules_for_this_law.clone());

            self.retraction_archive.push(RetractedLawRecord {
                law_id,
                retracted_at_epoch: epoch,
                reason: reason.to_string(),
                overthrown_by: overthrown_by.to_string(),
                invalidated_rules: rules_for_this_law,
            });
        }

        total_invalidated_rules
    }

    /// إعادة بناء شجرة E-Graph جديدة ونظيفة بحقن القوانين السيادية النشطة فقط
    /// يضمن محو أي أصناف تكافؤ ملوثة بنسبة 100%
    pub fn rebuild_clean_egraph(
        active_laws: &[&SovereignReceipt],
    ) -> Result<TransactionalEGraph, EpistemicError> {
        let mut clean_egraph = TransactionalEGraph::new();
        let ctx = DimensionalContext::mathematical();

        for receipt in active_laws {
            clean_egraph.add_expr(&receipt.ast, &ctx)?;
        }

        clean_egraph.rebuild()?;
        Ok(clean_egraph)
    }
}
