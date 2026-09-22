use crate::id::EClassId;
use aletheia_algebra::{Rational, VariableId};
use smallvec::SmallVec;
use std::fmt;

/// عقدة رياضية في فضاء الـ E-Graph (E-Node)
/// تستخدم SmallVec لتفادي الـ Heap Allocations في العمليات الثنائية
#[derive(Clone, PartialEq, Eq, Hash)]
pub enum ENode {
    Const(Rational),
    Var(VariableId),
    Add(SmallVec<[EClassId; 2]>),
    Mul(SmallVec<[EClassId; 2]>),
    Div([EClassId; 2]),
    Pow(EClassId, i32),
    Neg(EClassId),
    Custom(u32, SmallVec<[EClassId; 2]>),
}

impl ENode {
    /// استرجاع مراجع أبناء العقدة (فئات التكافؤ التابعة)
    pub fn children(&self) -> &[EClassId] {
        match self {
            ENode::Const(_) | ENode::Var(_) => &[],
            ENode::Add(ops) | ENode::Mul(ops) => ops.as_slice(),
            ENode::Div(ops) => ops.as_slice(),
            ENode::Pow(a, _) | ENode::Neg(a) => std::slice::from_ref(a),
            ENode::Custom(_, ops) => ops.as_slice(),
        }
    }

    /// استرجاع مراجع قابلة للتعديل لأبناء العقدة
    pub fn children_mut(&mut self) -> &mut [EClassId] {
        match self {
            ENode::Const(_) | ENode::Var(_) => &mut [],
            ENode::Add(ops) | ENode::Mul(ops) => ops.as_mut_slice(),
            ENode::Div(ops) => ops.as_mut_slice(),
            ENode::Pow(a, _) | ENode::Neg(a) => std::slice::from_mut(a),
            ENode::Custom(_, ops) => ops.as_mut_slice(),
        }
    }

    /// هل العقدة ورقية (بدون أبناء)
    #[inline]
    pub fn is_leaf(&self) -> bool {
        self.children().is_empty()
    }

    /// التحويل الكنسي للعقدة:
    /// 1. استبدال كل ابن بممثله الكنسي الحالي
    /// 2. الفرز الكنسي للعمليات التبادلية (Add و Mul) لضمان اتحاد a+b مع b+a تلقائياً في Hash-Cons
    pub fn canonicalize<F>(&mut self, mut get_canon: F)
    where
        F: FnMut(EClassId) -> EClassId,
    {
        match self {
            ENode::Const(_) | ENode::Var(_) => {}
            ENode::Add(ops) => {
                for id in ops.iter_mut() {
                    *id = get_canon(*id);
                }
                // الفرز الكنسي للعملية التبادلية
                ops.sort_unstable();
            }
            ENode::Mul(ops) => {
                for id in ops.iter_mut() {
                    *id = get_canon(*id);
                }
                // الفرز الكنسي للعملية التبادلية
                ops.sort_unstable();
            }
            ENode::Div(ops) => {
                ops[0] = get_canon(ops[0]);
                ops[1] = get_canon(ops[1]);
            }
            ENode::Pow(a, _) | ENode::Neg(a) => {
                *a = get_canon(*a);
            }
            ENode::Custom(_, ops) => {
                for id in ops.iter_mut() {
                    *id = get_canon(*id);
                }
            }
        }
    }
}

impl fmt::Display for ENode {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ENode::Const(c) => write!(f, "{}", c),
            ENode::Var(v) => write!(f, "{}", v),
            ENode::Add(ops) => {
                write!(f, "(+")?;
                for op in ops {
                    write!(f, " {}", op)?;
                }
                write!(f, ")")
            }
            ENode::Mul(ops) => {
                write!(f, "(*")?;
                for op in ops {
                    write!(f, " {}", op)?;
                }
                write!(f, ")")
            }
            ENode::Div(ops) => write!(f, "(/ {} {})", ops[0], ops[1]),
            ENode::Pow(a, exp) => write!(f, "(^ {} {})", a, exp),
            ENode::Neg(a) => write!(f, "(- {})", a),
            ENode::Custom(tag, ops) => {
                write!(f, "(custom#{}", tag)?;
                for op in ops {
                    write!(f, " {}", op)?;
                }
                write!(f, ")")
            }
        }
    }
}

impl fmt::Debug for ENode {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self)
    }
}
