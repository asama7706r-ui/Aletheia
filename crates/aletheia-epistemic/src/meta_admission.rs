use crate::error::EpistemicError;
use crate::seal_bridge::{BridgeRegistry, DomainBridge, DomainTag};
use aletheia_algebra::Rational;
use aletheia_egraph::TransactionalEGraph;
use aletheia_lattice::{DimensionVector, RationalMatrix};
use blake3::Hasher;

/// مقترح تدشين جسر أنطولوجي جديد عابر للمجالات (CandidateBridge)
/// يخضع لبروتوكول التدشين التوليدي المكون من 4 أقفال ميتا-معرفية
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CandidateBridge {
    pub bridge_id: [u8; 32],
    pub name: String,
    pub source_domain: DomainTag,
    pub target_domain: DomainTag,
    pub coupling_dimension: DimensionVector,
    pub coupling_scale: Rational,
    pub is_unidirectional: bool,
}

impl CandidateBridge {
    pub fn new(
        name: impl Into<String>,
        source_domain: DomainTag,
        target_domain: DomainTag,
        coupling_dimension: DimensionVector,
        coupling_scale: Rational,
    ) -> Self {
        let name_str = name.into();
        let mut hasher = Hasher::new();
        hasher.update(name_str.as_bytes());
        hasher.update(format!("{:?}->{:?}", source_domain, target_domain).as_bytes());
        hasher.update(coupling_scale.to_string().as_bytes());
        for i in 0..coupling_dimension.len() {
            hasher.update(coupling_dimension.get_coord(i).to_string().as_bytes());
        }
        let bridge_id = *hasher.finalize().as_bytes();

        Self {
            bridge_id,
            name: name_str,
            source_domain,
            target_domain,
            coupling_dimension,
            coupling_scale,
            is_unidirectional: false,
        }
    }

    pub fn with_unidirectional(mut self, unidir: bool) -> Self {
        self.is_unidirectional = unidir;
        self
    }
}

/// مقترح تدشين بُعد أساسي جديد في شبيكة الأبعاد (CandidateDimension)
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CandidateDimension {
    pub dimension_id: [u8; 32],
    pub name: String,
    pub unit_symbol: String,
    pub existing_components: DimensionVector,
}

impl CandidateDimension {
    pub fn new(
        name: impl Into<String>,
        unit_symbol: impl Into<String>,
        existing_components: DimensionVector,
    ) -> Self {
        let name_str = name.into();
        let unit_str = unit_symbol.into();
        let mut hasher = Hasher::new();
        hasher.update(name_str.as_bytes());
        hasher.update(unit_str.as_bytes());
        for i in 0..existing_components.len() {
            hasher.update(existing_components.get_coord(i).to_string().as_bytes());
        }
        let dimension_id = *hasher.finalize().as_bytes();

        Self {
            dimension_id,
            name: name_str,
            unit_symbol: unit_str,
            existing_components,
        }
    }
}

/// سجل الأبعاد الأساسية وفضاء الشبيكة الدلالية Q^N
#[derive(Clone, Debug)]
pub struct DimensionRegistry {
    pub dimensions: Vec<(String, String)>,
    pub basis: Vec<DimensionVector>,
}

impl Default for DimensionRegistry {
    fn default() -> Self {
        Self::new()
    }
}

impl DimensionRegistry {
    pub fn new() -> Self {
        Self {
            dimensions: Vec::new(),
            basis: Vec::new(),
        }
    }

    /// إنشاء سجل الأبعاد المعياري للنظام الدولي (SI-7 Standard)
    pub fn standard_si() -> Self {
        let si_defs = [
            ("Length", "m"),
            ("Mass", "kg"),
            ("Time", "s"),
            ("ElectricCurrent", "A"),
            ("Temperature", "K"),
            ("AmountOfSubstance", "mol"),
            ("LuminousIntensity", "cd"),
        ];

        let mut reg = Self::new();
        for (i, (name, unit)) in si_defs.iter().enumerate() {
            reg.dimensions.push((name.to_string(), unit.to_string()));
            reg.basis.push(DimensionVector::unit_basis(i, 7));
        }
        reg
    }

    /// فحص الاستقلال الخطي الصارم للبُعد المرشح في حقل الأعداد النسبية Q
    /// يحل المعادلة A * x = v عبر خوارزمية RREF الدقيقة:
    /// إذا كان العمود الأخير محوَر ارتكاز Pivot => لا يوجد حل في Span(basis) => مستقل خطياً بنسبة 100%!
    pub fn is_linearly_independent(&self, candidate: &DimensionVector) -> bool {
        if candidate.is_dimensionless() {
            return false;
        }
        if self.basis.is_empty() {
            return true;
        }

        let k = self.basis.len();
        let max_dim = candidate.len().max(self.basis.iter().map(|b| b.len()).max().unwrap_or(0));
        let num_rows = max_dim.max(1);
        let num_cols = k + 1;

        let mut matrix = RationalMatrix::new(num_rows, num_cols);

        // أعمدة الأساس القائم 0..k
        for (col_idx, b) in self.basis.iter().enumerate() {
            for row_idx in 0..num_rows {
                matrix.set(row_idx, col_idx, b.get_coord(row_idx));
            }
        }

        // العمود الموسع k: متجه البعد المرشح
        for row_idx in 0..num_rows {
            matrix.set(row_idx, k, candidate.get_coord(row_idx));
        }

        let (_rank, pivot_cols) = matrix.rref();

        // إذا كان العمود k من بين أعمدة الارتكاز، فهذا يعني وجود صف [0 ... 0 | 1]
        // أي أن المتجه يقع خارج الفضاء المولد Span، وبالتالي هو مستقل خطياً!
        pivot_cols.contains(&k)
    }

    /// ترقية الشبيكة وتدشين البعد الجديد Q^N -> Q^(N+1)
    pub fn admit_dimension(
        &mut self,
        candidate: &CandidateDimension,
    ) -> Result<usize, EpistemicError> {
        if !self.is_linearly_independent(&candidate.existing_components) {
            return Err(EpistemicError::MetaAdmissionRejected(format!(
                "البعد المرشح '{}' غير مستقل خطياً ويقع ضمن الفضاء المولد للأبعاد القائمة في Q^N",
                candidate.name
            )));
        }

        let new_index = self.basis.len();
        self.dimensions
            .push((candidate.name.clone(), candidate.unit_symbol.clone()));

        // المتجه الجديد يشغل وحدة الأساس الجديدة e_{new}
        let total_new_len = new_index + 1;
        self.basis
            .push(DimensionVector::unit_basis(new_index, total_new_len));

        Ok(new_index)
    }
}

/// بروتوكول التدشين التوليدي للجسور والأبعاد (Meta-Admission Protocol)
pub struct MetaAdmissionProtocol;

impl MetaAdmissionProtocol {
    /// تدشين جسر أنطولوجي جديد عبر الأقفال الأربعة الميتا-معرفية
    pub fn admit_bridge(
        registry: &BridgeRegistry,
        candidate: &CandidateBridge,
        source_dim: Option<&DimensionVector>,
        target_dim: Option<&DimensionVector>,
        egraph_opt: Option<&mut TransactionalEGraph>,
    ) -> Result<DomainBridge, EpistemicError> {
        // 1. القفل 1 (البواقي): التحقق من أن مقياس الاقتران غير صفري وصالح في Q
        if candidate.coupling_scale.is_zero() {
            return Err(EpistemicError::ResidualViolation(
                "مقياس الاقتران للجسر لا يمكن أن يكون صفراً مطلقاً في Q".to_string(),
            ));
        }

        // 2. القفل 2 (التجانس البعدي): التحقق من أن بُعد الاقتران يطابق عجز المجالين تماماً
        if let (Some(src_d), Some(tgt_d)) = (source_dim, target_dim) {
            let expected_dim = tgt_d - src_d;
            if candidate.coupling_dimension != expected_dim {
                return Err(EpistemicError::DimensionalClash(format!(
                    "بُعد اقتران الجسر لا يطابق الفرق البعدي بين المجالين: المتوقع {:?} والمسجل {:?}",
                    expected_dim, candidate.coupling_dimension
                )));
            }
        }

        // 3. القفل 3 (التوافق الفانكتوري - Functor Commutativity):
        // إذا كان هناك مسار قائم متعدد القفزات يربط بين نفس المجالين بنفس بُعد الاقتران،
        // يجب أن يتطابق مقياس الاقتران تماماً صوناً لمبدأ المخطط التبديلاتي (Commutative Diagram).
        // أما إذا كان بُعد الاقتران مختلفاً، فهو يمثل قناة اقتران فيزيائية مستقلة ومتعامدة (Orthogonal Coupling Channel).
        if let Some((path, existing_scale, _)) = registry.find_bridge_path_matching_dimension(
            candidate.source_domain,
            candidate.target_domain,
            &candidate.coupling_dimension,
        ) {
            if !path.is_empty() && candidate.coupling_scale != existing_scale {
                return Err(EpistemicError::MetaAdmissionRejected(format!(
                    "خرق في التوافق الفانكتوري: يوجد مسار قائم بنفس بُعد الاقتران {:?} بمقياس اقتران {} بينما الجسر المرشح له مقياس {}",
                    candidate.coupling_dimension, existing_scale, candidate.coupling_scale
                )));
            }
        }

        // 4. القفل 4 (التركيب التجريبي المعزول - Speculative Mounting):
        // اختبار التماسك في بيئة العزل بالـ E-Graph إن تم تزويده
        if let Some(egraph) = egraph_opt {
            let cp = egraph.checkpoint();
            let rebuild_res = egraph.rebuild();
            egraph.rollback(cp);

            if let Err(e) = rebuild_res {
                return Err(EpistemicError::OntologicalAnchorViolation(format!(
                    "فشل التركيب التجريبي للجسر في الـ E-Graph: {}",
                    e
                )));
            }
        }

        let mut bridge = DomainBridge::new(
            candidate.name.clone(),
            candidate.source_domain,
            candidate.target_domain,
            candidate.coupling_dimension.clone(),
            candidate.coupling_scale.clone(),
        );

        if candidate.is_unidirectional {
            bridge = bridge.unidirectional();
        }

        Ok(bridge)
    }

    /// تدشين بعد فيزيائي أساسي جديد في شبيكة الأبعاد
    pub fn admit_dimension(
        dim_registry: &mut DimensionRegistry,
        candidate: &CandidateDimension,
    ) -> Result<usize, EpistemicError> {
        dim_registry.admit_dimension(candidate)
    }
}
