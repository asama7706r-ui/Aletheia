use aletheia_algebra::Rational;
use std::cmp::Ordering;
use std::collections::{BinaryHeap, HashMap, HashSet};

/// خطوة اشتقاق أو تحويل واحدة في برهان أوكام
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct OccamProofStep {
    pub source_class: u32,
    pub target_class: u32,
    pub rule_name: String,
    pub coupling_scale: Rational,
    pub step_cost: Rational,
}

/// بيان الاشتقاق البرهاني الأصغري (Minimal Proof DAG)
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct OccamProofDag {
    pub source_class: u32,
    pub target_class: u32,
    pub steps: Vec<OccamProofStep>,
    pub cumulative_coupling: Rational,
    pub total_cost: Rational,
}

#[derive(Clone, Eq, PartialEq)]
struct DijkstraState {
    cost: Rational,
    class_id: u32,
}

impl Ord for DijkstraState {
    fn cmp(&self, other: &Self) -> Ordering {
        // ترتيب عكسي لاستخدام BinaryHeap كـ Min-Heap
        other.cost.partial_cmp(&self.cost).unwrap_or(Ordering::Equal)
    }
}

impl PartialOrd for DijkstraState {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

/// حافة انتقال موجهة في بيان الـ E-Graph
#[derive(Clone, Debug)]
struct HyperEdge {
    target: u32,
    rule_name: String,
    coupling_scale: Rational,
    cost: Rational,
}

/// مستخلص براهين أوكام عبر البيان الفائق للـ E-Graph في فضاء Q الصرف
#[derive(Clone, Debug, Default)]
pub struct OccamHypergraphExtractor {
    adjacency: HashMap<u32, Vec<HyperEdge>>,
}

impl OccamHypergraphExtractor {
    pub fn new() -> Self {
        Self {
            adjacency: HashMap::new(),
        }
    }

    /// إضافة انتقال أو تطبيق قاعدة إعادة كتابة / جسر اقتران بين صنفين
    pub fn add_transition(
        &mut self,
        source: u32,
        target: u32,
        rule_name: impl Into<String>,
        coupling_scale: Rational,
        cost: Rational,
    ) {
        let edge = HyperEdge {
            target,
            rule_name: rule_name.into(),
            coupling_scale: coupling_scale.clone(),
            cost: cost.clone(),
        };
        self.adjacency.entry(source).or_default().push(edge);

        // إذا كان التحويل عكوساً وبثابت اقتران غير صفري، نسجل الاتجاه المعاكس
        if !coupling_scale.is_zero() {
            let inv_scale = Rational::one() / coupling_scale;
            let rev_edge = HyperEdge {
                target: source,
                rule_name: format!("inv_{}", self.adjacency[&source].last().unwrap().rule_name),
                coupling_scale: inv_scale,
                cost,
            };
            self.adjacency.entry(target).or_default().push(rev_edge);
        }
    }

    /// استخراج مسار الاشتقاق الأقل كلفة (Minimal Proof DAG) باستخدام خوارزمية ديكسترا الكسرية
    pub fn extract_minimal_proof(&self, source: u32, target: u32) -> Option<OccamProofDag> {
        if source == target {
            return Some(OccamProofDag {
                source_class: source,
                target_class: target,
                steps: Vec::new(),
                cumulative_coupling: Rational::one(),
                total_cost: Rational::zero(),
            });
        }

        let mut dist: HashMap<u32, Rational> = HashMap::new();
        let mut prev: HashMap<u32, (u32, HyperEdge)> = HashMap::new();
        let mut heap = BinaryHeap::new();
        let mut visited = HashSet::new();

        dist.insert(source, Rational::zero());
        heap.push(DijkstraState {
            cost: Rational::zero(),
            class_id: source,
        });

        while let Some(DijkstraState { cost, class_id }) = heap.pop() {
            if class_id == target {
                break;
            }

            if visited.contains(&class_id) {
                continue;
            }
            visited.insert(class_id);

            if let Some(edges) = self.adjacency.get(&class_id) {
                for edge in edges {
                    if visited.contains(&edge.target) {
                        continue;
                    }

                    let next_cost = cost.clone() + edge.cost.clone();
                    let is_shorter = match dist.get(&edge.target) {
                        None => true,
                        Some(current_best) => &next_cost < current_best,
                    };

                    if is_shorter {
                        dist.insert(edge.target, next_cost.clone());
                        prev.insert(edge.target, (class_id, edge.clone()));
                        heap.push(DijkstraState {
                            cost: next_cost,
                            class_id: edge.target,
                        });
                    }
                }
            }
        }

        // إذا لم نصل إلى الهدف
        if !prev.contains_key(&target) {
            return None;
        }

        // إعادة تشكيل المسار والخطوات من الهدف إلى المصدر
        let mut steps = Vec::new();
        let mut curr = target;
        let mut total_coupling = Rational::one();
        let mut total_cost = Rational::zero();

        while curr != source {
            let (p_node, edge) = prev.get(&curr)?.clone();
            total_coupling *= edge.coupling_scale.clone();
            total_cost += edge.cost.clone();

            steps.push(OccamProofStep {
                source_class: p_node,
                target_class: curr,
                rule_name: edge.rule_name,
                coupling_scale: edge.coupling_scale,
                step_cost: edge.cost,
            });

            curr = p_node;
        }

        steps.reverse();

        Some(OccamProofDag {
            source_class: source,
            target_class: target,
            steps,
            cumulative_coupling: total_coupling,
            total_cost,
        })
    }
}
