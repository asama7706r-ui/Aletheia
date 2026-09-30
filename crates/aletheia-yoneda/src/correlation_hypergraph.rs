use crate::quarantine_buffer::QuarantineRecord;
use aletheia_algebra::VariableId;
use aletheia_lattice::DimensionVector;
use num_traits::ToPrimitive;
use std::collections::HashMap;

/// نوع الرابطة الفائقة في مخطط الارتباط الفائق
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum HyperedgeKind {
    /// 1. مجهول مشترك بين فرضيتين أو أكثر
    SharedUnknown(VariableId),
    /// 2. بصمة عجز بعدي سالب متطابقة في فضاء الشبكيات Q^N
    HomologousDeficit(Box<DimensionVector>),
    /// 3. تناظر مقولاتي حفظي مشترك (Noether Symmetry Invariant)
    NoetherInvariant(String),
    /// 4. شعاع تناسب بعدي خطي مشترك في Q^N (Collinear Ray Deficit)
    CollinearDeficit(Box<DimensionVector>),
}

impl HyperedgeKind {
    /// حساب المعرف الحتمي للحافة الفائقة عبر BLAKE3
    pub fn compute_id(&self) -> [u8; 32] {
        let mut hasher = blake3::Hasher::new();
        match self {
            HyperedgeKind::SharedUnknown(v) => {
                hasher.update(b"HYPEREDGE_UNKNOWN");
                hasher.update(&v.0.to_le_bytes());
            }
            HyperedgeKind::HomologousDeficit(dim) => {
                hasher.update(b"HYPEREDGE_DEFICIT");
                for (idx, c) in dim.coords().iter().enumerate() {
                    if !c.is_zero() {
                        hasher.update(&idx.to_le_bytes());
                        hasher.update(c.to_string().as_bytes());
                    }
                }
            }
            HyperedgeKind::NoetherInvariant(name) => {
                hasher.update(b"HYPEREDGE_NOETHER");
                hasher.update(name.as_bytes());
            }
            HyperedgeKind::CollinearDeficit(dim) => {
                hasher.update(b"HYPEREDGE_COLLINEAR");
                for (idx, c) in dim.coords().iter().enumerate() {
                    if !c.is_zero() {
                        hasher.update(&idx.to_le_bytes());
                        hasher.update(c.to_string().as_bytes());
                    }
                }
            }
        }
        *hasher.finalize().as_bytes()
    }
}

/// الحافة الفائقة الرابطة لمجموعة فرضيات في الحجر الصحي
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Hyperedge {
    pub id: [u8; 32],
    pub kind: HyperedgeKind,
    pub members: Vec<[u8; 32]>,
}

impl Hyperedge {
    pub fn new(kind: HyperedgeKind) -> Self {
        let id = kind.compute_id();
        Self {
            id,
            kind,
            members: Vec::new(),
        }
    }

    pub fn add_member(&mut self, record_id: [u8; 32]) {
        if !self.members.contains(&record_id) {
            self.members.push(record_id);
        }
    }
}

/// مخطط الارتباط الفائق للفرضيات المعلقة في الحجر الصحي (Correlation Hypergraph)
#[derive(Clone, Debug, Default)]
pub struct CorrelationHypergraph {
    pub records: HashMap<[u8; 32], QuarantineRecord>,
    pub hyperedges: HashMap<[u8; 32], Hyperedge>,
}

impl CorrelationHypergraph {
    pub fn new() -> Self {
        Self {
            records: HashMap::new(),
            hyperedges: HashMap::new(),
        }
    }

    /// إدراج فرضية معلقة في المخطط وفهرسة عجزها البعدي تلقائياً كحافة فائقة
    pub fn insert_record(&mut self, mut record: QuarantineRecord) {
        let dim_deficit = record.shadow.dim_deficit.clone();
        let record_id = record.record_id;

        // فهرسة العجز البعدي المتماثل
        if !dim_deficit.is_dimensionless() {
            let hedge_kind = HyperedgeKind::HomologousDeficit(Box::new(dim_deficit.clone()));
            let hedge_id = hedge_kind.compute_id();
            let entry = self
                .hyperedges
                .entry(hedge_id)
                .or_insert_with(|| Hyperedge::new(hedge_kind));
            entry.add_member(record_id);
            record.hyperedge_keys.push(hedge_id);

            // فهرسة الشعاع التناسبي البدائي في Q^N للعجوزات المتناسبة (Collinear Deficit)
            if let Some(primitive) = compute_primitive_ray(&dim_deficit) {
                let col_kind = HyperedgeKind::CollinearDeficit(Box::new(primitive));
                let col_id = col_kind.compute_id();
                let col_entry = self
                    .hyperedges
                    .entry(col_id)
                    .or_insert_with(|| Hyperedge::new(col_kind));
                col_entry.add_member(record_id);
                if !record.hyperedge_keys.contains(&col_id) {
                    record.hyperedge_keys.push(col_id);
                }
            }
        }

        self.records.insert(record_id, record);
    }

    /// ربط فرضية بمجهول مشترك
    pub fn link_shared_unknown(&mut self, record_id: [u8; 32], var: VariableId) {
        let hedge_kind = HyperedgeKind::SharedUnknown(var);
        let hedge_id = hedge_kind.compute_id();
        let entry = self
            .hyperedges
            .entry(hedge_id)
            .or_insert_with(|| Hyperedge::new(hedge_kind));
        entry.add_member(record_id);

        if let Some(r) = self.records.get_mut(&record_id) {
            if !r.hyperedge_keys.contains(&hedge_id) {
                r.hyperedge_keys.push(hedge_id);
            }
        }
    }

    /// ربط فرضية بتناظر نويثري محفوظ
    pub fn link_noether_invariant(&mut self, record_id: [u8; 32], symmetry_name: &str) {
        let hedge_kind = HyperedgeKind::NoetherInvariant(symmetry_name.to_string());
        let hedge_id = hedge_kind.compute_id();
        let entry = self
            .hyperedges
            .entry(hedge_id)
            .or_insert_with(|| Hyperedge::new(hedge_kind));
        entry.add_member(record_id);

        if let Some(r) = self.records.get_mut(&record_id) {
            if !r.hyperedge_keys.contains(&hedge_id) {
                r.hyperedge_keys.push(hedge_id);
            }
        }
    }

    /// إزالة فرضية تماماً من مخطط الارتباط الفائق عند ترقيتها سيادياً أو إبطالها
    pub fn remove_record(&mut self, record_id: &[u8; 32]) {
        if let Some(r) = self.records.remove(record_id) {
            for hedge_id in &r.hyperedge_keys {
                if let Some(hedge) = self.hyperedges.get_mut(hedge_id) {
                    hedge.members.retain(|m| m != record_id);
                }
            }
        }
    }

    /// استخراج كافة الحواف الفائقة المؤهلة لدمج النيوترينو (تضم فرضيتين أو أكثر نشطة وذات درجات حرية غير مصفّرة)
    pub fn consolidation_candidates(&self) -> Vec<&Hyperedge> {
        self.hyperedges
            .values()
            .filter(|e| {
                let active_members_count = e.members.iter().filter(|m| {
                    if let Some(r) = self.records.get(*m) {
                        !r.remaining_dof.is_zero() && !r.is_dormant
                    } else {
                        false
                    }
                }).count();
                active_members_count >= 2
            })
            .collect()
    }
}

/// حساب الشعاع البدائي في Q^N (Primitive Ray Direction)
/// يحول أي متجه أبعاد كسري إلى متجه أعداد صحيحة أولية نسبياً عبر القاسم المشترك الأكبر
pub fn compute_primitive_ray(dim: &DimensionVector) -> Option<DimensionVector> {
    if dim.is_dimensionless() {
        return None;
    }

    // 1. حساب المضاعف المشترك الأصغر للمقامات LCM
    let mut lcm: i64 = 1;
    for c in dim.coords() {
        let den = c.denom().to_i64().unwrap_or(1);
        lcm = integer_lcm(lcm, den);
    }

    // 2. تحويل الإحداثيات إلى أعداد صحيحة عبر توحيد المقامات
    let mut ints: Vec<i64> = Vec::with_capacity(dim.len());
    for c in dim.coords() {
        let num = c.numer().to_i64().unwrap_or(0);
        let den = c.denom().to_i64().unwrap_or(1);
        let factor = lcm / den;
        ints.push(num * factor);
    }

    // 3. حساب القاسم المشترك الأكبر GCD
    let mut g: i64 = 0;
    for &val in &ints {
        g = integer_gcd(g, val.abs());
    }

    if g == 0 {
        return None;
    }

    // 4. الاختزال بالقسمة على GCD
    for val in &mut ints {
        *val /= g;
    }

    // 5. ضبط إشارة أول إحداثي غير صفري ليكون موجباً (التمثيل الكنسي الفريد للشعاع)
    let first_nonzero = ints.iter().find(|&&x| x != 0);
    if let Some(&first) = first_nonzero {
        if first < 0 {
            for val in &mut ints {
                *val = -*val;
            }
        }
    }

    Some(DimensionVector::from_integers(&ints))
}

fn integer_gcd(mut a: i64, mut b: i64) -> i64 {
    while b != 0 {
        let t = b;
        b = a % b;
        a = t;
    }
    a.abs()
}

fn integer_lcm(a: i64, b: i64) -> i64 {
    if a == 0 || b == 0 {
        0
    } else {
        (a.abs() / integer_gcd(a, b)) * b.abs()
    }
}

