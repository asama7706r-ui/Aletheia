use crate::egraph::TransactionalEGraph;
use crate::id::EClassId;
use crate::node::ENode;
use aletheia_algebra::VariableId;
use aletheia_lattice::LatticeData;
use std::collections::HashMap;

/// عقدة شبحية افتراضية في معاملة تخمينية معزولة (Virtual Ghost Node - المحور 4 القسم 6)
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct GhostNode {
    pub ghost_id: u32,
    pub variable_id: VariableId,
    pub class_id: EClassId,
    pub lattice_data: Option<LatticeData>,
    pub is_materialized: bool,
}

/// مدير العقد الشبحية الافتراضية للتعامل مع المفاهيم والوسطاء الفيزيائيين المفقودين
#[derive(Clone, Debug)]
pub struct GhostNodeManager {
    next_ghost_id: u32,
    active_ghosts: HashMap<u32, GhostNode>,
}

impl Default for GhostNodeManager {
    fn default() -> Self {
        Self::new()
    }
}

impl GhostNodeManager {
    pub const GHOST_VAR_OFFSET: u32 = 900_000;

    pub fn new() -> Self {
        Self {
            next_ghost_id: 1,
            active_ghosts: HashMap::new(),
        }
    }

    /// توليد عقدة شبحية افتراضية مقيدة بتوقيع بعدي داخل الـ E-Graph
    pub fn spawn_ghost(
        &mut self,
        egraph: &mut TransactionalEGraph,
        lattice_data: Option<LatticeData>,
    ) -> GhostNode {
        let ghost_id = self.next_ghost_id;
        self.next_ghost_id += 1;

        let var_id = VariableId(Self::GHOST_VAR_OFFSET + ghost_id);
        let node = ENode::Var(var_id);
        let class_id = egraph.add_node(node, lattice_data.clone());

        let ghost = GhostNode {
            ghost_id,
            variable_id: var_id,
            class_id,
            lattice_data,
            is_materialized: false,
        };

        self.active_ghosts.insert(ghost_id, ghost.clone());
        ghost
    }

    /// ترقية وتثبيت العقدة الشبحية بعد إغلاق فضاء العجز بنجاح
    pub fn materialize_ghost(&mut self, ghost_id: u32) -> Option<&GhostNode> {
        if let Some(ghost) = self.active_ghosts.get_mut(&ghost_id) {
            ghost.is_materialized = true;
            Some(ghost)
        } else {
            None
        }
    }

    /// استرجاع العقدة الشبحية
    pub fn get_ghost(&self, ghost_id: u32) -> Option<&GhostNode> {
        self.active_ghosts.get(&ghost_id)
    }

    /// التحقق هل المتغير هو عقدة شبحية
    pub fn is_ghost_variable(var: VariableId) -> bool {
        var.0 >= Self::GHOST_VAR_OFFSET
    }

    /// عدد العقد الشبحية النشطة
    pub fn active_count(&self) -> usize {
        self.active_ghosts.len()
    }
}
