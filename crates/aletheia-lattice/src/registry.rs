use crate::error::LatticeError;
use crate::vector::DimensionVector;
use aletheia_algebra::Rational;

/// معرّف البعد الأساسي الفهرسي
#[derive(Copy, Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct DimensionId(pub usize);

/// سجل الأبعاد الكونية (Universal Dimension Registry)
/// يُدير قاعدة فضاء الشبكيات النسبي Q^N ويبدأ بالأبعاد الفيزيائية السبعة الأساسية (SI-7)
/// مع قابلية حتمية للتوسع المتعامد عند اكتشاف مجالات جديدة (Orthogonal Extension N -> N+1)
#[derive(Clone, Debug)]
pub struct DimensionRegistry {
    dimension_names: Vec<String>,
}

impl DimensionRegistry {
    /// الثوابت الفهرسية للأبعاد السبعة الأساسية للنظام الدولي
    pub const LENGTH_IDX: usize = 0;      // [L]
    pub const MASS_IDX: usize = 1;        // [M]
    pub const TIME_IDX: usize = 2;        // [T]
    pub const CURRENT_IDX: usize = 3;     // [I]
    pub const TEMPERATURE_IDX: usize = 4; // [Θ]
    pub const SUBSTANCE_IDX: usize = 5;   // [N]
    pub const LUMINOSITY_IDX: usize = 6;  // [J]

    /// تهيئة السجل بالأبعاد السبعة الأساسية الموضوعية (SI Base Dimensions)
    pub fn new() -> Self {
        Self {
            dimension_names: vec![
                "Length".to_string(),
                "Mass".to_string(),
                "Time".to_string(),
                "ElectricCurrent".to_string(),
                "Temperature".to_string(),
                "AmountOfSubstance".to_string(),
                "LuminousIntensity".to_string(),
            ],
        }
    }

    /// عدد الأبعاد المسجلة حالياً في الفضاء (البعد N)
    #[inline]
    pub fn dimension_count(&self) -> usize {
        self.dimension_names.len()
    }

    /// البحث عن بعد بالاسم
    pub fn find_dimension(&self, name: &str) -> Option<DimensionId> {
        self.dimension_names
            .iter()
            .position(|n| n.eq_ignore_ascii_case(name))
            .map(DimensionId)
    }

    /// الحصول على اسم البعد
    pub fn get_name(&self, id: DimensionId) -> Result<&str, LatticeError> {
        self.dimension_names
            .get(id.0)
            .map(|s| s.as_str())
            .ok_or_else(|| LatticeError::DimensionNotFound(format!("ID {}", id.0)))
    }

    /// التوسع المتعامد المباشر: إضافة بعد أولي جديد متعامد تماماً (Orthogonal Base Extension)
    /// V_new = V_current ⊕ Q * e_new
    pub fn register_orthogonal(&mut self, name: &str) -> Result<DimensionId, LatticeError> {
        if self.find_dimension(name).is_some() {
            return Err(LatticeError::LinearDependence(format!(
                "Dimension '{}' already exists in registry",
                name
            )));
        }
        let new_id = DimensionId(self.dimension_names.len());
        self.dimension_names.push(name.to_string());
        Ok(new_id)
    }

    /// توليد متجه الأساس المتعامد لبعد معين e_k
    pub fn unit_basis(&self, id: DimensionId) -> Result<DimensionVector, LatticeError> {
        if id.0 >= self.dimension_names.len() {
            return Err(LatticeError::DimensionNotFound(format!("ID {}", id.0)));
        }
        Ok(DimensionVector::unit_basis(id.0, self.dimension_names.len()))
    }

    // =========================================================================
    // دوال مساعدة سريعة للأبعاد السبعة الأساسية
    // =========================================================================

    #[inline]
    pub fn dimensionless(&self) -> DimensionVector {
        DimensionVector::dimensionless()
    }

    #[inline]
    pub fn length(&self) -> DimensionVector {
        DimensionVector::unit_basis(Self::LENGTH_IDX, self.dimension_names.len())
    }

    #[inline]
    pub fn mass(&self) -> DimensionVector {
        DimensionVector::unit_basis(Self::MASS_IDX, self.dimension_names.len())
    }

    #[inline]
    pub fn time(&self) -> DimensionVector {
        DimensionVector::unit_basis(Self::TIME_IDX, self.dimension_names.len())
    }

    #[inline]
    pub fn current(&self) -> DimensionVector {
        DimensionVector::unit_basis(Self::CURRENT_IDX, self.dimension_names.len())
    }

    #[inline]
    pub fn temperature(&self) -> DimensionVector {
        DimensionVector::unit_basis(Self::TEMPERATURE_IDX, self.dimension_names.len())
    }

    #[inline]
    pub fn substance(&self) -> DimensionVector {
        DimensionVector::unit_basis(Self::SUBSTANCE_IDX, self.dimension_names.len())
    }

    #[inline]
    pub fn luminosity(&self) -> DimensionVector {
        DimensionVector::unit_basis(Self::LUMINOSITY_IDX, self.dimension_names.len())
    }

    // =========================================================================
    // دوال مساعدة لأشهر الأبعاد المشتقة (Derived Dimensions)
    // =========================================================================

    /// المساحة: [L^2]
    pub fn area(&self) -> DimensionVector {
        self.length().scale(&Rational::from_i64(2))
    }

    /// الحجم: [L^3]
    pub fn volume(&self) -> DimensionVector {
        self.length().scale(&Rational::from_i64(3))
    }

    /// السرعة: [L * T^(-1)]
    pub fn velocity(&self) -> DimensionVector {
        self.length() - self.time()
    }

    /// التسارع: [L * T^(-2)]
    pub fn acceleration(&self) -> DimensionVector {
        self.length() - self.time().scale(&Rational::from_i64(2))
    }

    /// القوة: [M * L * T^(-2)] (نيوتن)
    pub fn force(&self) -> DimensionVector {
        self.mass() + self.acceleration()
    }

    /// الطاقة / الشغل: [M * L^2 * T^(-2)] (جول)
    pub fn energy(&self) -> DimensionVector {
        self.force() + self.length()
    }

    /// القدرة: [M * L^2 * T^(-3)] (واط)
    pub fn power(&self) -> DimensionVector {
        self.energy() - self.time()
    }

    /// التردد: [T^(-1)] (هيرتز)
    pub fn frequency(&self) -> DimensionVector {
        -self.time()
    }
}

impl Default for DimensionRegistry {
    fn default() -> Self {
        Self::new()
    }
}
