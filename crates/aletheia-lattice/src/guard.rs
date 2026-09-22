use crate::error::LatticeError;
use crate::vector::DimensionVector;
use aletheia_algebra::{CanonicalExpr, Polynomial, Rational, VariableId};
use std::collections::HashMap;

/// بيئة السياق البُعدي (Dimensional Context)
/// تربط معرّفات المتغيرات الرقمية VariableId بمتجهاتها البُعدية الفيزيائية في Q^N
#[derive(Clone, Debug, Default)]
pub struct DimensionalContext {
    bindings: HashMap<VariableId, DimensionVector>,
    default_dim: Option<DimensionVector>,
}

impl DimensionalContext {
    pub fn new() -> Self {
        Self {
            bindings: HashMap::new(),
            default_dim: None,
        }
    }

    /// سياق رياضي مجرد: تعامل المتغيرات غير المسجلة صراحة كأعداد لا بُعدية [1]
    pub fn mathematical() -> Self {
        Self {
            bindings: HashMap::new(),
            default_dim: Some(DimensionVector::dimensionless()),
        }
    }

    /// تعيين بعد افتراضي للمتغيرات غير المسجلة
    pub fn with_default_dimension(mut self, dim: DimensionVector) -> Self {
        self.default_dim = Some(dim);
        self
    }

    /// ربط متغير بمتجه أبعاد فيزيائي
    pub fn bind(&mut self, var: VariableId, dim: DimensionVector) {
        self.bindings.insert(var, dim);
    }

    /// استرجاع متجه أبعاد متغير مع الرجوع للبعد الافتراضي إن وجد
    pub fn get(&self, var: VariableId) -> Option<&DimensionVector> {
        self.bindings.get(&var).or(self.default_dim.as_ref())
    }

    /// عدد المتغيرات المعرفة في السياق
    pub fn len(&self) -> usize {
        self.bindings.len()
    }

    pub fn is_empty(&self) -> bool {
        self.bindings.is_empty()
    }
}

/// حارس القبول الدلالي الصارم (Semantic Admissibility Guard)
/// يفحص شجرة التعبيرات الكنسية CanonicalExpr وكثيرات الحدود قبل إدخالها للـ E-Graph
pub struct SemanticGuard;

impl SemanticGuard {
    /// استنتاج متجه الأبعاد لشجرة تعبيرات كنسية مع فرض شرط التجانس الجمعي وحراسة الأسس
    pub fn infer_dimension(
        expr: &CanonicalExpr,
        ctx: &DimensionalContext,
    ) -> Result<DimensionVector, LatticeError> {
        match expr {
            // الثوابت العددية المجردة هي دائماً لا بُعدية [1]
            CanonicalExpr::Const(_) => Ok(DimensionVector::dimensionless()),

            // المتغيرات تُسترجع أبعادها من سياق الأبعاد
            CanonicalExpr::Var(v) => ctx
                .get(*v)
                .cloned()
                .ok_or(LatticeError::VariableDimensionMissing(v.0)),

            // النفي الجمعي يحتفظ بنفس الأبعاد
            CanonicalExpr::Neg(inner) => Self::infer_dimension(inner, ctx),

            // شرط التجانس الجمعي الصارم: A + B <=> d_A == d_B
            CanonicalExpr::Add(operands) => {
                if operands.is_empty() {
                    return Ok(DimensionVector::dimensionless());
                }

                let expected_dim = Self::infer_dimension(&operands[0], ctx)?;

                for op in &operands[1..] {
                    let actual_dim = Self::infer_dimension(op, ctx)?;
                    if expected_dim != actual_dim {
                        return Err(LatticeError::IncompatibleDimensions {
                            expected: expected_dim.to_string(),
                            actual: actual_dim.to_string(),
                        });
                    }
                }

                Ok(expected_dim)
            }

            // الضرب: جمع متجهات الأبعاد [A * B] = d_A + d_B
            CanonicalExpr::Mul(operands) => {
                let mut total_dim = DimensionVector::dimensionless();
                for op in operands {
                    total_dim += Self::infer_dimension(op, ctx)?;
                }
                Ok(total_dim)
            }

            // القسمة: طرح متجهات الأبعاد [A / B] = d_A - d_B
            CanonicalExpr::Div(num, den) => {
                let num_dim = Self::infer_dimension(num, ctx)?;
                let den_dim = Self::infer_dimension(den, ctx)?;
                Ok(num_dim - den_dim)
            }

            // الرفع لقوة: ضرب المتجه في الأس الصحيح (موجب أو سالب) [A^k] = k * d_A
            CanonicalExpr::Pow(base, exp) => {
                let base_dim = Self::infer_dimension(base, ctx)?;
                let exp_rat = Rational::from_i64(*exp as i64);
                Ok(base_dim.scale(&exp_rat))
            }
        }
    }

    /// حارس المتساميات (Transcendental Invariant)
    /// يفرض أن مدخلات الدوال المتسامية التحليلية (sin, cos, exp, ln) يجب أن تكون لا بُعدية تماماً
    pub fn check_transcendental_argument(dim: &DimensionVector) -> Result<(), LatticeError> {
        if !dim.is_dimensionless() {
            return Err(LatticeError::TranscendentalArgumentNotDimensionless(
                dim.to_string(),
            ));
        }
        Ok(())
    }

    /// فحص التجانس البُعدي لكثير حدود Polynomial
    /// يتأكد من أن جميع حدود كثير الحدود تمتلك نفس متجه الأبعاد بالضبط
    pub fn verify_polynomial_homogeneity(
        poly: &Polynomial,
        ctx: &DimensionalContext,
    ) -> Result<DimensionVector, LatticeError> {
        if poly.is_zero() {
            return Ok(DimensionVector::dimensionless());
        }

        let mut expected_dim: Option<DimensionVector> = None;

        for term in poly.terms() {
            // حساب أبعاد المونوم كتركيب خطي
            let mut term_dim = DimensionVector::dimensionless();
            for &(var, pow) in term.monomial.factors() {
                let var_dim = ctx
                    .get(var)
                    .ok_or(LatticeError::VariableDimensionMissing(var.0))?;
                let pow_rat = Rational::from_i64(pow as i64);
                term_dim += var_dim.scale(&pow_rat);
            }

            match &expected_dim {
                None => expected_dim = Some(term_dim),
                Some(exp) => {
                    if exp != &term_dim {
                        return Err(LatticeError::IncompatibleDimensions {
                            expected: exp.to_string(),
                            actual: term_dim.to_string(),
                        });
                    }
                }
            }
        }

        Ok(expected_dim.unwrap_or_else(DimensionVector::dimensionless))
    }
}
