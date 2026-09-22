use crate::eclass::EClass;
use crate::id::EClassId;
use crate::node::ENode;
use crate::union_find::UnionFind;
use aletheia_lattice::LatticeData;
use std::collections::HashMap;

/// العمليات العكسية المسجلة في مكدس التراجع الذري (Undo Operations)
#[derive(Clone, Debug)]
pub enum UndoOp {
    /// عكس دمج في Union-Find
    UnionFind {
        child: EClassId,
        parent: EClassId,
        old_parent_rank: u32,
    },
    /// عكس إنشاء فئة تكافؤ جديدة
    CreateClass {
        id: EClassId,
    },
    /// عكس إضافة عقدة لفئة
    PopClassNode {
        class_id: EClassId,
    },
    /// اقتطاع قائمة عقد فئة إلى طول سابق
    TruncateClassNodes {
        class_id: EClassId,
        old_len: usize,
    },
    /// عكس إضافة أب لفئة
    PopClassParent {
        class_id: EClassId,
    },
    /// اقتطاع قائمة آباء فئة إلى طول سابق
    TruncateClassParents {
        class_id: EClassId,
        old_len: usize,
    },
    /// عكس إدخال أو تعديل في جدول الـ Hash-Cons
    SetHashCons {
        node: ENode,
        old_val: Option<EClassId>,
    },
    /// عكس تعديل البيانات الدلالية لفئة
    SetClassData {
        class_id: EClassId,
        old_data: Box<Option<LatticeData>>,
    },
}

/// سجل العمليات العكسية ونقاط التفتيش (Undo Journal)
/// يضمن استرجاع حالة الذاكرة بالكامل بدقة البت (Bit-Exact Rollback)
#[derive(Clone, Debug, Default)]
pub struct UndoJournal {
    ops: Vec<UndoOp>,
}

impl UndoJournal {
    pub fn new() -> Self {
        Self { ops: Vec::new() }
    }

    /// أخذ نقطة تفتيش في زمن لحظي O(1)
    #[inline]
    pub fn checkpoint(&self) -> usize {
        self.ops.len()
    }

    /// تسجيل عملية عكسية في المكدس
    #[inline]
    pub fn push(&mut self, op: UndoOp) {
        self.ops.push(op);
    }

    /// عدد العمليات المسجلة حالياً
    #[inline]
    pub fn len(&self) -> usize {
        self.ops.len()
    }

    #[inline]
    pub fn is_empty(&self) -> bool {
        self.ops.is_empty()
    }

    /// تثبيت المعاملة حتى نقطة التفتيش: لا يلزم أي إجراء لأن الحالة معتمدة
    pub fn commit(&mut self, _token: usize) {
        // يمكن اختياري تفريغ العمليات القديمة لتوفير الذاكرة
    }

    /// التراجع الذري اللحظي التام حتى نقطة التفتيش
    pub fn rollback(
        &mut self,
        token: usize,
        classes: &mut HashMap<EClassId, EClass>,
        hashcons: &mut HashMap<ENode, EClassId>,
        union_find: &mut UnionFind,
    ) {
        while self.ops.len() > token {
            let op = self.ops.pop().unwrap();
            match op {
                UndoOp::UnionFind {
                    child,
                    parent,
                    old_parent_rank,
                } => {
                    union_find.rollback_union(child, parent, old_parent_rank);
                }
                UndoOp::CreateClass { id } => {
                    classes.remove(&id);
                }
                UndoOp::PopClassNode { class_id } => {
                    if let Some(class) = classes.get_mut(&class_id) {
                        class.nodes.pop();
                    }
                }
                UndoOp::TruncateClassNodes { class_id, old_len } => {
                    if let Some(class) = classes.get_mut(&class_id) {
                        class.nodes.truncate(old_len);
                    }
                }
                UndoOp::PopClassParent { class_id } => {
                    if let Some(class) = classes.get_mut(&class_id) {
                        class.parents.pop();
                    }
                }
                UndoOp::TruncateClassParents { class_id, old_len } => {
                    if let Some(class) = classes.get_mut(&class_id) {
                        class.parents.truncate(old_len);
                    }
                }
                UndoOp::SetHashCons { node, old_val } => match old_val {
                    Some(old_class) => {
                        hashcons.insert(node, old_class);
                    }
                    None => {
                        hashcons.remove(&node);
                    }
                },
                UndoOp::SetClassData {
                    class_id,
                    old_data,
                } => {
                    if let Some(class) = classes.get_mut(&class_id) {
                        class.data = *old_data;
                    }
                }
            }
        }
    }
}
