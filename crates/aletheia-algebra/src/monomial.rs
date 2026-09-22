use smallvec::SmallVec;
use std::cmp::Ordering;
use std::fmt;

/// معرّف المتغير الرياضي العددي الصرف لمنع تخصيصات الـ Heap أثناء المقارنات والفرز
#[derive(Copy, Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct VariableId(pub u32);

impl fmt::Display for VariableId {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        // تمثيل رمزي قياسي x0, x1, ...
        write!(f, "x{}", self.0)
    }
}

/// ترتيبات المونوميات المقبولة دستورياً (Well-Orderings)
#[derive(Copy, Clone, Debug, PartialEq, Eq, Hash, Default)]
pub enum MonomialOrder {
    #[default]
    DegRevLex, // الأمثل لخوارزميات أسس غروبنر
    Lex,       // الترتيب المعجمي الصارم
    DegLex,    // الترتيب بالدرجة ثم المعجمي
}

/// تمثيل المونوم (Monomial) x1^a1 * x2^a2 * ...
/// يعتمد على SmallVec لتفادي الـ Heap Allocations في 99% من الحدود الجبرية
#[derive(Clone, PartialEq, Eq, Hash)]
pub struct Monomial {
    // مصفوفة أزواج (المتغير، الأس) مرتبة تصاعدياً بدقة حسب VariableId، ولا تحتوي على أس صفر
    factors: SmallVec<[(VariableId, u32); 4]>,
    total_degree: u32,
}

impl Monomial {
    /// المونوم المحايد (1) بدرجة صفرية
    #[inline]
    pub fn one() -> Self {
        Self {
            factors: SmallVec::new(),
            total_degree: 0,
        }
    }

    /// إنشاء مونوم من متغير واحد مرفوع لأس
    pub fn variable(var: VariableId, power: u32) -> Self {
        if power == 0 {
            return Self::one();
        }
        let mut factors = SmallVec::new();
        factors.push((var, power));
        Self {
            factors,
            total_degree: power,
        }
    }

    /// إنشاء مونوم من قائمة أزواج (متغير، أس) غير مفرزة بالضرورة
    pub fn from_factors<I>(iter: I) -> Self
    where
        I: IntoIterator<Item = (VariableId, u32)>,
    {
        let mut raw: SmallVec<[(VariableId, u32); 4]> = iter
            .into_iter()
            .filter(|(_, p)| *p > 0)
            .collect();

        if raw.is_empty() {
            return Self::one();
        }

        raw.sort_unstable_by_key(|&(v, _)| v);

        // دمج المتغيرات المكررة إن وجدت
        let mut dedup: SmallVec<[(VariableId, u32); 4]> = SmallVec::new();
        let mut total_deg = 0u32;

        for (var, pow) in raw {
            if let Some(last) = dedup.last_mut() {
                if last.0 == var {
                    last.1 += pow;
                    total_deg += pow;
                    continue;
                }
            }
            total_deg += pow;
            dedup.push((var, pow));
        }

        Self {
            factors: dedup,
            total_degree: total_deg,
        }
    }

    /// الدرجة الكلية للمونوم (Total Degree)
    #[inline]
    pub fn total_degree(&self) -> u32 {
        self.total_degree
    }

    /// هل المونوم هو العنصر المحايد (1)
    #[inline]
    pub fn is_one(&self) -> bool {
        self.factors.is_empty()
    }

    /// العوامل وأسسها
    #[inline]
    pub fn factors(&self) -> &[(VariableId, u32)] {
        &self.factors
    }

    /// استخراج أس متغير معين في المونوم
    pub fn exponent_of(&self, var: VariableId) -> u32 {
        match self.factors.binary_search_by_key(&var, |&(v, _)| v) {
            Ok(idx) => self.factors[idx].1,
            Err(_) => 0,
        }
    }

    /// ضرب مونوم في مونوم آخر (O(n + m)) مع دمج الأسس
    pub fn mul(&self, other: &Self) -> Self {
        if self.is_one() {
            return other.clone();
        }
        if other.is_one() {
            return self.clone();
        }

        let mut result = SmallVec::with_capacity(self.factors.len() + other.factors.len());
        let mut i = 0;
        let mut j = 0;

        while i < self.factors.len() && j < other.factors.len() {
            let (v1, p1) = self.factors[i];
            let (v2, p2) = other.factors[j];
            match v1.cmp(&v2) {
                Ordering::Less => {
                    result.push((v1, p1));
                    i += 1;
                }
                Ordering::Greater => {
                    result.push((v2, p2));
                    j += 1;
                }
                Ordering::Equal => {
                    result.push((v1, p1 + p2));
                    i += 1;
                    j += 1;
                }
            }
        }

        while i < self.factors.len() {
            result.push(self.factors[i]);
            i += 1;
        }

        while j < other.factors.len() {
            result.push(other.factors[j]);
            j += 1;
        }

        Self {
            factors: result,
            total_degree: self.total_degree + other.total_degree,
        }
    }

    /// القاسم المشترك الأكبر (GCD) بين مونومين
    pub fn gcd(&self, other: &Self) -> Self {
        let mut result = SmallVec::new();
        let mut total_deg = 0u32;

        let mut i = 0;
        let mut j = 0;

        while i < self.factors.len() && j < other.factors.len() {
            let (v1, p1) = self.factors[i];
            let (v2, p2) = other.factors[j];
            match v1.cmp(&v2) {
                Ordering::Less => i += 1,
                Ordering::Greater => j += 1,
                Ordering::Equal => {
                    let min_p = p1.min(p2);
                    if min_p > 0 {
                        result.push((v1, min_p));
                        total_deg += min_p;
                    }
                    i += 1;
                    j += 1;
                }
            }
        }

        Self {
            factors: result,
            total_degree: total_deg,
        }
    }

    /// المضاعف المشترك الأصغر (LCM) بين مونومين
    pub fn lcm(&self, other: &Self) -> Self {
        let mut result = SmallVec::with_capacity(self.factors.len() + other.factors.len());
        let mut total_deg = 0u32;

        let mut i = 0;
        let mut j = 0;

        while i < self.factors.len() && j < other.factors.len() {
            let (v1, p1) = self.factors[i];
            let (v2, p2) = other.factors[j];
            match v1.cmp(&v2) {
                Ordering::Less => {
                    result.push((v1, p1));
                    total_deg += p1;
                    i += 1;
                }
                Ordering::Greater => {
                    result.push((v2, p2));
                    total_deg += p2;
                    j += 1;
                }
                Ordering::Equal => {
                    let max_p = p1.max(p2);
                    result.push((v1, max_p));
                    total_deg += max_p;
                    i += 1;
                    j += 1;
                }
            }
        }

        while i < self.factors.len() {
            let (v1, p1) = self.factors[i];
            result.push((v1, p1));
            total_deg += p1;
            i += 1;
        }

        while j < other.factors.len() {
            let (v2, p2) = other.factors[j];
            result.push((v2, p2));
            total_deg += p2;
            j += 1;
        }

        Self {
            factors: result,
            total_degree: total_deg,
        }
    }

    /// هل self يقبل القسمة على divisor (أي divisor يقسم self)
    pub fn is_divisible_by(&self, divisor: &Self) -> bool {
        if divisor.is_one() {
            return true;
        }
        if divisor.total_degree > self.total_degree {
            return false;
        }

        for &(div_v, div_p) in &divisor.factors {
            if self.exponent_of(div_v) < div_p {
                return false;
            }
        }
        true
    }

    /// قسمة self على divisor مع إرجاع الناتج إن أمكن
    pub fn checked_div(&self, divisor: &Self) -> Option<Self> {
        if !self.is_divisible_by(divisor) {
            return None;
        }

        let mut result = SmallVec::new();
        let mut total_deg = 0u32;

        for &(v, p) in &self.factors {
            let div_p = divisor.exponent_of(v);
            if p > div_p {
                let rem_p = p - div_p;
                result.push((v, rem_p));
                total_deg += rem_p;
            }
        }

        Some(Self {
            factors: result,
            total_degree: total_deg,
        })
    }

    /// مقارنة مونومين وفق ترتيب مونومي محدد
    pub fn cmp_with_order(&self, other: &Self, order: MonomialOrder) -> Ordering {
        match order {
            MonomialOrder::DegRevLex => self.cmp_degrevlex(other),
            MonomialOrder::Lex => self.cmp_lex(other),
            MonomialOrder::DegLex => self.cmp_deglex(other),
        }
    }

    /// الترتيب المعكوس لدرجة المونوم (DegRevLex)
    /// 1. الدرجة الكلية أولاً
    /// 2. عند تساوي الدرجة، في الفرق (a - b) أول متغير يختلف من النهاية (أعلى VariableId):
    ///    المونوم ذو الأس الأصغر يكون هو الأكبر في الترتيب
    fn cmp_degrevlex(&self, other: &Self) -> Ordering {
        let deg_cmp = self.total_degree.cmp(&other.total_degree);
        if deg_cmp != Ordering::Equal {
            return deg_cmp;
        }

        // البحث من أعلى VariableId نزولاً
        let mut i = self.factors.len();
        let mut j = other.factors.len();

        while i > 0 || j > 0 {
            let v1 = if i > 0 { Some(self.factors[i - 1].0) } else { None };
            let v2 = if j > 0 { Some(other.factors[j - 1].0) } else { None };

            match (v1, v2) {
                (Some(var1), Some(var2)) => match var1.cmp(&var2) {
                    Ordering::Equal => {
                        let p1 = self.factors[i - 1].1;
                        let p2 = other.factors[j - 1].1;
                        if p1 != p2 {
                            // في DegRevLex: الأس الأصغر يعني مونوم أكبر!
                            return p2.cmp(&p1);
                        }
                        i -= 1;
                        j -= 1;
                    }
                    Ordering::Greater => {
                        // var1 موجود في self وغير موجود في other (أس other هو 0)
                        // p1 > 0 بينما p2 = 0 -> self له أس أكبر، إذن self أصغر!
                        return Ordering::Less;
                    }
                    Ordering::Less => {
                        // var2 موجود في other وغير موجود في self (أس self هو 0)
                        // p2 > 0 بينما p1 = 0 -> other له أس أكبر، إذن self أكبر!
                        return Ordering::Greater;
                    }
                },
                (Some(_), None) => {
                    return Ordering::Less;
                }
                (None, Some(_)) => {
                    return Ordering::Greater;
                }
                (None, None) => break,
            }
        }

        Ordering::Equal
    }

    /// الترتيب المعجمي الصارم (Lex)
    fn cmp_lex(&self, other: &Self) -> Ordering {
        let mut i = 0;
        let mut j = 0;

        while i < self.factors.len() || j < other.factors.len() {
            let v1 = if i < self.factors.len() { Some(self.factors[i].0) } else { None };
            let v2 = if j < other.factors.len() { Some(other.factors[j].0) } else { None };

            match (v1, v2) {
                (Some(var1), Some(var2)) => match var1.cmp(&var2) {
                    Ordering::Equal => {
                        let p1 = self.factors[i].1;
                        let p2 = other.factors[j].1;
                        if p1 != p2 {
                            return p1.cmp(&p2);
                        }
                        i += 1;
                        j += 1;
                    }
                    Ordering::Less => {
                        // var1 أصغر، إذن يظهر أولاً في الترتيب المعجمي
                        return Ordering::Greater;
                    }
                    Ordering::Greater => {
                        // var2 أصغر، إذن other له الأسبقية
                        return Ordering::Less;
                    }
                },
                (Some(_), None) => return Ordering::Greater,
                (None, Some(_)) => return Ordering::Less,
                (None, None) => break,
            }
        }

        Ordering::Equal
    }

    /// الترتيب بالدرجة ثم المعجمي (DegLex)
    fn cmp_deglex(&self, other: &Self) -> Ordering {
        let deg_cmp = self.total_degree.cmp(&other.total_degree);
        if deg_cmp != Ordering::Equal {
            deg_cmp
        } else {
            self.cmp_lex(other)
        }
    }
}

impl Default for Monomial {
    #[inline]
    fn default() -> Self {
        Self::one()
    }
}

impl PartialOrd for Monomial {
    #[inline]
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for Monomial {
    #[inline]
    fn cmp(&self, other: &Self) -> Ordering {
        // الترتيب الافتراضي الدستوري للنواة هو DegRevLex
        self.cmp_with_order(other, MonomialOrder::DegRevLex)
    }
}

impl fmt::Display for Monomial {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        if self.is_one() {
            return write!(f, "1");
        }
        for (i, &(v, p)) in self.factors.iter().enumerate() {
            if i > 0 {
                write!(f, "*")?;
            }
            if p == 1 {
                write!(f, "{}", v)?;
            } else {
                write!(f, "{}^{}", v, p)?;
            }
        }
        Ok(())
    }
}

impl fmt::Debug for Monomial {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Monomial({})", self)
    }
}
