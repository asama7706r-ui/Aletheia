use crate::receipt::{LockReceipt, LockType};
use aletheia_algebra::Rational;
use aletheia_lattice::DimensionVector;
use serde::{Deserialize, Serialize};
use std::collections::{HashSet, VecDeque};

/// وسوم المجالات الأنطولوجية المعزولة
#[derive(Copy, Clone, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum DomainTag {
    /// المجال المجرد الكوني واللابعدي
    UniversalAbstract,
    /// الميكانيكا الكلاسيكية
    ClassicalMechanics,
    /// الكهرومغناطيسية
    Electromagnetism,
    /// الديناميكا الحرارية
    Thermodynamics,
    /// النسبية
    Relativity,
    /// ميكانيكا الكم
    QuantumMechanics,
    /// الميكانيكا الإحصائية
    StatisticalMechanics,
    /// علم الكونيات
    Cosmology,
    /// مجال فيزيائي مخصص بالمعرف العددي
    Custom(u32),
}

/// مواصفات وتوصيف المجال المعرفي الدستوري وفق المحور 8 (SpawnedDomainDescriptor)
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct DomainDescriptor {
    pub domain_id: u16,
    pub name: String,
    pub invariance_group: String,
    pub basis_dimension_indices: Vec<usize>,
}

impl DomainDescriptor {
    pub fn new(
        domain_id: u16,
        name: impl Into<String>,
        invariance_group: impl Into<String>,
        basis_dimension_indices: Vec<usize>,
    ) -> Self {
        Self {
            domain_id,
            name: name.into(),
            invariance_group: invariance_group.into(),
            basis_dimension_indices,
        }
    }
}

impl DomainTag {
    /// الحصول على المعرف العددي الثنائي للمجال
    pub fn id(&self) -> u16 {
        match self {
            DomainTag::UniversalAbstract => 0,
            DomainTag::ClassicalMechanics => 1,
            DomainTag::Electromagnetism => 2,
            DomainTag::Thermodynamics => 3,
            DomainTag::Relativity => 4,
            DomainTag::QuantumMechanics => 5,
            DomainTag::StatisticalMechanics => 6,
            DomainTag::Cosmology => 7,
            DomainTag::Custom(c) => *c as u16,
        }
    }

    /// استرجاع وسم المجال من المعرف العددي الثنائي
    pub fn from_id(id: u16) -> Self {
        match id {
            0 => DomainTag::UniversalAbstract,
            1 => DomainTag::ClassicalMechanics,
            2 => DomainTag::Electromagnetism,
            3 => DomainTag::Thermodynamics,
            4 => DomainTag::Relativity,
            5 => DomainTag::QuantumMechanics,
            6 => DomainTag::StatisticalMechanics,
            7 => DomainTag::Cosmology,
            other => DomainTag::Custom(other as u32),
        }
    }

    /// فهارس الأبعاد الأساسية التي تُعرّف هذا المجال في شبيكة SI-7
    /// 0: Length [L], 1: Mass [M], 2: Time [T], 3: ElectricCurrent [I]
    /// 4: Temperature [Θ], 5: AmountOfSubstance [N], 6: LuminousIntensity [J]
    pub fn active_dimension_indices(&self) -> &'static [usize] {
        match self {
            DomainTag::UniversalAbstract => &[],
            DomainTag::ClassicalMechanics => &[0, 1, 2],         // [L, M, T]
            DomainTag::Electromagnetism => &[0, 1, 2, 3],        // [L, M, T, I]
            DomainTag::Thermodynamics => &[0, 1, 2, 4],          // [L, M, T, Θ]
            DomainTag::Relativity => &[0, 1, 2],                 // [L, M, T] (invariant c)
            DomainTag::QuantumMechanics => &[0, 1, 2],            // [L, M, T] (invariant ħ)
            DomainTag::StatisticalMechanics => &[0, 1, 2, 4, 5], // [L, M, T, Θ, N]
            DomainTag::Cosmology => &[0, 1, 2, 4, 6],            // [L, M, T, Θ, J]
            DomainTag::Custom(_) => &[],
        }
    }

    /// زمرة التناظر الدستورية التي تحكم هذا المجال
    pub fn invariance_group(&self) -> &'static str {
        match self {
            DomainTag::UniversalAbstract => "Identity",
            DomainTag::ClassicalMechanics => "Galilean_SE3",
            DomainTag::Electromagnetism => "Gauge_U1_Lorentz",
            DomainTag::Thermodynamics => "MaxEnt_Equilibrium",
            DomainTag::Relativity => "Poincare_SO13",
            DomainTag::QuantumMechanics => "Unitary_U_Hilbert",
            DomainTag::StatisticalMechanics => "Liouville_PhaseSpace",
            DomainTag::Cosmology => "FLRW_Diffeomorphism",
            DomainTag::Custom(_) => "Custom_Symmetry",
        }
    }

    /// استخراج التوصيف الدستوري الكامل للمجال (SpawnedDomainDescriptor)
    pub fn descriptor(&self) -> DomainDescriptor {
        DomainDescriptor {
            domain_id: self.id(),
            name: format!("{:?}", self),
            invariance_group: self.invariance_group().to_string(),
            basis_dimension_indices: self.active_dimension_indices().to_vec(),
        }
    }

    /// توليد متجه الأبعاد الأساسي التجميعي في شبيكة SI-7
    pub fn composite_dimension(&self) -> DimensionVector {
        let indices = self.active_dimension_indices();
        if indices.is_empty() {
            return DimensionVector::dimensionless();
        }
        let max_idx = indices.iter().max().copied().unwrap_or(0);
        let mut coords = vec![0i64; max_idx + 1];
        for &idx in indices {
            coords[idx] = 1;
        }
        DimensionVector::from_integers(&coords)
    }

    /// اشتقاق الفجوة البُعدية الكنسية لثابت الاقتران لسد الانتقال بين مجالين
    /// [K_bridge] = [D_target] * [D_source]^-1 = d_target - d_source
    pub fn canonical_coupling_gap(&self, target: &DomainTag) -> DimensionVector {
        let source_dim = self.composite_dimension();
        let target_dim = target.composite_dimension();
        &target_dim - &source_dim
    }
}

impl From<u16> for DomainTag {
    fn from(id: u16) -> Self {
        Self::from_id(id)
    }
}

impl From<DomainTag> for u16 {
    fn from(tag: DomainTag) -> Self {
        tag.id()
    }
}

/// جسر أنطولوجي معتمد بين مجالين معرفيين
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct DomainBridge {
    pub name: String,
    pub source: DomainTag,
    pub target: DomainTag,
    /// متجه أبعاد ثابت الاقتران [K] in Q^N
    pub coupling_dimension: DimensionVector,
    /// مقياس الاقتران النسبي في Q
    pub coupling_scale: Rational,
    /// هل الجسر أحادي الاتجاه قطيعة (غير قابل للعكس)
    pub is_unidirectional: bool,
}

impl DomainBridge {
    pub fn new(
        name: impl Into<String>,
        source: DomainTag,
        target: DomainTag,
        coupling_dimension: DimensionVector,
        coupling_scale: Rational,
    ) -> Self {
        Self {
            name: name.into(),
            source,
            target,
            coupling_dimension,
            coupling_scale,
            is_unidirectional: false,
        }
    }

    /// إنشاء جسر اشتقاقي كنسي مع الحساب التلقائي لمتجه أبعاد الاقتران
    /// وفق معادلة المحور السابع: [K] = [D_target] - [D_source]
    pub fn canonical(
        name: impl Into<String>,
        source: DomainTag,
        target: DomainTag,
        coupling_scale: Rational,
    ) -> Self {
        let coupling_dimension = source.canonical_coupling_gap(&target);
        Self::new(name, source, target, coupling_dimension, coupling_scale)
    }

    pub fn unidirectional(mut self) -> Self {
        self.is_unidirectional = true;
        self
    }
}

/// سجل الجسور المصادق عليها ومحرك البحث الطوبولوجي متعدي النقل (Transitive Bridge Registry)
#[derive(Clone, Debug, Default)]
pub struct BridgeRegistry {
    bridges: Vec<DomainBridge>,
}

impl BridgeRegistry {
    pub fn new() -> Self {
        Self {
            bridges: Vec::new(),
        }
    }

    /// تسجيل جسر معتمد في السجل
    pub fn register_bridge(&mut self, bridge: DomainBridge) {
        self.bridges.push(bridge);
    }

    /// استرجاع الجسور المسجلة للقراءة
    pub fn bridges(&self) -> &[DomainBridge] {
        &self.bridges
    }

    /// اكتشاف أقصر مسار تحويلي بين مجالين باستخدام البحث العرضي (BFS)
    /// يدعم الجسور العكسية تلقائياً:
    /// إذا كان الجسر D1 -> D2 بمقياس S وبعد K، فإن مسار D2 -> D1 له مقياس 1/S وبعد -K
    pub fn find_shortest_bridge_path(
        &self,
        from: DomainTag,
        to: DomainTag,
    ) -> Option<(Vec<DomainBridge>, Rational, DimensionVector)> {
        if from == to || from == DomainTag::UniversalAbstract || to == DomainTag::UniversalAbstract {
            return Some((Vec::new(), Rational::one(), DimensionVector::dimensionless()));
        }

        // صف الانتظار: (المجال الحالي، الجسور المتراكمة، المقياس التراكمي، البعد التراكمي)
        let mut queue: VecDeque<(DomainTag, Vec<DomainBridge>, Rational, DimensionVector)> = VecDeque::new();
        let mut visited: HashSet<DomainTag> = HashSet::new();

        queue.push_back((from, Vec::new(), Rational::one(), DimensionVector::dimensionless()));
        visited.insert(from);

        while let Some((curr, path, cum_scale, cum_dim)) = queue.pop_front() {
            if curr == to {
                return Some((path, cum_scale, cum_dim));
            }

            for bridge in &self.bridges {
                // 1. الاتجاه المباشر: source -> target
                if bridge.source == curr && !visited.contains(&bridge.target) {
                    visited.insert(bridge.target);
                    let mut next_path = path.clone();
                    next_path.push(bridge.clone());
                    let next_scale = &cum_scale * &bridge.coupling_scale;
                    let next_dim = &cum_dim + &bridge.coupling_dimension;
                    queue.push_back((bridge.target, next_path, next_scale, next_dim));
                }

                // 2. الاتجاه العكسي التلقائي: target -> source (إذا لم يكن أحادي الاتجاه)
                if !bridge.is_unidirectional && bridge.target == curr && !visited.contains(&bridge.source) {
                    visited.insert(bridge.source);
                    let inv_scale = &Rational::one() / &bridge.coupling_scale;
                    let inv_dim = -bridge.coupling_dimension.clone();

                    let inv_bridge = DomainBridge {
                        name: format!("Inv({})", bridge.name),
                        source: bridge.target,
                        target: bridge.source,
                        coupling_dimension: inv_dim.clone(),
                        coupling_scale: inv_scale.clone(),
                        is_unidirectional: true,
                    };

                    let mut next_path = path.clone();
                    next_path.push(inv_bridge);
                    let next_scale = &cum_scale * &inv_scale;
                    let next_dim = &cum_dim + &inv_dim;
                    queue.push_back((bridge.source, next_path, next_scale, next_dim));
                }
            }
        }

        None
    }

    /// اكتشاف مسار تحويلي بين مجالين يطابق فجوة أبعاد محددة (أو معكوسها) للتعامل مع قنوات الاقتران المتعامدة
    pub fn find_bridge_path_matching_dimension(
        &self,
        from: DomainTag,
        to: DomainTag,
        target_dim: &DimensionVector,
    ) -> Option<(Vec<DomainBridge>, Rational, DimensionVector)> {
        if from == to || from == DomainTag::UniversalAbstract || to == DomainTag::UniversalAbstract {
            if target_dim.is_dimensionless() {
                return Some((Vec::new(), Rational::one(), DimensionVector::dimensionless()));
            } else {
                return None;
            }
        }

        let mut queue: VecDeque<(DomainTag, Vec<DomainBridge>, Rational, DimensionVector)> = VecDeque::new();
        let mut visited: HashSet<(DomainTag, DimensionVector)> = HashSet::new();

        queue.push_back((from, Vec::new(), Rational::one(), DimensionVector::dimensionless()));
        visited.insert((from, DimensionVector::dimensionless()));

        while let Some((curr, path, cum_scale, cum_dim)) = queue.pop_front() {
            if curr == to && (&cum_dim == target_dim || &cum_dim == &-target_dim.clone()) && !path.is_empty() {
                return Some((path, cum_scale, cum_dim));
            }

            for bridge in &self.bridges {
                // 1. الاتجاه المباشر: source -> target
                if bridge.source == curr {
                    let next_scale = &cum_scale * &bridge.coupling_scale;
                    let next_dim = &cum_dim + &bridge.coupling_dimension;
                    if visited.insert((bridge.target, next_dim.clone())) {
                        let mut next_path = path.clone();
                        next_path.push(bridge.clone());
                        queue.push_back((bridge.target, next_path, next_scale, next_dim));
                    }
                }

                // 2. الاتجاه العكسي التلقائي: target -> source (إذا لم يكن أحادي الاتجاه)
                if !bridge.is_unidirectional && bridge.target == curr {
                    let inv_scale = &Rational::one() / &bridge.coupling_scale;
                    let inv_dim = -bridge.coupling_dimension.clone();
                    let next_scale = &cum_scale * &inv_scale;
                    let next_dim = &cum_dim + &inv_dim;

                    if visited.insert((bridge.source, next_dim.clone())) {
                        let inv_bridge = DomainBridge {
                            name: format!("Inv({})", bridge.name),
                            source: bridge.target,
                            target: bridge.source,
                            coupling_dimension: inv_dim,
                            coupling_scale: inv_scale,
                            is_unidirectional: true,
                        };

                        let mut next_path = path.clone();
                        next_path.push(inv_bridge);
                        queue.push_back((bridge.source, next_path, next_scale, next_dim));
                    }
                }
            }
        }

        None
    }
}

/// القفل الثالث: غربال عزل المجالات وشبكة الجسور متعدية النقل (Seal 3)
pub struct BridgeSieve;

impl BridgeSieve {
    /// فحص عزل المجالات ومصادقة مسار الجسر بين مجالين
    pub fn verify(
        registry: &BridgeRegistry,
        from: DomainTag,
        to: DomainTag,
        required_scale: Option<&Rational>,
        required_dim_gap: Option<&DimensionVector>,
    ) -> LockReceipt {
        if from == to || from == DomainTag::UniversalAbstract || to == DomainTag::UniversalAbstract {
            return LockReceipt::new(
                LockType::DomainIsolationBridge,
                "Domain Isolation Bridge Sieve",
                true,
                "عزل المجالات محقق: المجالات متطابقة أو ذات طبيعة رياضية مجردة عامة",
                None,
            );
        }

        let path_opt = if let Some(req_dim) = required_dim_gap {
            registry.find_bridge_path_matching_dimension(from, to, req_dim)
        } else {
            registry.find_shortest_bridge_path(from, to)
        };

        match path_opt {
            Some((path, cum_scale, cum_dim)) => {
                // التحقق من توافق المقياس التراكمي إن طُلب
                if let Some(req_scale) = required_scale {
                    let inv_req = &Rational::one() / req_scale;
                    if &cum_scale != req_scale && cum_scale != inv_req {
                        return LockReceipt::new(
                            LockType::DomainIsolationBridge,
                            "Bridge Scale Mismatch",
                            false,
                            format!(
                                "مقياس الاقتران التراكمي للجسر ({}) لا يطابق المقياس المطلوب ({})",
                                cum_scale, req_scale
                            ),
                            None,
                        );
                    }
                }

                // التحقق من توافق الفجوة البعدية إن طُلبت
                if let Some(req_dim) = required_dim_gap {
                    let inv_dim = -req_dim.clone();
                    if &cum_dim != req_dim && cum_dim != inv_dim {
                        return LockReceipt::new(
                            LockType::DomainIsolationBridge,
                            "Bridge Dimensional Gap Incoherence",
                            false,
                            format!(
                                "بُعد الاقتران التراكمي ({}) لا يطابق فجوة الأبعاد المطلوبة للعبور ({})",
                                cum_dim, req_dim
                            ),
                            None,
                        );
                    }
                }

                LockReceipt::new(
                    LockType::DomainIsolationBridge,
                    "Domain Isolation Bridge Sieve",
                    true,
                    format!(
                        "تمت مصادقة مسار الجسر بنجاح عبر {} قفزات (مقياس تراكمي: {}، بعد تراكمي: {})",
                        path.len(),
                        cum_scale,
                        cum_dim
                    ),
                    None,
                )
            }
            None => LockReceipt::new(
                LockType::DomainIsolationBridge,
                "Domain Isolation Bridge Sieve",
                false,
                format!(
                    "خرق في عزل المجالات: لا يوجد أي مسار جسر معتمد يربط بين {:?} و {:?}",
                    from, to
                ),
                None,
            ),
        }
    }
}
