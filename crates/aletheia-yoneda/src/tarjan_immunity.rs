use std::collections::HashSet;

/// تمثيل طوبولوجي للرسم البياني المعرفي لحساب نقاط التمفصل والجسور
#[derive(Clone, Debug, Default)]
pub struct KnowledgeGraph {
    pub num_nodes: usize,
    /// قائمة التجاور: adj[u] = Vec<(v, edge_index)>
    pub adj: Vec<Vec<(usize, usize)>>,
    /// قائمة الحواف: edges[edge_index] = (u, v)
    pub edges: Vec<(usize, usize)>,
}

impl KnowledgeGraph {
    pub fn new(num_nodes: usize) -> Self {
        Self {
            num_nodes,
            adj: vec![Vec::new(); num_nodes],
            edges: Vec::new(),
        }
    }

    /// إضافة حافة غير موجهة تمثل فرضية أو جسراً بين مجالين
    pub fn add_edge(&mut self, u: usize, v: usize) -> usize {
        let edge_idx = self.edges.len();
        self.edges.push((u, v));
        if u < self.num_nodes && v < self.num_nodes {
            self.adj[u].push((v, edge_idx));
            self.adj[v].push((u, edge_idx));
        }
        edge_idx
    }
}

/// كاشف الجسور الطوبولوجية وفق خوارزمية تارجان الخطية في O(V + E)
/// يمنح «حصانة الجسر» للفرضيات التي يؤدي حذفها لتمزيق الاتصال بين المجالات المعرفية (Δβ_0 > 0)
pub struct TarjanBridgeDetector;

impl TarjanBridgeDetector {
    /// اكتشاف كافة الحواف التي تمثل جسوراً طوبولوجية في الرسم البياني
    pub fn find_all_bridges(graph: &KnowledgeGraph) -> HashSet<usize> {
        let n = graph.num_nodes;
        let mut visited = vec![false; n];
        let mut tin = vec![0; n];
        let mut low = vec![0; n];
        let mut timer = 0;
        let mut bridges = HashSet::new();

        for i in 0..n {
            if !visited[i] {
                Self::dfs(
                    i,
                    None,
                    &graph.adj,
                    &mut visited,
                    &mut tin,
                    &mut low,
                    &mut timer,
                    &mut bridges,
                );
            }
        }

        bridges
    }

    /// فحص ما إذا كانت حافة معينة تملك حصانة الجسر الطوبولوجي
    pub fn has_bridge_immunity(graph: &KnowledgeGraph, edge_idx: usize) -> bool {
        let bridges = Self::find_all_bridges(graph);
        bridges.contains(&edge_idx)
    }

    #[allow(clippy::too_many_arguments)]
    fn dfs(
        u: usize,
        p_edge: Option<usize>,
        adj: &[Vec<(usize, usize)>],
        visited: &mut [bool],
        tin: &mut [usize],
        low: &mut [usize],
        timer: &mut usize,
        bridges: &mut HashSet<usize>,
    ) {
        visited[u] = true;
        *timer += 1;
        tin[u] = *timer;
        low[u] = *timer;

        for &(v, edge_idx) in &adj[u] {
            if Some(edge_idx) == p_edge {
                continue;
            }

            if visited[v] {
                low[u] = low[u].min(tin[v]);
            } else {
                Self::dfs(
                    v,
                    Some(edge_idx),
                    adj,
                    visited,
                    tin,
                    low,
                    timer,
                    bridges,
                );
                low[u] = low[u].min(low[v]);
                // شرط تارجان الكلاسيكي الصارم للجسر: low[to] > tin[from]
                if low[v] > tin[u] {
                    bridges.insert(edge_idx);
                }
            }
        }
    }
}
