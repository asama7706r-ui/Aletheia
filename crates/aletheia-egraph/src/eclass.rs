use crate::id::EClassId;
use crate::node::ENode;
use aletheia_lattice::LatticeData;

/// فئة التكافؤ الكنسية في الـ E-Graph (E-Class)
/// تحتوي على كل العقد الرياضية المتكافئة، وقائمة الآباء، والبيانات الدلالية الصرفة (LatticeData)
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct EClass {
    pub id: EClassId,
    pub nodes: Vec<ENode>,
    pub parents: Vec<(ENode, EClassId)>,
    pub data: Option<LatticeData>,
}

impl EClass {
    pub fn new(id: EClassId, data: Option<LatticeData>) -> Self {
        Self {
            id,
            nodes: Vec::new(),
            parents: Vec::new(),
            data,
        }
    }

    /// هل الفئة تحوي عقدة معينة
    pub fn contains_node(&self, node: &ENode) -> bool {
        self.nodes.contains(node)
    }
}
