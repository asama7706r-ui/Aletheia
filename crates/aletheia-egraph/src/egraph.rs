use crate::eclass::EClass;
use crate::error::EGraphError;
use crate::id::EClassId;
use crate::node::ENode;
use crate::undo::{UndoJournal, UndoOp};
use crate::union_find::UnionFind;
use aletheia_algebra::CanonicalExpr;
use aletheia_lattice::{DimensionalContext, LatticeData, SemanticDomain, SemanticGuard};
use smallvec::SmallVec;
use std::collections::HashMap;

/// بنية الـ E-Graph المعاملاتية الصرفة (Transactional E-Graph Substrate)
/// مفاعل استدلالي ذري يدعم طرح الفرضيات والتراجع اللحظي التام (Bit-Exact Rollback)
#[derive(Clone, Debug, Default)]
pub struct TransactionalEGraph {
    pub classes: HashMap<EClassId, EClass>,
    pub hashcons: HashMap<ENode, EClassId>,
    pub union_find: UnionFind,
    pub undo_journal: UndoJournal,
    pub worklist: Vec<EClassId>,
}

impl TransactionalEGraph {
    pub fn new() -> Self {
        Self {
            classes: HashMap::new(),
            hashcons: HashMap::new(),
            union_find: UnionFind::new(),
            undo_journal: UndoJournal::new(),
            worklist: Vec::new(),
        }
    }

    /// استعلام الممثل الكنسي (Read-Only Find O(log N) خفيف وسريع)
    #[inline]
    pub fn find(&self, id: EClassId) -> EClassId {
        self.union_find.find(id)
    }

    /// التحويل الكنسي للعقدة
    #[inline]
    pub fn canonicalize_node(&self, node: &mut ENode) {
        node.canonicalize(|id| self.find(id));
    }

    /// أخذ نقطة تفتيش في زمن لحظي O(1)
    #[inline]
    pub fn checkpoint(&self) -> usize {
        self.undo_journal.checkpoint()
    }

    /// التراجع الذري اللحظي التام إلى نقطة التفتيش
    pub fn rollback(&mut self, token: usize) {
        self.undo_journal.rollback(
            token,
            &mut self.classes,
            &mut self.hashcons,
            &mut self.union_find,
        );
        self.worklist.clear();
    }

    /// تثبيت المعاملة
    pub fn commit(&mut self, token: usize) {
        self.undo_journal.commit(token);
    }

    /// إضافة عقدة رياضية جديدة مع تسجيل العمليات في سجل التراجع
    pub fn add_node(&mut self, mut node: ENode, data: Option<LatticeData>) -> EClassId {
        self.canonicalize_node(&mut node);

        // إذا كانت العقدة موجودة مسبقاً في جدول الـ Hash-Cons، نعيد فئتها الكنسية فوراً
        if let Some(&id) = self.hashcons.get(&node) {
            let canon = self.find(id);
            // إذا كان لدينا بيانات دلالية جديدة ولم تكن موجودة في الفئة، ندمجها
            if let Some(new_data) = data {
                let old_data = self.classes.get(&canon).and_then(|c| c.data.clone());
                if old_data.is_none() {
                    self.undo_journal.push(UndoOp::SetClassData {
                        class_id: canon,
                        old_data: Box::new(old_data),
                    });
                    if let Some(c) = self.classes.get_mut(&canon) {
                        c.data = Some(new_data);
                    }
                }
            }
            return canon;
        }

        // إنشاء فئة تكافؤ جديدة
        let new_id = self.union_find.make_set();
        self.undo_journal.push(UndoOp::CreateClass { id: new_id });

        let mut class = EClass::new(new_id, data);
        class.nodes.push(node.clone());
        self.undo_journal.push(UndoOp::PopClassNode { class_id: new_id });

        // تسجيل مؤشرات الآباء في الفئات التابعة للأبناء
        for &child in node.children() {
            let canon_child = self.find(child);
            if let Some(c) = self.classes.get_mut(&canon_child) {
                c.parents.push((node.clone(), new_id));
                self.undo_journal.push(UndoOp::PopClassParent { class_id: canon_child });
            }
        }

        // إدراج العقدة في جدول الـ Hash-Cons
        self.hashcons.insert(node.clone(), new_id);
        self.undo_journal.push(UndoOp::SetHashCons {
            node,
            old_val: None,
        });

        self.classes.insert(new_id, class);
        new_id
    }

    /// تحويل وإدخال شجرة تعبيرات كنسية CanonicalExpr إلى الـ E-Graph مع التحقق الدلالي وتمرير LatticeData لكل تعبير فرعي
    pub fn add_expr(
        &mut self,
        expr: &CanonicalExpr,
        ctx: &DimensionalContext,
    ) -> Result<EClassId, EGraphError> {
        self.add_expr_internal(expr, ctx)
    }

    fn add_expr_internal(
        &mut self,
        expr: &CanonicalExpr,
        ctx: &DimensionalContext,
    ) -> Result<EClassId, EGraphError> {
        // حساب وتمرير LatticeData لكل فرع وتعبير فرعي بدلاً من None لحماية المتغيرات من الدمج البُعدي الخاطئ
        let dim = SemanticGuard::infer_dimension(expr, ctx)?;
        let domain = if dim.is_dimensionless() {
            SemanticDomain::PureMathematics
        } else {
            SemanticDomain::PhysicalCore
        };
        let lattice_data = LatticeData::new(dim, domain);

        match expr {
            CanonicalExpr::Const(c) => Ok(self.add_node(ENode::Const(c.clone()), Some(lattice_data))),
            CanonicalExpr::Var(v) => Ok(self.add_node(ENode::Var(*v), Some(lattice_data))),
            CanonicalExpr::Neg(inner) => {
                let inner_id = self.add_expr_internal(inner, ctx)?;
                Ok(self.add_node(ENode::Neg(inner_id), Some(lattice_data)))
            }
            CanonicalExpr::Add(operands) => {
                let mut ids = SmallVec::with_capacity(operands.len());
                for op in operands {
                    ids.push(self.add_expr_internal(op, ctx)?);
                }
                Ok(self.add_node(ENode::Add(ids), Some(lattice_data)))
            }
            CanonicalExpr::Mul(operands) => {
                let mut ids = SmallVec::with_capacity(operands.len());
                for op in operands {
                    ids.push(self.add_expr_internal(op, ctx)?);
                }
                Ok(self.add_node(ENode::Mul(ids), Some(lattice_data)))
            }
            CanonicalExpr::Div(num, den) => {
                let num_id = self.add_expr_internal(num, ctx)?;
                let den_id = self.add_expr_internal(den, ctx)?;
                Ok(self.add_node(ENode::Div([num_id, den_id]), Some(lattice_data)))
            }
            CanonicalExpr::Pow(base, exp) => {
                let base_id = self.add_expr_internal(base, ctx)?;
                Ok(self.add_node(ENode::Pow(base_id, *exp), Some(lattice_data)))
            }
        }
    }

    /// البحث عن فئة التكافؤ الكنسية لتعبير دون تعديل الشجرة (Read-Only Expression Lookup)
    pub fn lookup_expr(&self, expr: &CanonicalExpr) -> Option<EClassId> {
        self.lookup_expr_internal(expr)
    }

    fn lookup_expr_internal(&self, expr: &CanonicalExpr) -> Option<EClassId> {
        let node = match expr {
            CanonicalExpr::Const(c) => ENode::Const(c.clone()),
            CanonicalExpr::Var(v) => ENode::Var(*v),
            CanonicalExpr::Neg(inner) => {
                let inner_id = self.lookup_expr_internal(inner)?;
                ENode::Neg(self.find(inner_id))
            }
            CanonicalExpr::Add(operands) => {
                let mut ids = SmallVec::with_capacity(operands.len());
                for op in operands {
                    ids.push(self.find(self.lookup_expr_internal(op)?));
                }
                ENode::Add(ids)
            }
            CanonicalExpr::Mul(operands) => {
                let mut ids = SmallVec::with_capacity(operands.len());
                for op in operands {
                    ids.push(self.find(self.lookup_expr_internal(op)?));
                }
                ENode::Mul(ids)
            }
            CanonicalExpr::Div(num, den) => {
                let num_id = self.find(self.lookup_expr_internal(num)?);
                let den_id = self.find(self.lookup_expr_internal(den)?);
                ENode::Div([num_id, den_id])
            }
            CanonicalExpr::Pow(base, exp) => {
                let base_id = self.find(self.lookup_expr_internal(base)?);
                ENode::Pow(base_id, *exp)
            }
        };

        let mut canon_node = node;
        self.canonicalize_node(&mut canon_node);
        self.hashcons.get(&canon_node).map(|&id| self.find(id))
    }

    /// دمج فئتي تكافؤ (Union) مع فحص التكامل الدلالي LatticeData
    /// إذا حدث تعارض بُعدي، يطلق خطأ LatticeError لإطلاق التراجع الذري فوراً
    pub fn union(&mut self, id1: EClassId, id2: EClassId) -> Result<bool, EGraphError> {
        let r1 = self.find(id1);
        let r2 = self.find(id2);

        if r1 == r2 {
            return Ok(false);
        }

        // دمج الشجرتين في UnionFind
        let (child, parent, old_rank) = self.union_find.union(r1, r2).unwrap();
        self.undo_journal.push(UndoOp::UnionFind {
            child,
            parent,
            old_parent_rank: old_rank,
        });

        // فحص ودمج البيانات الدلالية LatticeData
        let child_data = self.classes.get(&child).and_then(|c| c.data.clone());
        let parent_data = self.classes.get(&parent).and_then(|c| c.data.clone());

        let merged_data = match (parent_data.clone(), child_data) {
            (Some(pd), Some(cd)) => {
                // إذا كان هناك تعارض بُعدي، دالة merge ستطلق ContradictoryMerge ويفشل الاستدعاء
                let m = pd.merge(&cd)?;
                Some(m)
            }
            (Some(d), None) | (None, Some(d)) => Some(d),
            (None, None) => None,
        };

        if merged_data != parent_data {
            self.undo_journal.push(UndoOp::SetClassData {
                class_id: parent,
                old_data: Box::new(parent_data),
            });
            if let Some(p_class) = self.classes.get_mut(&parent) {
                p_class.data = merged_data;
            }
        }

        // دمج العقد وقوائم الآباء من child إلى parent لدفع شلال إغلاق التطابق صعوداً
        let (child_nodes, child_parents) = if let Some(c) = self.classes.get(&child) {
            (c.nodes.clone(), c.parents.clone())
        } else {
            (Vec::new(), Vec::new())
        };

        if let Some(p_class) = self.classes.get_mut(&parent) {
            let old_nodes_len = p_class.nodes.len();
            p_class.nodes.extend(child_nodes);
            self.undo_journal.push(UndoOp::TruncateClassNodes {
                class_id: parent,
                old_len: old_nodes_len,
            });

            let old_parents_len = p_class.parents.len();
            p_class.parents.extend(child_parents);
            self.undo_journal.push(UndoOp::TruncateClassParents {
                class_id: parent,
                old_len: old_parents_len,
            });
        }

        self.worklist.push(parent);
        Ok(true)
    }

    /// دورة إغلاق التطابق الكنسية (Congruence Closure Rebuild Cycle)
    /// برهان حتمية الانتهاء O(N * alpha(N)) حتى نقطة الثبات Fixed Point
    pub fn rebuild(&mut self) -> Result<usize, EGraphError> {
        let mut total_unions = 0;

        while let Some(class_id) = self.worklist.pop() {
            let canon_class = self.find(class_id);

            // استخراج قائمة الآباء للتحديث
            let raw_parents = match self.classes.get_mut(&canon_class) {
                Some(c) => std::mem::take(&mut c.parents),
                None => continue,
            };

            let mut new_parents = Vec::with_capacity(raw_parents.len());

            for (mut node, parent_id) in raw_parents {
                // إزالة التجزئة القديمة
                self.hashcons.remove(&node);
                self.undo_journal.push(UndoOp::SetHashCons {
                    node: node.clone(),
                    old_val: Some(parent_id),
                });

                // تحديث كنسي للعقدة
                self.canonicalize_node(&mut node);
                let canon_parent = self.find(parent_id);

                // فحص ما إذا كانت العقدة بعد التحديث أصبحت مطابقة لعقدة موجودة في الـ Hash-Cons
                if let Some(&existing_class) = self.hashcons.get(&node) {
                    let canon_existing = self.find(existing_class);
                    if canon_existing != canon_parent && self.union(canon_existing, canon_parent)? {
                        total_unions += 1;
                    }
                } else {
                    self.hashcons.insert(node.clone(), canon_parent);
                    self.undo_journal.push(UndoOp::SetHashCons {
                        node: node.clone(),
                        old_val: None,
                    });
                }

                new_parents.push((node, canon_parent));
            }

            if let Some(c) = self.classes.get_mut(&canon_class) {
                c.parents = new_parents;
            }
        }

        Ok(total_unions)
    }

    /// استخراج عدد فئات التكافؤ النشطة
    pub fn class_count(&self) -> usize {
        self.classes.len()
    }

    /// استخراج عدد العقد الإجمالي
    pub fn node_count(&self) -> usize {
        self.hashcons.len()
    }

    /// مكرر لجميع معرفات فئات التكافؤ النشطة
    pub fn class_ids(&self) -> impl Iterator<Item = EClassId> + '_ {
        self.classes.keys().copied()
    }

    /// استرجاع مرجع لفئة التكافؤ باستخدام معرفها أو ممثلها الكنسي
    pub fn get_class(&self, id: EClassId) -> Option<&EClass> {
        let canon = self.find(id);
        self.classes.get(&canon)
    }
}
