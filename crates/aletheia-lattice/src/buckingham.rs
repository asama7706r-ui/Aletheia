use crate::rref::RationalMatrix;
use crate::vector::DimensionVector;
use aletheia_algebra::Rational;
use std::fmt;

/// تمثيل متغير فيزيائي يدخل في تحليل باكنغهام باي
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PhysicalVariable {
    pub symbol: String,
    pub dimension: DimensionVector,
}

impl PhysicalVariable {
    pub fn new(symbol: impl Into<String>, dimension: DimensionVector) -> Self {
        Self {
            symbol: symbol.into(),
            dimension,
        }
    }
}

/// مجموعة لابُعدية (Dimensionless Pi-Group) مستخرجة بنظرية باكنغهام
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct DimensionlessGroup {
    pub exponents: Vec<(String, Rational)>,
}

impl DimensionlessGroup {
    /// التحقق من أن المجموعة لا بُعدية بالكامل عند ضرب أبعاد المتغيرات بأسسها
    pub fn verify_dimensionless(&self, variables: &[PhysicalVariable]) -> bool {
        let mut total_dim = DimensionVector::dimensionless();
        for (sym, exp) in &self.exponents {
            if let Some(var) = variables.iter().find(|v| &v.symbol == sym) {
                total_dim += var.dimension.scale(exp);
            }
        }
        total_dim.is_dimensionless()
    }
}

impl fmt::Display for DimensionlessGroup {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let mut printed = false;
        for (sym, exp) in &self.exponents {
            if exp.is_zero() {
                continue;
            }
            if printed {
                write!(f, " * ")?;
            }
            if exp.is_one() {
                write!(f, "{}", sym)?;
            } else {
                write!(f, "{}^({})", sym, exp)?;
            }
            printed = true;
        }
        if !printed {
            write!(f, "1")
        } else {
            Ok(())
        }
    }
}

/// محرك نظرية باي لباكنغهام عبر الفضاء الصفري النسبي الصرف (Rational Buckingham Pi Engine)
pub struct BuckinghamPiEngine;

impl BuckinghamPiEngine {
    /// تطبيق نظرية باكنغهام باي على مجموعة من المتغيرات الفيزيائية
    /// n: عدد المتغيرات
    /// k: رتبة مصفوفة الأبعاد
    /// عدد الأعداد اللابُعدية p = n - k
    pub fn analyze(variables: &[PhysicalVariable]) -> Vec<DimensionlessGroup> {
        let n = variables.len();
        if n == 0 {
            return Vec::new();
        }

        // إيجاد أقصى بعد مسجل عبر كل المتغيرات
        let max_dim = variables.iter().map(|v| v.dimension.effective_len()).max().unwrap_or(0);
        if max_dim == 0 {
            // جميع المتغيرات لا بعدية أصلاً
            return variables
                .iter()
                .map(|v| DimensionlessGroup {
                    exponents: vec![(v.symbol.clone(), Rational::from_i64(1))],
                })
                .collect();
        }

        // بناء مصفوفة الأبعاد M ذات الحجم (max_dim x n)
        // كل عمود j يمثل إحداثيات المتغير variables[j]
        let mut mat = RationalMatrix::new(max_dim, n);
        for (j, var) in variables.iter().enumerate() {
            for i in 0..max_dim {
                mat.set(i, j, var.dimension.get_coord(i));
            }
        }

        // حساب أساس الفضاء الصفري النسبي بدقة حقل Q دون أي نقطة عائمة
        let nullspace_basis = mat.nullspace();

        // تحويل كل متجه حل في الفضاء الصفري إلى مجموعة لابُعدية Pi_i
        let mut groups = Vec::with_capacity(nullspace_basis.len());
        for sol in nullspace_basis {
            let mut exponents = Vec::new();
            for (j, var) in variables.iter().enumerate() {
                let exp = &sol[j];
                if !exp.is_zero() {
                    exponents.push((var.symbol.clone(), exp.clone()));
                }
            }
            let group = DimensionlessGroup { exponents };
            debug_assert!(group.verify_dimensionless(variables));
            groups.push(group);
        }

        groups
    }
}
