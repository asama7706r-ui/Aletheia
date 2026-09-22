use crate::error::EpistemicError;
use crate::receipt::{LockReceipt, LockType};
use aletheia_algebra::{CanonicalExpr, Rational, VariableId};
use aletheia_egraph::{ENode, TransactionalEGraph};
use aletheia_lattice::LatticeError;
use std::collections::{HashMap, HashSet};

/// سجل تناظرات وقوانين نويثر المعتمدة رسمياً في النواة
#[derive(Clone, Debug)]
pub struct NoetherRegistry {
    certified_invariants: HashSet<String>,
}

impl Default for NoetherRegistry {
    fn default() -> Self {
        Self::standard_physics()
    }
}

impl NoetherRegistry {
    pub fn new() -> Self {
        Self {
            certified_invariants: HashSet::new(),
        }
    }

    /// السجل المعياري للفيزياء الأساسية
    pub fn standard_physics() -> Self {
        let mut set = HashSet::new();
        set.insert("EnergyConservation".into());
        set.insert("LinearMomentumConservation".into());
        set.insert("AngularMomentumConservation".into());
        set.insert("ElectricChargeConservation".into());
        set.insert("LorentzInvariance".into());
        set.insert("CPTSymmetry".into());
        Self {
            certified_invariants: set,
        }
    }

    /// تسجيل تناظر معتمد جديد
    pub fn register_invariant(&mut self, invariant_name: impl Into<String>) {
        self.certified_invariants.insert(invariant_name.into());
    }

    /// التحقق من أن كافة التناظرات المشار إليها متجذرة في السجل المعتمد
    pub fn verify_invariants(&self, referenced: &[String]) -> Result<(), String> {
        for inv in referenced {
            if !self.certified_invariants.contains(inv) {
                return Err(format!("الفرضية تشير إلى تناظر غير معتمد رسمياً: '{}'", inv));
            }
        }
        Ok(())
    }
}

/// نتيجة الفحص المعاملي في التجربة الفكرية
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum GedankenexperimentResult {
    /// اجتياز تام: لا يوجد أي تناقض أو انهيار فترات
    Consistent,
    /// نزاع إبستمولوجي: تصادم في الفترات المعتمدة مع قاعدة قائمة (Lattice ContradictoryMerge)
    EpistemicDispute(String),
    /// تناقض صوري صريح في الـ E-Graph
    FormalContradiction(String),
}

/// القفل الرابع: غربال التجذير الأنطولوجي والتجربة الفكرية المعاملاتية (Seal 4)
pub struct AnchoringSieve;

impl AnchoringSieve {
    /// فحص التجذير في زمر نويثر، وإجراء التجربة الفكرية المعزولة في الـ E-Graph
    pub fn verify(
        noether: &NoetherRegistry,
        referenced_invariants: &[String],
        egraph_opt: Option<&mut TransactionalEGraph>,
        solution: Option<&HashMap<VariableId, Rational>>,
        expr_opt: Option<&CanonicalExpr>,
    ) -> LockReceipt {
        // 1. التحقق من التجذير الأنطولوجي في زمر نويثر المعتمدة
        if let Err(err_msg) = noether.verify_invariants(referenced_invariants) {
            return LockReceipt::new(
                LockType::OntologicalAnchor,
                "Ontological Anchoring",
                false,
                err_msg,
                None,
            );
        }

        // 2. إجراء التجربة الفكرية المعاملاتية المعزولة في الـ E-Graph (إن وجد)
        if let Some(egraph) = egraph_opt {
            let gedanken_result = Self::run_gedankenexperiment(egraph, solution, expr_opt);
            match gedanken_result {
                GedankenexperimentResult::Consistent => LockReceipt::new(
                    LockType::OntologicalAnchor,
                    "Ontological Anchoring & Gedankenexperiment",
                    true,
                    "اجتياز تام للمحاكاة الفكرية المعزولة دون أي تسميم أو انهيار للفترات",
                    None,
                ),
                GedankenexperimentResult::EpistemicDispute(dispute_msg) => LockReceipt::new(
                    LockType::OntologicalAnchor,
                    "Ontological Anchoring (Epistemic Dispute)",
                    false,
                    format!("DISPUTE: {}", dispute_msg),
                    None,
                ),
                GedankenexperimentResult::FormalContradiction(contra_msg) => LockReceipt::new(
                    LockType::OntologicalAnchor,
                    "Ontological Anchoring (Formal Contradiction)",
                    false,
                    format!("REFUTATION: {}", contra_msg),
                    None,
                ),
            }
        } else {
            LockReceipt::new(
                LockType::OntologicalAnchor,
                "Ontological Anchoring",
                true,
                "التجذير التناظري مصادق عليه بنجاح",
                None,
            )
        }
    }

    /// تنفيذ التجربة الفكرية المعزولة مع التراجع الذري الحتمي 100%
    pub fn run_gedankenexperiment(
        egraph: &mut TransactionalEGraph,
        solution: Option<&HashMap<VariableId, Rational>>,
        expr_opt: Option<&CanonicalExpr>,
    ) -> GedankenexperimentResult {
        let cp = egraph.checkpoint();

        let execution_outcome = (|| -> Result<(), EpistemicError> {
            // أ. حقن حلول المتغيرات التجريبية كعقد مؤقتة
            if let Some(sol) = solution {
                for (var, val) in sol {
                    let var_cid = egraph.add_node(ENode::Var(*var), None);
                    let val_cid = egraph.add_node(ENode::Const(val.clone()), None);
                    egraph.union(var_cid, val_cid)?;
                }
            }

            // ب. حقن التعبير الكنسي إن وجد
            if let Some(expr) = expr_opt {
                let ctx = aletheia_lattice::DimensionalContext::mathematical();
                let _expr_cid = egraph.add_expr(expr, &ctx)?;
            }

            // ج. إطلاق دورة الإغلاق التطابقي الكاملة
            egraph.rebuild()?;

            Ok(())
        })();

        // التراجع الذري الحتمي بنسبة 100% يمحو كافة آثار التجربة الفكرية من الذاكرة الحية
        egraph.rollback(cp);

        match execution_outcome {
            Ok(()) => GedankenexperimentResult::Consistent,
            Err(EpistemicError::EGraphError(aletheia_egraph::EGraphError::Lattice(
                LatticeError::ContradictoryMerge(msg),
            ))) => {
                // التقاط انهيار الفترات المعتمدة أو تصادم الأبعاد كنزاع إبستمولوجي صلب
                GedankenexperimentResult::EpistemicDispute(format!(
                    "انهيار في الفترات المعتمدة أو تصادم مع النموذج القائم: {}",
                    msg
                ))
            }
            Err(EpistemicError::EGraphError(aletheia_egraph::EGraphError::Contradiction(msg))) => {
                GedankenexperimentResult::FormalContradiction(msg)
            }
            Err(e) => GedankenexperimentResult::FormalContradiction(e.to_string()),
        }
    }

    /// تنفيذ التجربة الفكرية المعزولة مع فحص الحدود والفترات الفيزيائية عبر [min, max]
    pub fn run_boundary_gedankenexperiment(
        egraph: &mut TransactionalEGraph,
        dim_ctx: &aletheia_lattice::DimensionalContext,
        var_bounds: &[(VariableId, Rational, Rational)],
        test_points: &HashMap<VariableId, Rational>,
        expr_opt: Option<&CanonicalExpr>,
    ) -> GedankenexperimentResult {
        let cp = egraph.checkpoint();

        let execution_outcome = (|| -> Result<(), EpistemicError> {
            // أ. حقن متغيرات الفحص مع فترات الصلاحية [min, max]
            for (var, min, max) in var_bounds {
                let dim = dim_ctx
                    .get(*var)
                    .cloned()
                    .unwrap_or_else(|| aletheia_lattice::DimensionVector::dimensionless());
                let data = aletheia_lattice::LatticeData::with_bounds(
                    dim,
                    aletheia_lattice::SemanticDomain::PhysicalCore,
                    (min.clone(), max.clone()),
                );
                let _var_cid = egraph.add_node(ENode::Var(*var), Some(data));
            }

            // ب. حقن نقاط الاختبار التجريبية ومحاولة دمجها مع المتغيرات
            for (var, val) in test_points {
                let var_cid = egraph.add_node(ENode::Var(*var), None);
                let val_data = aletheia_lattice::LatticeData::with_bounds(
                    dim_ctx
                        .get(*var)
                        .cloned()
                        .unwrap_or_else(|| aletheia_lattice::DimensionVector::dimensionless()),
                    aletheia_lattice::SemanticDomain::PhysicalCore,
                    (val.clone(), val.clone()),
                );
                let val_cid = egraph.add_node(ENode::Const(val.clone()), Some(val_data));
                egraph.union(var_cid, val_cid)?;
            }

            // ج. حقن التعبير الكنسي إن وجد
            if let Some(expr) = expr_opt {
                let _expr_cid = egraph.add_expr(expr, dim_ctx)?;
            }

            // د. إطلاق دورة الإغلاق التطابقي الكاملة
            egraph.rebuild()?;

            Ok(())
        })();

        // التراجع الذري الحتمي بنسبة 100% يمحو كافة آثار التجربة الفكرية
        egraph.rollback(cp);

        match execution_outcome {
            Ok(()) => GedankenexperimentResult::Consistent,
            Err(EpistemicError::EGraphError(aletheia_egraph::EGraphError::Lattice(
                LatticeError::ContradictoryMerge(msg),
            ))) => GedankenexperimentResult::EpistemicDispute(format!(
                "انهيار في الفترات المعتمدة أو تصادم مع الحدود الفيزيائية: {}",
                msg
            )),
            Err(EpistemicError::EGraphError(aletheia_egraph::EGraphError::Contradiction(msg))) => {
                GedankenexperimentResult::FormalContradiction(msg)
            }
            Err(e) => GedankenexperimentResult::FormalContradiction(e.to_string()),
        }
    }
}
