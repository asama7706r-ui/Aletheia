use crate::error::FormalContradictionError;
use crate::rational::Rational;

/// حساب إشارة كوزول المدرجة (Koszul Graded Parity Sign)
/// (-1)^(deg(a) * deg(b))
/// تحكم بديهية التناظر الموتري المدرج للأشكال التفاضلية وميكانيكا الكم
#[inline]
pub fn koszul_parity_sign(deg_a: u32, deg_b: u32) -> i8 {
    if (deg_a * deg_b) % 2 == 1 {
        -1
    } else {
        1
    }
}

/// إشارة كوزول كعدد كسري صريح في حقل Q
#[inline]
pub fn koszul_parity_rational(deg_a: u32, deg_b: u32) -> Rational {
    Rational::from_i64(koszul_parity_sign(deg_a, deg_b) as i64)
}

/// عنصر مدرج في الجبر المتدرج (Graded Algebra Element)
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct GradedElement<T> {
    pub value: T,
    pub grade: u32,
}

impl<T> GradedElement<T> {
    pub fn new(value: T, grade: u32) -> Self {
        Self { value, grade }
    }

    /// هل العنصر بوزوني تبادلي (درجة زوجية)
    #[inline]
    pub fn is_bosonic(&self) -> bool {
        self.grade.is_multiple_of(2)
    }

    /// هل العنصر فرميوني عكس-تبادلي (درجة فردية)
    #[inline]
    pub fn is_fermionic(&self) -> bool {
        !self.is_bosonic()
    }

    /// حساب معامل التبادل مع عنصر مدرج آخر
    pub fn exchange_sign<U>(&self, other: &GradedElement<U>) -> i8 {
        koszul_parity_sign(self.grade, other.grade)
    }

    /// التحقق من التناظر المدرج
    pub fn verify_commutation_sign<U>(&self, other: &GradedElement<U>, expected_sign: i8) -> Result<(), FormalContradictionError> {
        let actual_sign = self.exchange_sign(other);
        if actual_sign != expected_sign {
            return Err(FormalContradictionError::ParityViolation(format!(
                "Graded commutation failed: grade {} and {} require sign {}, but got {}",
                self.grade, other.grade, actual_sign, expected_sign
            )));
        }
        Ok(())
    }
}

/// تمثيل المؤشرات العلوية والسفلية لتقليص أينشتاين الموتري (Einstein Contraction)
#[derive(Copy, Clone, Debug, PartialEq, Eq, Hash)]
pub struct ContravariantIndex(pub u32); // مؤشر علوي

#[derive(Copy, Clone, Debug, PartialEq, Eq, Hash)]
pub struct CovariantIndex(pub u32);     // مؤشر سفلي

/// تحقق من صحة الاقتران لتقليص أينشتاين (علوي مع سفلي لنفس الرمز)
pub fn can_contract_einstein(upper: ContravariantIndex, lower: CovariantIndex) -> bool {
    upper.0 == lower.0
}
