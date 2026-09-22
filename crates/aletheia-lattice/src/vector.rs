use aletheia_algebra::Rational;
use smallvec::SmallVec;
use std::fmt;
use std::hash::{Hash, Hasher};
use std::ops::{Add, AddAssign, Neg, Sub, SubAssign};

/// متجه الأبعاد الكسري في فضاء الشبكيات النسبي Q^N
/// يعتمد على SmallVec لتفادي تخصيصات الـ Heap في الأبعاد السبعة الأساسية (SI-7)
/// ويطبق قاعدة التمدد والإسقاط الصفري الكنسي (Zero-Extension Rule) تلقائياً
#[derive(Clone)]
pub struct DimensionVector {
    coords: SmallVec<[Rational; 8]>,
}

impl DimensionVector {
    /// المتجه الصفري اللابُعدي الكامل [1]
    pub fn dimensionless() -> Self {
        Self {
            coords: SmallVec::new(),
        }
    }

    /// إنشاء متجه أبعاد من مصفوفة إحداثيات كسرية
    pub fn from_coords<I>(iter: I) -> Self
    where
        I: IntoIterator<Item = Rational>,
    {
        Self {
            coords: iter.into_iter().collect(),
        }
    }

    /// إنشاء متجه أبعاد من أعداد صحيحة
    pub fn from_integers(ints: &[i64]) -> Self {
        let coords = ints.iter().map(|&n| Rational::from_i64(n)).collect();
        Self { coords }
    }

    /// إنشاء متجه أساس مفرد (Unit Basis Vector e_k)
    pub fn unit_basis(index: usize, total_len: usize) -> Self {
        let len = total_len.max(index + 1);
        let mut coords = SmallVec::with_capacity(len);
        for i in 0..len {
            if i == index {
                coords.push(Rational::one());
            } else {
                coords.push(Rational::zero());
            }
        }
        Self { coords }
    }

    /// عدد الإحداثيات المخزنة حالياً
    #[inline]
    pub fn len(&self) -> usize {
        self.coords.len()
    }

    /// هل مصفوفة الإحداثيات فارغة
    #[inline]
    pub fn is_empty(&self) -> bool {
        self.coords.is_empty()
    }

    /// قراءة الإحداثي عند الفهرس k مع تطبيق قاعدة التمدد الصفري (Zero-Extension)
    pub fn get_coord(&self, index: usize) -> Rational {
        if index < self.coords.len() {
            self.coords[index].clone()
        } else {
            Rational::zero()
        }
    }

    /// تعيين إحداثي لبعد معين مع توسيع المتجه إذا لزم الأمر
    pub fn set_coord(&mut self, index: usize, val: Rational) {
        if index >= self.coords.len() {
            while self.coords.len() < index {
                self.coords.push(Rational::zero());
            }
            self.coords.push(val);
        } else {
            self.coords[index] = val;
        }
    }

    /// هل المتجه يمثل كمية لا بُعدية تماماً (جميع الإحداثيات أصفار)
    pub fn is_dimensionless(&self) -> bool {
        self.coords.iter().all(|c| c.is_zero())
    }

    /// فهرس آخر إحداثي غير صفري (لحساب الطول الفعّال)
    pub fn effective_len(&self) -> usize {
        let mut last_nonzero = 0;
        for (i, c) in self.coords.iter().enumerate() {
            if !c.is_zero() {
                last_nonzero = i + 1;
            }
        }
        last_nonzero
    }

    /// ضرب قياسي بكسر نسبي (رفع لكمية فيزيائية لأس كسري)
    pub fn scale(&self, scalar: &Rational) -> Self {
        if scalar.is_zero() || self.is_dimensionless() {
            return Self::dimensionless();
        }
        let scaled = self.coords.iter().map(|c| c * scalar).collect();
        Self { coords: scaled }
    }

    /// الإحداثيات الخام
    pub fn coords(&self) -> &[Rational] {
        &self.coords
    }
}

// تطبيق قاعدة المقارنة مع التمدد الصفري الكنسي (Zero-Extension Equality)
impl PartialEq for DimensionVector {
    fn eq(&self, other: &Self) -> bool {
        let max_len = self.coords.len().max(other.coords.len());
        for k in 0..max_len {
            if self.get_coord(k) != other.get_coord(k) {
                return false;
            }
        }
        true
    }
}

impl Eq for DimensionVector {}

// تطبيق Hash متسق تماماً مع التمدد الصفري (يتجاهل الأصفار الزائدة في النهاية)
impl Hash for DimensionVector {
    fn hash<H: Hasher>(&self, state: &mut H) {
        let eff_len = self.effective_len();
        eff_len.hash(state);
        for k in 0..eff_len {
            self.get_coord(k).hash(state);
        }
    }
}

impl Default for DimensionVector {
    #[inline]
    fn default() -> Self {
        Self::dimensionless()
    }
}

// الجمع البُعدي مع التمدد الصفري (ضرب الكميات الفيزيائية: [X * Y] = d_X + d_Y)
impl Add for DimensionVector {
    type Output = Self;
    fn add(self, rhs: Self) -> Self::Output {
        &self + &rhs
    }
}

impl<'b> Add<&'b DimensionVector> for &DimensionVector {
    type Output = DimensionVector;
    fn add(self, rhs: &'b DimensionVector) -> Self::Output {
        let max_len = self.coords.len().max(rhs.coords.len());
        let mut result = SmallVec::with_capacity(max_len);
        for k in 0..max_len {
            result.push(self.get_coord(k) + rhs.get_coord(k));
        }
        DimensionVector { coords: result }
    }
}

impl AddAssign for DimensionVector {
    fn add_assign(&mut self, rhs: Self) {
        let max_len = self.coords.len().max(rhs.coords.len());
        for k in 0..max_len {
            let sum = self.get_coord(k) + rhs.get_coord(k);
            if k < self.coords.len() {
                self.coords[k] = sum;
            } else {
                self.coords.push(sum);
            }
        }
    }
}

// الطرح البُعدي مع التمدد الصفري (قسمة الكميات الفيزيائية: [X / Y] = d_X - d_Y)
impl Sub for DimensionVector {
    type Output = Self;
    fn sub(self, rhs: Self) -> Self::Output {
        &self - &rhs
    }
}

impl<'b> Sub<&'b DimensionVector> for &DimensionVector {
    type Output = DimensionVector;
    fn sub(self, rhs: &'b DimensionVector) -> Self::Output {
        let max_len = self.coords.len().max(rhs.coords.len());
        let mut result = SmallVec::with_capacity(max_len);
        for k in 0..max_len {
            result.push(self.get_coord(k) - rhs.get_coord(k));
        }
        DimensionVector { coords: result }
    }
}

impl SubAssign for DimensionVector {
    fn sub_assign(&mut self, rhs: Self) {
        let max_len = self.coords.len().max(rhs.coords.len());
        for k in 0..max_len {
            let diff = self.get_coord(k) - rhs.get_coord(k);
            if k < self.coords.len() {
                self.coords[k] = diff;
            } else {
                self.coords.push(diff);
            }
        }
    }
}

impl Neg for DimensionVector {
    type Output = Self;
    fn neg(self) -> Self::Output {
        -(&self)
    }
}

impl Neg for &DimensionVector {
    type Output = DimensionVector;
    fn neg(self) -> Self::Output {
        let neg_coords = self.coords.iter().map(|c| -c).collect();
        DimensionVector { coords: neg_coords }
    }
}

impl fmt::Display for DimensionVector {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        if self.is_dimensionless() {
            return write!(f, "[1]");
        }

        let base_symbols = ["L", "M", "T", "I", "Θ", "N", "J"];
        let mut printed_any = false;

        for (i, coord) in self.coords.iter().enumerate() {
            if coord.is_zero() {
                continue;
            }
            if printed_any {
                write!(f, " * ")?;
            }
            let name = if i < base_symbols.len() {
                base_symbols[i].to_string()
            } else {
                format!("D{}", i)
            };

            if coord.is_one() {
                write!(f, "[{}]", name)?;
            } else {
                write!(f, "[{}]^({})", name, coord)?;
            }
            printed_any = true;
        }

        if !printed_any {
            write!(f, "[1]")
        } else {
            Ok(())
        }
    }
}

impl fmt::Debug for DimensionVector {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "DimVec({})", self)
    }
}
