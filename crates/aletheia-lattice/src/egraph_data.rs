use crate::error::LatticeError;
use crate::vector::DimensionVector;
use aletheia_algebra::Rational;

/// المجال الدلالي المعرفي للعقدة في الـ E-Graph
#[derive(Copy, Clone, Debug, PartialEq, Eq, Hash)]
pub enum SemanticDomain {
    /// الأبعاد الفيزيائية الأساسية والمشتقة من الطبيعة
    PhysicalCore,
    /// الأبعاد المولدة ديناميكياً (المعلومات، الاقتصاد، النظريات المكتشفة حديثاً)
    DynamicExtended,
    /// الفضاء الرياضي المجرد والكميات اللابُعدية الصرفة
    PureMathematics,
}

/// حاوية البيانات الدلالية الخفيفة الملحقة بكل مجموعة تكافؤ (E-Class Analysis Data) في الـ E-Graph
/// مسؤولة عن فرض الاستقرار الدلالي وإطلاق التراجع المعاملاتي الفوري عند أي تعارض
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct LatticeData {
    pub dim: DimensionVector,
    pub domain: SemanticDomain,
    pub falsification_bounds: Option<(Rational, Rational)>,
}

impl LatticeData {
    pub fn new(dim: DimensionVector, domain: SemanticDomain) -> Self {
        Self {
            dim,
            domain,
            falsification_bounds: None,
        }
    }

    pub fn with_bounds(
        dim: DimensionVector,
        domain: SemanticDomain,
        bounds: (Rational, Rational),
    ) -> Self {
        Self {
            dim,
            domain,
            falsification_bounds: Some(bounds),
        }
    }

    pub fn dimensionless() -> Self {
        Self {
            dim: DimensionVector::dimensionless(),
            domain: SemanticDomain::PureMathematics,
            falsification_bounds: None,
        }
    }

    pub fn physical(dim: DimensionVector) -> Self {
        Self {
            dim,
            domain: SemanticDomain::PhysicalCore,
            falsification_bounds: None,
        }
    }

    /// منطق الدمج الدلالي لمجموعتي تكافؤ في الـ E-Graph (E-Class Merge Analysis)
    /// القاعدة الدستورية الصارمة: إذا اختلفت الأبعاد، يُرفض الدمج فوراً ويُطلق خطأ ContradictoryMerge
    /// لإيقاف العملية وتفعيل التراجع الذري (Atomic Rollback)
    pub fn merge(&self, other: &Self) -> Result<Self, LatticeError> {
        // 1. فحص تطابق الأبعاد مع التمدد الصفري الكنسي
        if self.dim != other.dim {
            return Err(LatticeError::ContradictoryMerge(format!(
                "Dimensional clash during E-Class merge: cannot merge {} with {}",
                self.dim, other.dim
            )));
        }

        // 2. دمج المجالات الدلالية
        let merged_domain = match (self.domain, other.domain) {
            (SemanticDomain::PhysicalCore, _) | (_, SemanticDomain::PhysicalCore) => {
                SemanticDomain::PhysicalCore
            }
            (SemanticDomain::DynamicExtended, _) | (_, SemanticDomain::DynamicExtended) => {
                SemanticDomain::DynamicExtended
            }
            (SemanticDomain::PureMathematics, SemanticDomain::PureMathematics) => {
                SemanticDomain::PureMathematics
            }
        };

        // 3. تقاطع فترات التفنيد العددي (Interval Bounds Intersection)
        let merged_bounds = match (&self.falsification_bounds, &other.falsification_bounds) {
            (Some((min1, max1)), Some((min2, max2))) => {
                let new_min = min1.max(min2).clone();
                let new_max = max1.min(max2).clone();
                if new_min > new_max {
                    return Err(LatticeError::ContradictoryMerge(format!(
                        "Falsification bounds clash: interval [{}, {}] is empty",
                        new_min, new_max
                    )));
                }
                Some((new_min, new_max))
            }
            (Some(b), None) | (None, Some(b)) => Some(b.clone()),
            (None, None) => None,
        };

        Ok(Self {
            dim: self.dim.clone(),
            domain: merged_domain,
            falsification_bounds: merged_bounds,
        })
    }
}
