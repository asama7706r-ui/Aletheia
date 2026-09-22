use crate::correlation_hypergraph::{CorrelationHypergraph, HyperedgeKind};
use crate::error::YonedaError;
use crate::linear_rref::LinearRREFEngine;
use aletheia_algebra::Rational;
use aletheia_lattice::DimensionVector;

/// نتيجة دورة دمج النيوترينو للفرضيات المتكافلة
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct NeutrinoConsolidationResult {
    /// هل تم إغلاق فضاء الإلغاء بالكامل (dof -> 0) وتحرير الفرضيات؟
    pub is_resolved: bool,
    /// الرتبة التضافرية المشتركة بعد قفزة الرتبة
    pub joint_rank: usize,
    /// درجات الحرية الصافية المتبقية ككسر نسبي في Q
    pub remaining_dof: Rational,
    /// الفرضيات المحررة التي انغلقت مجاهيلها المشتركة
    pub freed_records: Vec<[u8; 32]>,
    /// الحل الحتمي المستخلص
    pub joint_solution: Option<Vec<Rational>>,
    /// الثابت البعدي المكتشف ذاتياً إن تم الاستنباط دون مرشحات مسبقة
    pub discovered_carrier_dim: Option<DimensionVector>,
}

/// منسق دورة دمج النيوترينو (The Neutrino Consolidation Cycle)
pub struct NeutrinoConsolidator;

impl NeutrinoConsolidator {
    /// تشغيل دورة الدمج على حافة فائقة تضم فرضيتين أو أكثر في مخطط الارتباط
    pub fn consolidate_hyperedge(
        graph: &mut CorrelationHypergraph,
        hyperedge_id: &[u8; 32],
        candidate_bases: &[DimensionVector],
    ) -> Result<NeutrinoConsolidationResult, YonedaError> {
        let hedge = match graph.hyperedges.get(hyperedge_id) {
            Some(h) if h.members.len() >= 2 => h.clone(),
            _ => {
                return Ok(NeutrinoConsolidationResult {
                    is_resolved: false,
                    joint_rank: 0,
                    remaining_dof: Rational::one(),
                    freed_records: Vec::new(),
                    joint_solution: None,
                    discovered_carrier_dim: None,
                });
            }
        };

        // جمع متجهات العجز البعدي للفرضيات المشتركة في الحافة الفائقة
        let mut member_deficits = Vec::new();
        for member_id in &hedge.members {
            if let Some(record) = graph.records.get(member_id) {
                member_deficits.push(record.shadow.dim_deficit.clone());
            }
        }

        if member_deficits.is_empty() {
            return Ok(NeutrinoConsolidationResult {
                is_resolved: false,
                joint_rank: 0,
                remaining_dof: Rational::one(),
                freed_records: Vec::new(),
                joint_solution: None,
                discovered_carrier_dim: None,
            });
        }

        // تحديد القواعد المرشحة: إما الممررة صراحة أو المستنبطة ذاتياً من الحافة الفائقة (Autonomous Carrier Discovery)
        let (effective_bases, discovered_carrier_dim) = if !candidate_bases.is_empty() {
            (candidate_bases.to_vec(), None)
        } else {
            let carrier = match &hedge.kind {
                HyperedgeKind::HomologousDeficit(dim) => Some(*dim.clone()),
                HyperedgeKind::CollinearDeficit(primitive) => Some(*primitive.clone()),
                _ => member_deficits.first().cloned(),
            };
            let bases = carrier.as_ref().map(|c| vec![c.clone()]).unwrap_or_default();
            (bases, carrier)
        };

        // بناء مصفوفة القيود المشتركة المدمجة:
        // كل عجز بعدي يشكل مجموعة قيود متزامنة، مما يرفع الرتبة المشتركة Rank_joint >= max(Rank_1, Rank_2)
        // دمج العجوزات التراكمية في فضاء الشبكيات
        let mut joint_deficit = DimensionVector::dimensionless();
        for d in &member_deficits {
            joint_deficit = &joint_deficit + d;
        }

        let linear_res = LinearRREFEngine::solve_linear_system(&effective_bases, &joint_deficit);

        let is_resolved = linear_res.is_consistent && linear_res.dof.is_zero();
        let freed_records = if is_resolved {
            // تحديث درجات الحرية للفرضيات المتكافلة وتحريرها
            for member_id in &hedge.members {
                if let Some(record) = graph.records.get_mut(member_id) {
                    record.remaining_dof = Rational::zero();
                }
            }
            hedge.members.clone()
        } else {
            // إذا لم تنغلق بالكامل، تحديث dof المنكمش
            for member_id in &hedge.members {
                if let Some(record) = graph.records.get_mut(member_id) {
                    record.remaining_dof = linear_res.dof.clone();
                }
            }
            Vec::new()
        };

        Ok(NeutrinoConsolidationResult {
            is_resolved,
            joint_rank: linear_res.rank,
            remaining_dof: linear_res.dof,
            freed_records,
            joint_solution: linear_res.particular_solution,
            discovered_carrier_dim,
        })
    }

    /// دمج الحافة الفائقة ذاتياً دون أي توجيه أو مرشحات مسبقة (Autonomous Invariant Discovery)
    pub fn discover_and_consolidate(
        graph: &mut CorrelationHypergraph,
        hyperedge_id: &[u8; 32],
    ) -> Result<NeutrinoConsolidationResult, YonedaError> {
        Self::consolidate_hyperedge(graph, hyperedge_id, &[])
    }
}
