use crate::correlation_hypergraph::CorrelationHypergraph;
use crate::quarantine_buffer::LatentBuffer;
use aletheia_lattice::DimensionVector;

/// أقصى عمر مسموح به للفرضية في الحجر قبل تحويلها للخمول المؤقت إن لم تكن جسراً محصناً
pub const DEFAULT_MAX_SATURATION_AGE: usize = 10;

/// أحداث التحول المعرفي والتوسع في شبكة المعرفة
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum GraphMutationEvent {
    /// اكتشاف قانون أو جسر جديد يربط مجالات
    NewLawDiscovered { law_id: String },
    /// توسع بعدي في فضاء الشبكيات Q^N -> Q^(N+1)
    DimensionalExpansion { added_dimension_index: usize },
    /// حل عجز فرضية متكافلة
    ConsolidationOccurred { resolved_record_id: [u8; 32] },
}

/// منسق الخمول المرحلي والبعث الحتمي (Dormancy & Deterministic Resurrection)
pub struct DormancyManager;

impl DormancyManager {
    /// فحص الفرضيات الراكدة وتحويلها إلى خمول مؤقت ما لم تكن تمتلك حصانة الجسر
    pub fn apply_transient_dormancy(
        buffer: &mut LatentBuffer,
        max_age: usize,
        protected_bridge_records: &[[u8; 32]],
    ) -> usize {
        let mut newly_dormant = 0;
        for record in buffer.records_mut() {
            if !record.is_dormant
                && record.saturation_age >= max_age
                && !protected_bridge_records.contains(&record.record_id)
            {
                record.set_dormant(true);
                newly_dormant += 1;
            }
        }
        newly_dormant
    }

    /// بروتوكول البعث الحتمي عند حدوث أي تحول معرفي (Paradigm Shift)
    /// تسقط أختام الخمول المؤقتة وتُستدعى الفرضيات النائمة لإعادة الفحص والمطابقة
    pub fn resurrect_on_mutation(
        buffer: &mut LatentBuffer,
        hypergraph: &mut CorrelationHypergraph,
        event: &GraphMutationEvent,
    ) -> Vec<[u8; 32]> {
        let mut resurrected = Vec::new();

        match event {
            GraphMutationEvent::DimensionalExpansion { added_dimension_index } => {
                // إيقاظ كافة الفرضيات الخاملة التي تمتلك عجزاً قد يستفيد من البعد الجديد
                for record in buffer.records_mut() {
                    if record.is_dormant {
                        // إذا كان البعد الجديد يتقاطع مع مجال العجز
                        if record.shadow.dim_deficit.get_coord(*added_dimension_index).is_zero() {
                            record.set_dormant(false);
                            resurrected.push(record.record_id);
                        }
                    }
                }
            }
            GraphMutationEvent::NewLawDiscovered { .. } | GraphMutationEvent::ConsolidationOccurred { .. } => {
                // إيقاظ عام للفرضيات الخاملة المرتبطة بحواف المخطط الفائق
                for record in buffer.records_mut() {
                    if record.is_dormant && !record.hyperedge_keys.is_empty() {
                        record.set_dormant(false);
                        resurrected.push(record.record_id);
                    }
                }
            }
        }

        // تحديث حالة السجلات في المخطط الفائق
        for &id in &resurrected {
            if let Some(r) = buffer.get(&id) {
                hypergraph.insert_record(r.clone());
            }
        }

        resurrected
    }

    /// مساعدة لفحص هل الفرضية تتقاطع مع متجه أبعاد معين
    pub fn shares_interface(deficit: &DimensionVector, target: &DimensionVector) -> bool {
        let max_len = deficit.effective_len().max(target.effective_len());
        for i in 0..max_len {
            if !deficit.get_coord(i).is_zero() && !target.get_coord(i).is_zero() {
                return true;
            }
        }
        false
    }
}
