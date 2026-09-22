use crate::error::DnaError;
use crate::mmap_engine::DnaStorageEngine;
use crate::packed_enode::{ENODE_SIZE, FLAG_IMMUTABLE_CONST, PackedENode};
use crate::record::{
    UniversalRecordPrefix, RECORD_PREFIX_SIZE, RECORD_STATUS_ACTIVE, RECORD_TYPE_BRIDGE_DEF,
};
use aletheia_algebra::Rational;
use aletheia_epistemic::SovereignDnaPayload;
use num_traits::ToPrimitive;
use std::collections::HashMap;

/// مصفوفة التوجيه الطوبولوجي المباشر للجسور في الذاكرة العشوائية (In-Memory Ephemeral Cache)
/// تحسب مسبقاً مسارات فلويد-وارشال والثابت التراكمي K_cum للاستعلام في O(1)
#[derive(Clone, Debug, Default)]
pub struct DirectBridgeRoutingMatrix {
    /// جدول التوجيه: (المجال المصدر، المجال الهدف) -> (المسار الوسيط، ثابت الاقتران التراكمي في Q)
    routes: HashMap<(u16, u16), (Vec<u16>, Rational)>,
}

impl DirectBridgeRoutingMatrix {
    pub fn new() -> Self {
        Self {
            routes: HashMap::new(),
        }
    }

    /// تسجيل جسر أولي مباشر
    pub fn register_direct_bridge(
        &mut self,
        source: u16,
        target: u16,
        scale: Rational,
    ) {
        self.routes.insert((source, target), (vec![source, target], scale.clone()));
        if !scale.is_zero() {
            let inv_scale = Rational::one() / scale;
            self.routes.insert((target, source), (vec![target, source], inv_scale));
        }
    }

    /// استرجاع مسار التحويل وثابت الاقتران التراكمي في زمن O(1)
    pub fn query_route(&self, source: u16, target: u16) -> Option<(&[u16], Rational)> {
        if source == target {
            static SELF_ROUTE: [u16; 1] = [0];
            return Some((&SELF_ROUTE[..0], Rational::one()));
        }

        self.routes
            .get(&(source, target))
            .map(|(path, scale)| (path.as_slice(), scale.clone()))
    }

    /// إعادة حوسبة المسارات التراكمية بين جميع المجالات (Floyd-Warshall Algorithm)
    pub fn recompute_all_pairs(&mut self, domains: &[u16]) {
        for &k in domains {
            for &i in domains {
                for &j in domains {
                    if i == j {
                        continue;
                    }
                    if let (Some((path_ik, scale_ik)), Some((path_kj, scale_kj))) = (
                        self.routes.get(&(i, k)).cloned(),
                        self.routes.get(&(k, j)).cloned(),
                    ) {
                        let new_scale = scale_ik * scale_kj;
                        let mut new_path = path_ik;
                        if path_kj.len() > 1 {
                            new_path.extend_from_slice(&path_kj[1..]);
                        }

                        let should_update = match self.routes.get(&(i, j)) {
                            None => true,
                            Some((existing_path, _)) => new_path.len() < existing_path.len(),
                        };

                        if should_update {
                            self.routes.insert((i, j), (new_path, new_scale));
                        }
                    }
                }
            }
        }
    }

    /// إعادة حوسبة المسارات بين كافة المجالات المسجلة حالياً
    pub fn recompute_all_known_pairs(&mut self) {
        let mut domains: Vec<u16> = self.routes.keys().flat_map(|&(s, t)| [s, t]).collect();
        domains.sort_unstable();
        domains.dedup();
        self.recompute_all_pairs(&domains);
    }
}

/// المحرك التنفيذي للتطور المعرفي الذاتي واستيعاب الصكوك في الـ DNA
pub struct AutonomousEvolutionEngine {
    pub storage: DnaStorageEngine,
    pub routing_matrix: DirectBridgeRoutingMatrix,
}

/// مواصفة وصف المجال المستحدث
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct SpawnedDomainDescriptor {
    pub domain_id: u16,
    pub name: String,
    pub invariance_group: u16,
    pub basis_id: u32,
}

/// التحقق من الاستقلال الخطي المطلق للبعد المقترح فوق حقل الأعداد النسبية Q
/// d_new ∉ span_Q(B_existing)
pub fn verify_algebraic_independence(
    existing_basis: &[aletheia_lattice::DimensionVector],
    proposed: &aletheia_lattice::DimensionVector,
) -> bool {
    if proposed.is_dimensionless() {
        return false;
    }
    if existing_basis.is_empty() {
        return true;
    }

    let mut max_dim = proposed.effective_len();
    for vec in existing_basis {
        max_dim = max_dim.max(vec.effective_len());
    }
    if max_dim == 0 {
        return false;
    }

    let mut basis_rows = Vec::with_capacity(existing_basis.len());
    for vec in existing_basis {
        let mut row = Vec::with_capacity(max_dim);
        for i in 0..max_dim {
            row.push(vec.get_coord(i));
        }
        basis_rows.push(row);
    }
    let mut basis_mat = aletheia_lattice::RationalMatrix::from_rows(basis_rows.clone());
    let (basis_rank, _) = basis_mat.rref();

    let mut extended_rows = basis_rows;
    let mut prop_row = Vec::with_capacity(max_dim);
    for i in 0..max_dim {
        prop_row.push(proposed.get_coord(i));
    }
    extended_rows.push(prop_row);

    let mut extended_mat = aletheia_lattice::RationalMatrix::from_rows(extended_rows);
    let (extended_rank, _) = extended_mat.rref();

    extended_rank > basis_rank
}

impl AutonomousEvolutionEngine {
    pub fn new(storage: DnaStorageEngine) -> Self {
        let mut engine = Self {
            storage,
            routing_matrix: DirectBridgeRoutingMatrix::new(),
        };
        engine.rebuild_in_memory_routing();
        engine
    }

    /// التمدد البعدي الفيزيائي: ترقية فضاء الأبعاد Q^N إلى Q^(N+1)
    /// تطبيق قاعدة الإسقاط الصفري الكنسي: ترقية الرتبة دون لمس العقد السابقة
    pub fn spawn_dimension(&mut self, _name: &str) -> Result<u16, DnaError> {
        let current_rank = self.storage.header.dimension_rank();
        let new_rank = current_rank + 1;
        self.storage.header.set_dimension_rank(new_rank);
        self.storage.sync_header()?;
        Ok(new_rank)
    }

    /// التمدد البعدي الفيزيائي مع فحص غربال الاستقلال الجبري الحتمي:
    /// التحقق من أن المتجه المقترح لا ينتمي إلى الفضاء المولد بالأبعاد القائمة فوق Q
    pub fn spawn_dimension_checked(
        &mut self,
        name: &str,
        proposed_vector: &aletheia_lattice::DimensionVector,
        existing_basis: &[aletheia_lattice::DimensionVector],
    ) -> Result<u16, DnaError> {
        if !verify_algebraic_independence(existing_basis, proposed_vector) {
            return Err(DnaError::AlgebraicDependenceError(format!(
                "البعد المقترح '{}' يعتمد خطياً على الأساس البعدي القائم، ولا يمثل بعداً أصيلاً مستقلاً",
                name
            )));
        }
        self.spawn_dimension(name)
    }

    /// زرع ثابت الاقتران مادياً كـ PackedENode مصمتة وتحديث فئة التكافؤ
    pub fn materialize_bridge_constant(
        &mut self,
        source_domain: u16,
        target_domain: u16,
        scale: Rational,
    ) -> Result<u32, DnaError> {
        let const_node_idx = self.storage.header.total_enodes;
        let const_class_id = self.storage.header.total_classes;

        // 1. حساب الإزاحات
        let node_offset = self.storage.header.offset_enodes as usize + (const_node_idx as usize * ENODE_SIZE);
        let uf_offset = self.storage.header.offset_uf as usize + (const_class_id as usize * 4);

        // التأكد من توفر المساحة في الحيز المحجوز مسبقاً
        let required = uf_offset + 4 + RECORD_PREFIX_SIZE + 64;
        self.storage.ensure_capacity(required)?;

        // 2. كتابة العقدة المصمتة في مصفوفة الـ Arena
        // ملاحظة معمارية: aux_data في العقدة المصمتة يخزن بسط الثابت للاسترجاع السريع في الحالات الصحيحة،
        // بينما يتم حفظ الكسر الدقيق (بسطاً ومقاماً) بدقة مطلقة في سجل الـ Lineage "{}:{}" وفي مصفوفة التوجيه.
        let enode = PackedENode {
            op_id: crate::packed_enode::OpCode::RationalConst as u16,
            arity: 0,
            flags: FLAG_IMMUTABLE_CONST,
            left_class_id: const_class_id,
            right_class_id: 0,
            aux_data: scale.numer().to_u32().unwrap_or(0),
        };

        {
            let buf = self.storage.buffer_mut()?;
            buf[node_offset..node_offset + ENODE_SIZE].copy_from_slice(&enode.to_bytes());
            // 3. كتابة جدول الـ Union-Find بتسطيح مسار كامل (parent[c] = c)
            buf[uf_offset..uf_offset + 4].copy_from_slice(&const_class_id.to_le_bytes());
        }

        // 4. كتابة سجل الجسر في قطاع الـ Lineage عند الذيل الحالي (offset_lineage + lineage_size)
        let payload = format!("{}:{}", scale.numer(), scale.denom()).into_bytes();
        let payload_crc = UniversalRecordPrefix::compute_crc(&payload);
        let prefix = UniversalRecordPrefix::new_bridge(
            source_domain,
            target_domain,
            payload.len() as u32,
            payload_crc,
        );

        let append_offset = self.storage.header.offset_lineage as usize + self.storage.header.lineage_size as usize;
        let record_len = RECORD_PREFIX_SIZE + payload.len();
        let next_capacity = append_offset + record_len;
        self.storage.ensure_capacity(next_capacity)?;

        {
            let buf = self.storage.buffer_mut()?;
            buf[append_offset..append_offset + RECORD_PREFIX_SIZE]
                .copy_from_slice(&prefix.to_bytes());
            buf[append_offset + RECORD_PREFIX_SIZE..next_capacity].copy_from_slice(&payload);
        }

        // 5. تحديث عدادات الترويسة ومقدار قطاع الـ Lineage مع الإبقاء على offset_lineage ثابتاً
        self.storage.header.total_enodes += 1;
        self.storage.header.total_classes += 1;
        self.storage.header.lineage_size += record_len as u32;
        self.storage.flush()?;

        // 6. تحديث مصفوفة التوجيه المباشر في الذاكرة العشوائية
        self.routing_matrix
            .register_direct_bridge(source_domain, target_domain, scale);

        Ok(const_class_id)
    }

    /// تسجيل مجال معرفي مستقل في ركيزة الـ DNA
    pub fn materialize_domain(
        &mut self,
        domain_id: u16,
        group_id: u16,
        basis_id: u32,
    ) -> Result<(), DnaError> {
        self.materialize_domain_with_descriptor(domain_id, group_id, basis_id, "")
    }

    /// تسجيل مجال معرفي مستقل في ركيزة الـ DNA مع وصف نصي للمجال في حمولة السجل
    pub fn materialize_domain_with_descriptor(
        &mut self,
        domain_id: u16,
        group_id: u16,
        basis_id: u32,
        name: &str,
    ) -> Result<(), DnaError> {
        let payload = name.as_bytes();
        let payload_len = payload.len() as u32;
        let payload_crc = if payload_len > 0 {
            UniversalRecordPrefix::compute_crc(payload)
        } else {
            0
        };

        let prefix = UniversalRecordPrefix::new_domain_with_payload(
            domain_id,
            group_id,
            basis_id,
            payload_len,
            payload_crc,
        );

        let append_offset = self.storage.header.offset_lineage as usize + self.storage.header.lineage_size as usize;
        let record_len = RECORD_PREFIX_SIZE + payload.len();
        let next_capacity = append_offset + record_len;
        self.storage.ensure_capacity(next_capacity)?;

        {
            let buf = self.storage.buffer_mut()?;
            buf[append_offset..append_offset + RECORD_PREFIX_SIZE].copy_from_slice(&prefix.to_bytes());
            if payload_len > 0 {
                buf[append_offset + RECORD_PREFIX_SIZE..next_capacity].copy_from_slice(payload);
            }
        }

        self.storage.header.lineage_size += record_len as u32;
        self.storage.flush()?;
        Ok(())
    }

    /// استرجاع مسار التحويل وثابت الاقتران التراكمي في زمن O(1)
    pub fn query_bridge_path(&self, source_domain: u16, target_domain: u16) -> (Vec<u16>, Rational) {
        if let Some((path, k_cum)) = self.routing_matrix.query_route(source_domain, target_domain) {
            (path.to_vec(), k_cum)
        } else {
            (Vec::new(), Rational::zero())
        }
    }

    /// استيعاب حمولة المحور السابع (SovereignDnaPayload) وتثبيتها كسجلات سيادية
    pub fn ingest_sovereign_payload(
        &mut self,
        payload: &SovereignDnaPayload,
    ) -> Result<usize, DnaError> {
        let mut count = 0;

        for receipt in &payload.sovereign_receipts {
            // التحقق من النزاهة التشفيرية للصك
            if !receipt.verify_integrity() {
                return Err(DnaError::PayloadIngestionError(format!(
                    "صك سيادي فاسد للقانون '{}'",
                    receipt.law_id
                )));
            }

            // تسلسل الصك السيادي بالكامل
            let receipt_bytes = receipt.to_bytes().map_err(|e| {
                DnaError::PayloadIngestionError(format!("فشل تسلسل الصك السيادي: {:?}", e))
            })?;
            let payload_crc = UniversalRecordPrefix::compute_crc(&receipt_bytes);
            let domain_id = receipt.domain.id();

            let prefix = UniversalRecordPrefix::new_axiom(
                receipt_bytes.len() as u32,
                domain_id,
                payload_crc,
                payload.epoch,
            );

            let append_offset = self.storage.header.offset_lineage as usize + self.storage.header.lineage_size as usize;
            let record_len = RECORD_PREFIX_SIZE + receipt_bytes.len();
            let next_capacity = append_offset + record_len;
            self.storage.ensure_capacity(next_capacity)?;

            {
                let buf = self.storage.buffer_mut()?;
                buf[append_offset..append_offset + RECORD_PREFIX_SIZE]
                    .copy_from_slice(&prefix.to_bytes());
                buf[append_offset + RECORD_PREFIX_SIZE..next_capacity]
                    .copy_from_slice(&receipt_bytes);
            }

            self.storage.header.total_axioms += 1;
            self.storage.header.lineage_size += record_len as u32;
            count += 1;
        }

        self.storage.flush()?;
        Ok(count)
    }

    /// إعادة بناء مصفوفة التوجيه العابرة في الـ RAM بمسح سجلات الجسور القائمة
    pub fn rebuild_in_memory_routing(&mut self) {
        let buf = self.storage.buffer();
        let mut offset = self.storage.header.offset_lineage as usize;
        let lineage_end = offset + self.storage.header.lineage_size as usize;

        while offset + RECORD_PREFIX_SIZE <= lineage_end && offset + RECORD_PREFIX_SIZE <= buf.len() {
            if let Ok(prefix) = UniversalRecordPrefix::from_bytes(&buf[offset..offset + RECORD_PREFIX_SIZE]) {
                let payload_start = offset + RECORD_PREFIX_SIZE;
                let payload_end = payload_start + prefix.payload_len as usize;
                if payload_end > buf.len() || payload_end > lineage_end {
                    break;
                }

                if prefix.record_type == RECORD_TYPE_BRIDGE_DEF && prefix.status == RECORD_STATUS_ACTIVE {
                    if let Ok(s) = std::str::from_utf8(&buf[payload_start..payload_end]) {
                        let parts: Vec<&str> = s.split(':').collect();
                        if parts.len() == 2 {
                            if let (Ok(num), Ok(den)) = (parts[0].parse::<i64>(), parts[1].parse::<i64>()) {
                                if let Ok(scale) = Rational::new(num, den) {
                                    self.routing_matrix.register_direct_bridge(
                                        prefix.domain_id,
                                        prefix.group_id,
                                        scale,
                                    );
                                }
                            }
                        }
                    }
                }
                offset = payload_end;
            } else {
                break;
            }
        }
        self.routing_matrix.recompute_all_known_pairs();
    }
}
