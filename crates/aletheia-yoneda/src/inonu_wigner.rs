use crate::error::YonedaError;
use aletheia_algebra::{Monomial, MonomialOrder, Polynomial, Rational, Term, VariableId};

/// تمثيل جبر لي عبر مصفوفة ثلاثية كسرية لثوابت البنية C_{ij}^k في Q
/// خالي 100% من أي أعداد عائمة (Zero Float Drift)
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct LieAlgebra {
    /// بعد الجبر n (عدد المولدات المستقلة)
    pub dim: usize,
    /// أسماء المولدات لسهولة التتبع والتوثيق البرهاني
    pub generator_names: Vec<String>,
    /// مصفوفة ثوابت البنية ثلاثية الأبعاد: [i][j][k] حيث [X_i, X_j] = sum_k C_{ij}^k X_k
    pub structure_constants: Vec<Vec<Vec<Rational>>>,
}

impl LieAlgebra {
    /// إنشاء جبر لي جديد بعدد n من المولدات
    pub fn new(dim: usize, generator_names: Vec<String>) -> Self {
        assert_eq!(generator_names.len(), dim);
        let structure_constants = vec![vec![vec![Rational::zero(); dim]; dim]; dim];
        Self {
            dim,
            generator_names,
            structure_constants,
        }
    }

    /// ضبط ثابت بنية C_{ij}^k مع تطبيق التناظر العكسي C_{ji}^k = -C_{ij}^k تلقائياً
    pub fn set_bracket(&mut self, i: usize, j: usize, k: usize, val: Rational) {
        assert!(i < self.dim && j < self.dim && k < self.dim);
        if i == j {
            assert!(val.is_zero(), "ثابت القوس لمولد مع نفسه يجب أن يكون صفراً");
            return;
        }
        self.structure_constants[i][j][k] = val.clone();
        self.structure_constants[j][i][k] = -val;
    }

    /// استرجاع ثابت البنية C_{ij}^k
    #[inline]
    pub fn get_c(&self, i: usize, j: usize, k: usize) -> &Rational {
        &self.structure_constants[i][j][k]
    }

    /// التحقق الصارم من متطابقة ياكوبي (Jacobi Identity) لجميع الرباعيات (i, j, k, l)
    /// sum_m (C_{ij}^m C_{mk}^l + C_{jk}^m C_{mi}^l + C_{ki}^m C_{mj}^l) == 0
    pub fn verify_jacobi_identity(&self) -> Result<(), YonedaError> {
        let n = self.dim;
        for i in 0..n {
            for j in 0..n {
                for k in 0..n {
                    for l in 0..n {
                        let mut sum = Rational::zero();
                        for m in 0..n {
                            let term1 = self.get_c(i, j, m) * self.get_c(m, k, l);
                            let term2 = self.get_c(j, k, m) * self.get_c(m, i, l);
                            let term3 = self.get_c(k, i, m) * self.get_c(m, j, l);
                            sum += term1 + term2 + term3;
                        }
                        if !sum.is_zero() {
                            return Err(YonedaError::JacobiViolation(format!(
                                "فشل متطابقة ياكوبي للرباعية ({}, {}, {}, {}) حيث المجموع = {}",
                                self.generator_names[i],
                                self.generator_names[j],
                                self.generator_names[k],
                                self.generator_names[l],
                                sum
                            )));
                        }
                    }
                }
            }
        }
        Ok(())
    }

    /// إنشاء جبر الدوران ثلاثي الأبعاد so(3)
    pub fn so3() -> Self {
        let mut alg = Self::new(
            3,
            vec!["J1".to_string(), "J2".to_string(), "J3".to_string()],
        );
        // [J1, J2] = J3
        alg.set_bracket(0, 1, 2, Rational::one());
        // [J2, J3] = J1
        alg.set_bracket(1, 2, 0, Rational::one());
        // [J3, J1] = J2
        alg.set_bracket(2, 0, 1, Rational::one());

        alg
    }
}

/// محرك انكماش إينونو-فيغنر (Inönü-Wigner Contraction Engine)
/// يحول جبر لي إلى جبر آخر عبر معامل تقاربي بارامتري epsilon -> 0
/// باستخدام كثيرات الحدود الصرفة فوق حقل الأعداد النسبية Q
pub struct InonuWignerContraction;

impl InonuWignerContraction {
    /// حساب انكماش جبر لي وفق متجه التدريج s = (s_0, s_1, ..., s_{n-1}) حيث X'_i = epsilon^{s_i} X_i
    /// يولد كثيرات الحدود C~_{ij}^k(epsilon) ويقوم بتقييمها برهانياً عند epsilon = 0
    pub fn contract(
        original: &LieAlgebra,
        scaling_powers: &[u32],
        contracted_names: Vec<String>,
    ) -> Result<LieAlgebra, YonedaError> {
        let n = original.dim;
        if scaling_powers.len() != n {
            return Err(YonedaError::SingularContraction(format!(
                "أبعاد متجه التدريج ({}) لا تطابق بعد الجبر ({})",
                scaling_powers.len(),
                n
            )));
        }

        // تحقق من شرط الانكماش غير المنفرد: s_i + s_j >= s_k لكل C_{ij}^k != 0
        for i in 0..n {
            for j in 0..n {
                for k in 0..n {
                    let c_val = original.get_c(i, j, k);
                    if !c_val.is_zero() {
                        let si = scaling_powers[i] as i64;
                        let sj = scaling_powers[j] as i64;
                        let sk = scaling_powers[k] as i64;
                        let power_diff = si + sj - sk;
                        if power_diff < 0 {
                            return Err(YonedaError::SingularContraction(format!(
                                "انكماش منفرد ومتباعد: الأس الكلي ({}) سالب عند ({}, {}, {})",
                                power_diff, i, j, k
                            )));
                        }
                    }
                }
            }
        }

        // بناء كثير حدود بارامتري لكل ثابت بنية وتقييمه عند epsilon = 0
        // المتغير epsilon = VariableId(9999)
        let eps_var = VariableId(9999);
        let mut contracted = LieAlgebra::new(n, contracted_names);

        for i in 0..n {
            for j in (i + 1)..n {
                for k in 0..n {
                    let c_val = original.get_c(i, j, k);
                    if c_val.is_zero() {
                        continue;
                    }

                    let si = scaling_powers[i];
                    let sj = scaling_powers[j];
                    let sk = scaling_powers[k];
                    let power = (si + sj) - sk;

                    // إنشاء كثير الحدود P(epsilon) = C_{ij}^k * epsilon^power
                    let poly = if power == 0 {
                        Polynomial::constant(c_val.clone())
                    } else {
                        let term = Term::new(
                            c_val.clone(),
                            Monomial::variable(eps_var, power),
                        );
                        Polynomial::from_terms(vec![term], MonomialOrder::DegRevLex)
                    };

                    // تقييم كثير الحدود عند epsilon = 0
                    // إذا كان power > 0 فالناتج صفر، وإذا كان power == 0 فالناتج هو c_val
                    let contracted_val = Self::evaluate_at_zero(&poly, eps_var);
                    if !contracted_val.is_zero() {
                        contracted.set_bracket(i, j, k, contracted_val);
                    }
                }
            }
        }

        // التحقق من صحة متطابقة ياكوبي للجبر المنكمش الجديد
        contracted.verify_jacobi_identity()?;

        Ok(contracted)
    }

    /// تقييم كثير حدود عند تعويض المتغير var = 0
    fn evaluate_at_zero(poly: &Polynomial, var: VariableId) -> Rational {
        let mut result = Rational::zero();
        for term in poly.terms() {
            let mut contains_var = false;
            for &(v, pow) in term.monomial.factors() {
                if v == var && pow > 0 {
                    contains_var = true;
                    break;
                }
            }
            // الحد الذي لا يحتوي على المتغير هو الحد الثابت الذي يتبقى عند التعويض بصفر
            if !contains_var {
                result += term.coeff.clone();
            }
        }
        result
    }
}
