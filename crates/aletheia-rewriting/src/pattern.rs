use crate::error::RewritingError;
use aletheia_algebra::{CanonicalExpr, Rational, VariableId};
use aletheia_egraph::{EClassId, ENode, TransactionalEGraph};
use aletheia_lattice::{DimensionalContext, LatticeData, SemanticDomain};
use smallvec::SmallVec;
use std::collections::HashMap;

/// جدول التعويضات (Substitution Map)
/// يربط كل متغير حر في النمط Wildcard(u32) بفئة تكافؤ EClassId في الـ E-Graph
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct Subst {
    bindings: HashMap<u32, EClassId>,
}

impl Subst {
    pub fn new() -> Self {
        Self {
            bindings: HashMap::new(),
        }
    }

    /// استرجاع فئة التكافؤ المرتبطة بمتغير حر
    #[inline]
    pub fn get(&self, var: u32) -> Option<EClassId> {
        self.bindings.get(&var).copied()
    }

    /// ربط متغير حر بفئة تكافؤ مع الفحص الصارم لقيود التساوي (Multi-Variable Equijoins)
    /// إذا كان المتغير مرتبطاً مسبقاً، يُشترط تطابق الفئتين كنسياً
    pub fn insert(&mut self, var: u32, id: EClassId, egraph: &TransactionalEGraph) -> bool {
        let canon_id = egraph.find(id);
        if let Some(&existing) = self.bindings.get(&var) {
            egraph.find(existing) == canon_id
        } else {
            self.bindings.insert(var, canon_id);
            true
        }
    }

    pub fn len(&self) -> usize {
        self.bindings.len()
    }

    pub fn is_empty(&self) -> bool {
        self.bindings.is_empty()
    }
}

/// لغة الأنماط الرمزية لمحرك المطابقة وإعادة الكتابة (Pattern Language)
/// تفصل دستورياً بين المتغير الحر للنمط Wildcard(u32) والمتغير الرياضي المادي LiteralVar(VariableId)
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub enum Pattern {
    /// متغير حر يطابق أي فئة تكافؤ ويُسجل في جدول التعويضات (e.g. ?x, ?y)
    Wildcard(u32),
    /// متغير رياضي أو فيزيائي محدد وحصري (Literal Symbol e.g. x0, t, r)
    LiteralVar(VariableId),
    /// ثابت عددي دقيق في حقل الأعداد النسبية Q
    Const(Rational),
    /// جمع تبادلي
    Add(Vec<Pattern>),
    /// ضرب تبادلي
    Mul(Vec<Pattern>),
    /// قسمة كسرية ثنائية [num, den]
    Div(Box<Pattern>, Box<Pattern>),
    /// قوة صحيحة (base, exp)
    Pow(Box<Pattern>, i32),
    /// نفي جبري (-inner)
    Neg(Box<Pattern>),
}

impl Pattern {
    /// دوال مساعدة لإنشاء الأنماط بسلاسة
    pub fn wildcard(id: u32) -> Self {
        Pattern::Wildcard(id)
    }

    pub fn literal_var(var: VariableId) -> Self {
        Pattern::LiteralVar(var)
    }

    pub fn constant(c: Rational) -> Self {
        Pattern::Const(c)
    }

    pub fn add(ops: Vec<Pattern>) -> Self {
        Pattern::Add(ops)
    }

    pub fn mul(ops: Vec<Pattern>) -> Self {
        Pattern::Mul(ops)
    }

    #[allow(clippy::should_implement_trait)]
    pub fn div(num: Pattern, den: Pattern) -> Self {
        Pattern::Div(Box::new(num), Box::new(den))
    }

    pub fn pow(base: Pattern, exp: i32) -> Self {
        Pattern::Pow(Box::new(base), exp)
    }

    #[allow(clippy::should_implement_trait)]
    pub fn neg(inner: Pattern) -> Self {
        Pattern::Neg(Box::new(inner))
    }

    /// تحويل شجرة التعبير الكنسي CanonicalExpr إلى نمط مادي محدد (بدون Wildcards)
    pub fn from_canonical_expr(expr: &CanonicalExpr) -> Self {
        match expr {
            CanonicalExpr::Const(c) => Pattern::Const(c.clone()),
            CanonicalExpr::Var(v) => Pattern::LiteralVar(*v),
            CanonicalExpr::Neg(inner) => Pattern::Neg(Box::new(Self::from_canonical_expr(inner))),
            CanonicalExpr::Add(ops) => {
                Pattern::Add(ops.iter().map(Self::from_canonical_expr).collect())
            }
            CanonicalExpr::Mul(ops) => {
                Pattern::Mul(ops.iter().map(Self::from_canonical_expr).collect())
            }
            CanonicalExpr::Div(num, den) => Pattern::Div(
                Box::new(Self::from_canonical_expr(num)),
                Box::new(Self::from_canonical_expr(den)),
            ),
            CanonicalExpr::Pow(base, exp) => {
                Pattern::Pow(Box::new(Self::from_canonical_expr(base)), *exp)
            }
        }
    }

    /// تحويل النمط الرمزي إلى شجرة تعبير كنسية تقديرية لاستخراج المتجه الطيفي
    pub fn to_canonical_dummy(&self) -> CanonicalExpr {
        match self {
            Pattern::Wildcard(v) => CanonicalExpr::Var(VariableId(*v)),
            Pattern::LiteralVar(v) => CanonicalExpr::Var(*v),
            Pattern::Const(c) => CanonicalExpr::Const(c.clone()),
            Pattern::Neg(inner) => CanonicalExpr::Neg(Box::new(inner.to_canonical_dummy())),
            Pattern::Add(ops) => CanonicalExpr::Add(ops.iter().map(|p| p.to_canonical_dummy()).collect()),
            Pattern::Mul(ops) => CanonicalExpr::Mul(ops.iter().map(|p| p.to_canonical_dummy()).collect()),
            Pattern::Div(num, den) => CanonicalExpr::Div(
                Box::new(num.to_canonical_dummy()),
                Box::new(den.to_canonical_dummy()),
            ),
            Pattern::Pow(base, exp) => CanonicalExpr::Pow(Box::new(base.to_canonical_dummy()), *exp),
        }
    }

    /// تجسيد النمط (RHS Instantiation) داخل الـ E-Graph استناداً إلى جدول التعويضات Subst
    /// وتمرير LatticeData الصحيحة لكل فئة مضافة
    pub fn instantiate(
        &self,
        egraph: &mut TransactionalEGraph,
        subst: &Subst,
        ctx: &DimensionalContext,
    ) -> Result<EClassId, RewritingError> {
        match self {
            Pattern::Wildcard(var_id) => subst
                .get(*var_id)
                .ok_or(RewritingError::UnboundPatternVar(*var_id)),

            Pattern::LiteralVar(v) => {
                let expr = CanonicalExpr::Var(*v);
                let id = egraph.add_expr(&expr, ctx)?;
                Ok(id)
            }

            Pattern::Const(c) => {
                let expr = CanonicalExpr::Const(c.clone());
                let id = egraph.add_expr(&expr, ctx)?;
                Ok(id)
            }

            Pattern::Neg(inner) => {
                let inner_id = inner.instantiate(egraph, subst, ctx)?;
                let canon_inner = egraph.find(inner_id);
                let inner_data = egraph
                    .classes
                    .get(&canon_inner)
                    .and_then(|c| c.data.clone());
                let node = ENode::Neg(canon_inner);
                Ok(egraph.add_node(node, inner_data))
            }

            Pattern::Add(operands) => {
                let mut ids = SmallVec::with_capacity(operands.len());
                for op in operands {
                    ids.push(op.instantiate(egraph, subst, ctx)?);
                }
                // التحقق الدلالي للأبعاد إن توفرت
                let mut data = None;
                for &id in &ids {
                    let canon = egraph.find(id);
                    if let Some(c_data) = egraph.classes.get(&canon).and_then(|c| c.data.clone()) {
                        data = Some(c_data);
                        break;
                    }
                }
                let node = ENode::Add(ids);
                Ok(egraph.add_node(node, data))
            }

            Pattern::Mul(operands) => {
                let mut ids = SmallVec::with_capacity(operands.len());
                let mut combined_dim = None;
                for op in operands {
                    let id = op.instantiate(egraph, subst, ctx)?;
                    ids.push(id);
                    let canon = egraph.find(id);
                    if let Some(c_data) = egraph.classes.get(&canon).and_then(|c| c.data.clone()) {
                        combined_dim = match combined_dim {
                            Some(d) => Some(&d + &c_data.dim),
                            None => Some(c_data.dim.clone()),
                        };
                    }
                }
                let data = combined_dim.map(|d| {
                    let domain = if d.is_dimensionless() {
                        SemanticDomain::PureMathematics
                    } else {
                        SemanticDomain::PhysicalCore
                    };
                    LatticeData::new(d, domain)
                });
                let node = ENode::Mul(ids);
                Ok(egraph.add_node(node, data))
            }

            Pattern::Div(num, den) => {
                let num_id = num.instantiate(egraph, subst, ctx)?;
                let den_id = den.instantiate(egraph, subst, ctx)?;
                let canon_num = egraph.find(num_id);
                let canon_den = egraph.find(den_id);

                let num_data = egraph
                    .classes
                    .get(&canon_num)
                    .and_then(|c| c.data.clone());
                let den_data = egraph
                    .classes
                    .get(&canon_den)
                    .and_then(|c| c.data.clone());

                let data = match (num_data, den_data) {
                    (Some(nd), Some(dd)) => {
                        let dim = &nd.dim - &dd.dim;
                        let domain = if dim.is_dimensionless() {
                            SemanticDomain::PureMathematics
                        } else {
                            SemanticDomain::PhysicalCore
                        };
                        Some(LatticeData::new(dim, domain))
                    }
                    (Some(nd), None) => Some(nd),
                    _ => None,
                };

                let node = ENode::Div([canon_num, canon_den]);
                Ok(egraph.add_node(node, data))
            }

            Pattern::Pow(base, exp) => {
                let base_id = base.instantiate(egraph, subst, ctx)?;
                let canon_base = egraph.find(base_id);
                let base_data = egraph
                    .classes
                    .get(&canon_base)
                    .and_then(|c| c.data.clone());

                let data = base_data.map(|bd| {
                    let exp_rat = Rational::from_i64(*exp as i64);
                    let dim = bd.dim.scale(&exp_rat);
                    let domain = if dim.is_dimensionless() {
                        SemanticDomain::PureMathematics
                    } else {
                        SemanticDomain::PhysicalCore
                    };
                    LatticeData::new(dim, domain)
                });

                let node = ENode::Pow(canon_base, *exp);
                Ok(egraph.add_node(node, data))
            }
        }
    }
}
