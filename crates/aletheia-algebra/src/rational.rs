use crate::error::FormalContradictionError;
use num_bigint::BigInt;
use num_rational::Ratio;
use num_traits::{One, Signed, Zero};
use std::fmt;
use std::ops::{Add, AddAssign, Div, DivAssign, Mul, MulAssign, Neg, Sub, SubAssign};

/// كائن مصمت ومغلف (Opaque Wrapper) لحقل الأعداد الكسرية الصرفة Q
/// يضمن الانعدام التام للأعداد العائمة (Zero Float Drift) ويسمح بالتحسين الداخلي مستقبلاً
#[derive(Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Rational {
    inner: Ratio<BigInt>,
}

impl Rational {
    /// إنشاء كسر من بسط ومقام (مع التحقق من الصفر في المقام)
    #[inline]
    pub fn new(numer: i64, denom: i64) -> Result<Self, FormalContradictionError> {
        if denom == 0 {
            return Err(FormalContradictionError::DivisionByZero);
        }
        Ok(Self {
            inner: Ratio::new(BigInt::from(numer), BigInt::from(denom)),
        })
    }

    /// إنشاء كسر صحيح مباشرة من i64
    #[inline]
    pub fn from_i64(val: i64) -> Self {
        Self {
            inner: Ratio::from_integer(BigInt::from(val)),
        }
    }

    /// إنشاء كسر من أعداد BigInt
    #[inline]
    pub fn from_bigint(numer: BigInt, denom: BigInt) -> Result<Self, FormalContradictionError> {
        if denom.is_zero() {
            return Err(FormalContradictionError::DivisionByZero);
        }
        Ok(Self {
            inner: Ratio::new(numer, denom),
        })
    }

    /// العنصر المحايد الجمعي (0)
    #[inline]
    pub fn zero() -> Self {
        <Self as Zero>::zero()
    }

    /// العنصر المحايد الضربي (1)
    #[inline]
    pub fn one() -> Self {
        <Self as One>::one()
    }

    /// مرجع للبسط
    #[inline]
    pub fn numer(&self) -> &BigInt {
        self.inner.numer()
    }

    /// مرجع للمقام
    #[inline]
    pub fn denom(&self) -> &BigInt {
        self.inner.denom()
    }

    /// هل العدد يساوي صفراً
    #[inline]
    pub fn is_zero(&self) -> bool {
        self.inner.is_zero()
    }

    /// هل العدد يساوي واحداً
    #[inline]
    pub fn is_one(&self) -> bool {
        self.inner.is_one()
    }

    /// هل العدد سالب
    #[inline]
    pub fn is_negative(&self) -> bool {
        self.inner.is_negative()
    }

    /// هل العدد موجب
    #[inline]
    pub fn is_positive(&self) -> bool {
        self.inner.is_positive()
    }

    /// هل الكسر يمثل عدداً صحيحاً (المقام يساوي 1)
    #[inline]
    pub fn is_integer(&self) -> bool {
        self.inner.is_integer()
    }

    /// تحويل الكسر إلى i64 إذا أمكن دون فقدان للدقة
    pub fn to_i64(&self) -> Option<i64> {
        if self.is_integer() {
            num_traits::ToPrimitive::to_i64(self.numer())
        } else {
            None
        }
    }

    /// حساب حجم التمثيل الثنائي الدقيق للكسر (بالبت) دون أي أعداد عائمة (Zero Float Drift)
    /// يعتمد كلياً على BigInt::bits() لحساب طول البسط والمقام
    #[inline]
    pub fn bitsize(&self) -> u64 {
        let n_bits = self.numer().bits().max(1);
        let d_bits = self.denom().bits().max(1);
        n_bits + d_bits
    }

    /// المعكوس الضربي الحتمي (مع رفع استثناء عند الصفر)
    pub fn inv(&self) -> Result<Self, FormalContradictionError> {
        if self.is_zero() {
            return Err(FormalContradictionError::DivisionByZero);
        }
        Ok(Self {
            inner: self.inner.recip(),
        })
    }

    /// قسمة محققة ترفع استثناءً عند القسمة على صفر
    pub fn checked_div(&self, rhs: &Self) -> Result<Self, FormalContradictionError> {
        if rhs.is_zero() {
            return Err(FormalContradictionError::DivisionByZero);
        }
        Ok(Self {
            inner: &self.inner / &rhs.inner,
        })
    }

    /// حساب القوة الصحيحة غير السالبة
    pub fn pow(&self, exp: u32) -> Self {
        if exp == 0 {
            return Self::one();
        }
        let mut base = self.clone();
        let mut result = Self::one();
        let mut e = exp;
        while e > 0 {
            if e % 2 == 1 {
                result = &result * &base;
            }
            if e > 1 {
                base = &base * &base;
            }
            e /= 2;
        }
        result
    }

    /// القيمة المطلقة
    #[inline]
    pub fn abs(&self) -> Self {
        Self {
            inner: self.inner.abs(),
        }
    }
}

impl Zero for Rational {
    #[inline]
    fn zero() -> Self {
        Self {
            inner: Ratio::zero(),
        }
    }

    #[inline]
    fn is_zero(&self) -> bool {
        self.inner.is_zero()
    }
}

impl One for Rational {
    #[inline]
    fn one() -> Self {
        Self {
            inner: Ratio::one(),
        }
    }

    #[inline]
    fn is_one(&self) -> bool {
        self.inner.is_one()
    }
}

impl Default for Rational {
    #[inline]
    fn default() -> Self {
        Self::zero()
    }
}

impl fmt::Display for Rational {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        if self.inner.is_integer() {
            write!(f, "{}", self.inner.numer())
        } else {
            write!(f, "{}/{}", self.inner.numer(), self.inner.denom())
        }
    }
}

impl fmt::Debug for Rational {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Rational({})", self)
    }
}

// Implement standard Arithmetic Ops
impl Add for Rational {
    type Output = Self;
    #[inline]
    fn add(self, rhs: Self) -> Self::Output {
        Self {
            inner: self.inner + rhs.inner,
        }
    }
}

impl<'b> Add<&'b Rational> for &Rational {
    type Output = Rational;
    #[inline]
    fn add(self, rhs: &'b Rational) -> Self::Output {
        Rational {
            inner: &self.inner + &rhs.inner,
        }
    }
}

impl Add<&Rational> for Rational {
    type Output = Rational;
    #[inline]
    fn add(self, rhs: &Rational) -> Self::Output {
        Rational {
            inner: self.inner + &rhs.inner,
        }
    }
}

impl AddAssign for Rational {
    #[inline]
    fn add_assign(&mut self, rhs: Self) {
        self.inner += rhs.inner;
    }
}

impl Sub for Rational {
    type Output = Self;
    #[inline]
    fn sub(self, rhs: Self) -> Self::Output {
        Self {
            inner: self.inner - rhs.inner,
        }
    }
}

impl<'b> Sub<&'b Rational> for &Rational {
    type Output = Rational;
    #[inline]
    fn sub(self, rhs: &'b Rational) -> Self::Output {
        Rational {
            inner: &self.inner - &rhs.inner,
        }
    }
}

impl Sub<&Rational> for Rational {
    type Output = Rational;
    #[inline]
    fn sub(self, rhs: &Rational) -> Self::Output {
        Rational {
            inner: self.inner - &rhs.inner,
        }
    }
}

impl SubAssign for Rational {
    #[inline]
    fn sub_assign(&mut self, rhs: Self) {
        self.inner -= rhs.inner;
    }
}

impl Mul for Rational {
    type Output = Self;
    #[inline]
    fn mul(self, rhs: Self) -> Self::Output {
        Self {
            inner: self.inner * rhs.inner,
        }
    }
}

impl<'b> Mul<&'b Rational> for &Rational {
    type Output = Rational;
    #[inline]
    fn mul(self, rhs: &'b Rational) -> Self::Output {
        Rational {
            inner: &self.inner * &rhs.inner,
        }
    }
}

impl Mul<&Rational> for Rational {
    type Output = Rational;
    #[inline]
    fn mul(self, rhs: &Rational) -> Self::Output {
        Rational {
            inner: self.inner * &rhs.inner,
        }
    }
}

impl MulAssign for Rational {
    #[inline]
    fn mul_assign(&mut self, rhs: Self) {
        self.inner *= rhs.inner;
    }
}

impl Div for Rational {
    type Output = Self;
    #[inline]
    fn div(self, rhs: Self) -> Self::Output {
        if rhs.is_zero() {
            panic!("Axiom violated: Division by zero in field Q");
        }
        Self {
            inner: self.inner / rhs.inner,
        }
    }
}

impl<'b> Div<&'b Rational> for &Rational {
    type Output = Rational;
    #[inline]
    fn div(self, rhs: &'b Rational) -> Self::Output {
        if rhs.is_zero() {
            panic!("Axiom violated: Division by zero in field Q");
        }
        Rational {
            inner: &self.inner / &rhs.inner,
        }
    }
}

impl DivAssign for Rational {
    #[inline]
    fn div_assign(&mut self, rhs: Self) {
        if rhs.is_zero() {
            panic!("Axiom violated: Division by zero in field Q");
        }
        self.inner /= rhs.inner;
    }
}

impl Neg for Rational {
    type Output = Self;
    #[inline]
    fn neg(self) -> Self::Output {
        Self { inner: -self.inner }
    }
}

impl Neg for &Rational {
    type Output = Rational;
    #[inline]
    fn neg(self) -> Self::Output {
        Rational {
            inner: -&self.inner,
        }
    }
}

// Conversions
impl From<i64> for Rational {
    #[inline]
    fn from(val: i64) -> Self {
        Self::from_i64(val)
    }
}

impl From<i32> for Rational {
    #[inline]
    fn from(val: i32) -> Self {
        Self::from_i64(val as i64)
    }
}

impl From<u64> for Rational {
    #[inline]
    fn from(val: u64) -> Self {
        Self {
            inner: Ratio::from_integer(BigInt::from(val)),
        }
    }
}

impl From<u32> for Rational {
    #[inline]
    fn from(val: u32) -> Self {
        Self::from_i64(val as i64)
    }
}

impl From<BigInt> for Rational {
    #[inline]
    fn from(val: BigInt) -> Self {
        Self {
            inner: Ratio::from_integer(val),
        }
    }
}
