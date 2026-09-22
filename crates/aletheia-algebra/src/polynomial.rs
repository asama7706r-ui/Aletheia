use crate::error::FormalContradictionError;
use crate::monomial::{Monomial, MonomialOrder, VariableId};
use crate::rational::Rational;
use smallvec::SmallVec;
use std::cmp::Ordering;
use std::fmt;
use std::ops::{Add, Mul, Neg, Sub};

/// شجرة التعبيرات الكنسية الجاهزة للتكامل المباشر مع عُقد الـ E-Graph في المحور الرابع
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub enum CanonicalExpr {
    Const(Rational),
    Var(VariableId),
    Add(Vec<CanonicalExpr>),
    Mul(Vec<CanonicalExpr>),
    Div(Box<CanonicalExpr>, Box<CanonicalExpr>),
    Pow(Box<CanonicalExpr>, i32),
    Neg(Box<CanonicalExpr>),
}

/// الحد الجبري المفرد (Term = Coeff * Monomial)
#[derive(Clone, PartialEq, Eq, Hash)]
pub struct Term {
    pub coeff: Rational,
    pub monomial: Monomial,
}

impl Term {
    #[inline]
    pub fn new(coeff: Rational, monomial: Monomial) -> Self {
        Self { coeff, monomial }
    }

    #[inline]
    pub fn is_zero(&self) -> bool {
        self.coeff.is_zero()
    }

    /// ضرب حدين جبريين
    pub fn mul_term(&self, other: &Self) -> Self {
        Self {
            coeff: &self.coeff * &other.coeff,
            monomial: self.monomial.mul(&other.monomial),
        }
    }

    /// ضرب حد في عدد كسري
    pub fn scale(&self, scalar: &Rational) -> Self {
        Self {
            coeff: &self.coeff * scalar,
            monomial: self.monomial.clone(),
        }
    }
}

impl fmt::Display for Term {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        if self.monomial.is_one() {
            write!(f, "{}", self.coeff)
        } else if self.coeff.is_one() {
            write!(f, "{}", self.monomial)
        } else if (&self.coeff + &Rational::one()).is_zero() {
            write!(f, "-{}", self.monomial)
        } else {
            write!(f, "{}*{}", self.coeff, self.monomial)
        }
    }
}

/// كثير حدود متعدد المتغيرات في Q[x_1, ..., x_n]
/// الحدود مخزنة دائماً مفرزة تنازلياً وفق ترتيب المونوميات المختار، وبمعاملات غير صفرية قطيعة
#[derive(Clone, PartialEq, Eq, Hash)]
pub struct Polynomial {
    terms: SmallVec<[Term; 4]>,
    order: MonomialOrder,
}

impl Polynomial {
    /// كثير حدود صفري
    #[inline]
    pub fn zero() -> Self {
        Self::zero_with_order(MonomialOrder::DegRevLex)
    }

    #[inline]
    pub fn zero_with_order(order: MonomialOrder) -> Self {
        Self {
            terms: SmallVec::new(),
            order,
        }
    }

    /// كثير حدود محايد ضربياً (1)
    #[inline]
    pub fn one() -> Self {
        Self::one_with_order(MonomialOrder::DegRevLex)
    }

    #[inline]
    pub fn one_with_order(order: MonomialOrder) -> Self {
        let mut terms = SmallVec::new();
        terms.push(Term::new(Rational::one(), Monomial::one()));
        Self { terms, order }
    }

    /// كثير حدود ثابت من عدد كسري
    pub fn constant(val: Rational) -> Self {
        Self::constant_with_order(val, MonomialOrder::DegRevLex)
    }

    pub fn constant_with_order(val: Rational, order: MonomialOrder) -> Self {
        if val.is_zero() {
            return Self::zero_with_order(order);
        }
        let mut terms = SmallVec::new();
        terms.push(Term::new(val, Monomial::one()));
        Self { terms, order }
    }

    /// متغير مفرد مرفوع للقوة 1
    pub fn var(var: VariableId) -> Self {
        Self::var_with_order(var, MonomialOrder::DegRevLex)
    }

    pub fn var_with_order(var: VariableId, order: MonomialOrder) -> Self {
        let mut terms = SmallVec::new();
        terms.push(Term::new(Rational::one(), Monomial::variable(var, 1)));
        Self { terms, order }
    }

    /// إنشاء كثير حدود من قائمة حدود غير مفرزة بالضرورة مع دمج الحدود المتشابهة وحذف الأصفار
    pub fn from_terms<I>(terms_iter: I, order: MonomialOrder) -> Self
    where
        I: IntoIterator<Item = Term>,
    {
        let mut raw: Vec<Term> = terms_iter
            .into_iter()
            .filter(|t| !t.coeff.is_zero())
            .collect();

        if raw.is_empty() {
            return Self::zero_with_order(order);
        }

        // فرز تنازلي حسب الترتيب المونومي المختار
        raw.sort_unstable_by(|a, b| b.monomial.cmp_with_order(&a.monomial, order));

        let mut canonical_terms: SmallVec<[Term; 4]> = SmallVec::new();

        for term in raw {
            if let Some(last) = canonical_terms.last_mut() {
                if last.monomial == term.monomial {
                    last.coeff += term.coeff;
                    continue;
                }
            }
            canonical_terms.push(term);
        }

        // إزالة أي حدود أصبحت صفرية بعد الجمع
        canonical_terms.retain(|t| !t.coeff.is_zero());

        Self {
            terms: canonical_terms,
            order,
        }
    }

    /// الترتيب المونومي المستخدم
    #[inline]
    pub fn order(&self) -> MonomialOrder {
        self.order
    }

    /// تغيير الترتيب المونومي وإعادة فرز الحدود كنسياً
    pub fn with_order(&self, new_order: MonomialOrder) -> Self {
        if self.order == new_order {
            return self.clone();
        }
        Self::from_terms(self.terms.iter().cloned(), new_order)
    }

    /// هل كثير الحدود صفري
    #[inline]
    pub fn is_zero(&self) -> bool {
        self.terms.is_empty()
    }

    /// هل كثير الحدود يساوي 1
    pub fn is_one(&self) -> bool {
        self.terms.len() == 1
            && self.terms[0].coeff.is_one()
            && self.terms[0].monomial.is_one()
    }

    /// هل كثير الحدود مجرد ثابت
    pub fn is_constant(&self) -> bool {
        self.terms.is_empty() || (self.terms.len() == 1 && self.terms[0].monomial.is_one())
    }

    /// قائمة الحدود مرتبة
    #[inline]
    pub fn terms(&self) -> &[Term] {
        &self.terms
    }

    /// الحد القائد (Leading Term - LT)
    #[inline]
    pub fn leading_term(&self) -> Option<&Term> {
        self.terms.first()
    }

    /// المعامل القائد (Leading Coefficient - LC)
    pub fn leading_coeff(&self) -> Rational {
        self.leading_term()
            .map(|t| t.coeff.clone())
            .unwrap_or_else(Rational::zero)
    }

    /// المونوم القائد (Leading Monomial - LM)
    pub fn leading_monomial(&self) -> Monomial {
        self.leading_term()
            .map(|t| t.monomial.clone())
            .unwrap_or_else(Monomial::one)
    }

    /// أعلى درجة كلية في كثير الحدود
    pub fn total_degree(&self) -> u32 {
        self.terms
            .iter()
            .map(|t| t.monomial.total_degree())
            .max()
            .unwrap_or(0)
    }

    /// ضرب كثير الحدود في عدد كسري (Scalar Multiplication)
    pub fn scale(&self, scalar: &Rational) -> Self {
        if scalar.is_zero() || self.is_zero() {
            return Self::zero_with_order(self.order);
        }
        let scaled_terms = self
            .terms
            .iter()
            .map(|t| t.scale(scalar))
            .filter(|t| !t.coeff.is_zero())
            .collect();
        Self {
            terms: scaled_terms,
            order: self.order,
        }
    }

    /// جمع كثيري حدود (دمج خطي للمصفوفات المفرزة O(N + M))
    pub fn add_poly(&self, other: &Self) -> Self {
        assert_eq!(self.order, other.order, "Cannot add polynomials with different monomial orderings");
        let mut result: SmallVec<[Term; 4]> = SmallVec::with_capacity(self.terms.len() + other.terms.len());
        let mut i = 0;
        let mut j = 0;

        while i < self.terms.len() && j < other.terms.len() {
            let t1 = &self.terms[i];
            let t2 = &other.terms[j];

            match t1.monomial.cmp_with_order(&t2.monomial, self.order) {
                Ordering::Greater => {
                    result.push(t1.clone());
                    i += 1;
                }
                Ordering::Less => {
                    result.push(t2.clone());
                    j += 1;
                }
                Ordering::Equal => {
                    let sum_coeff = &t1.coeff + &t2.coeff;
                    if !sum_coeff.is_zero() {
                        result.push(Term::new(sum_coeff, t1.monomial.clone()));
                    }
                    i += 1;
                    j += 1;
                }
            }
        }

        while i < self.terms.len() {
            result.push(self.terms[i].clone());
            i += 1;
        }

        while j < other.terms.len() {
            result.push(other.terms[j].clone());
            j += 1;
        }

        Self {
            terms: result,
            order: self.order,
        }
    }

    /// طرح كثيري حدود
    pub fn sub_poly(&self, other: &Self) -> Self {
        self.add_poly(&(-other))
    }

    /// ضرب كثيري حدود
    pub fn mul_poly(&self, other: &Self) -> Self {
        assert_eq!(self.order, other.order, "Cannot multiply polynomials with different monomial orderings");
        if self.is_zero() || other.is_zero() {
            return Self::zero_with_order(self.order);
        }

        let mut acc = Self::zero_with_order(self.order);
        for t1 in &self.terms {
            let mut partial_terms = SmallVec::with_capacity(other.terms.len());
            for t2 in &other.terms {
                let prod = t1.mul_term(t2);
                if !prod.is_zero() {
                    partial_terms.push(prod);
                }
            }
            let partial_poly = Self {
                terms: partial_terms,
                order: self.order,
            };
            acc = acc.add_poly(&partial_poly);
        }
        acc
    }

    /// ضرب في حد مفرد
    pub fn mul_term(&self, term: &Term) -> Self {
        if term.is_zero() || self.is_zero() {
            return Self::zero_with_order(self.order);
        }
        let scaled_terms = self
            .terms
            .iter()
            .map(|t| t.mul_term(term))
            .filter(|t| !t.coeff.is_zero())
            .collect();
        Self {
            terms: scaled_terms,
            order: self.order,
        }
    }

    /// خوارزمية القسمة متعددة المتغيرات (Multivariate Division Algorithm)
    /// تُرجع (quots, remainder) بحيث: f = sum(q_i * g_i) + r
    /// مع ضمان أن لا يحتوي r على أي حد يقبل القسمة على أي مونوم قائد من مقسومات G
    pub fn divide_multivariate(&self, divisors: &[Polynomial]) -> (Vec<Polynomial>, Polynomial) {
        let s = divisors.len();
        let mut quotients = vec![Self::zero_with_order(self.order); s];
        let mut remainder_terms: Vec<Term> = Vec::new();
        let mut p = self.clone();

        while !p.is_zero() {
            let mut division_occurred = false;
            let lt_p = p.leading_term().unwrap().clone();

            for (i, divisor) in divisors.iter().enumerate() {
                if divisor.is_zero() {
                    continue;
                }
                let lt_div = divisor.leading_term().unwrap();

                // هل LT(divisor) يقسم LT(p)؟
                if let Some(quot_mono) = lt_p.monomial.checked_div(&lt_div.monomial) {
                    let quot_coeff = lt_p.coeff.checked_div(&lt_div.coeff).unwrap();
                    let quot_term = Term::new(quot_coeff, quot_mono);

                    // إضافة للمقسوم عليه
                    quotients[i] = quotients[i].add_poly(&Self {
                        terms: smallvec::smallvec![quot_term.clone()],
                        order: self.order,
                    });

                    // p = p - quot_term * divisor
                    let sub_poly = divisor.mul_term(&quot_term);
                    p = p.sub_poly(&sub_poly);

                    division_occurred = true;
                    break;
                }
            }

            if !division_occurred {
                // نقل الحد القائد من p إلى الباقي r
                remainder_terms.push(lt_p.clone());
                // إزالة الحد القائد من p
                p.terms.remove(0);
            }
        }

        let remainder = Self::from_terms(remainder_terms, self.order);
        (quotients, remainder)
    }

    /// اختزال كثير حدود بالنسبة لمجموعة من كثيرات الحدود (Normal Form Reduction)
    pub fn reduce_by(&self, divisors: &[Polynomial]) -> Polynomial {
        let (_, remainder) = self.divide_multivariate(divisors);
        remainder
    }

    // =========================================================================
    // التوافق مع الـ E-Graph: تصدير واستيراد الشجرة الكنسية (CanonicalExpr)
    // =========================================================================

    /// تصدير كثير الحدود إلى شجرة تعبيرات كنسية جاهزة للاندماج في الـ E-Graph
    pub fn to_canonical_expr(&self) -> CanonicalExpr {
        if self.is_zero() {
            return CanonicalExpr::Const(Rational::zero());
        }

        let mut add_operands = Vec::new();

        for term in &self.terms {
            let mut mul_operands = Vec::new();

            // المعامل العددي
            if term.monomial.is_one() || !term.coeff.is_one() {
                mul_operands.push(CanonicalExpr::Const(term.coeff.clone()));
            }

            // المتغيرات والأسس
            for &(var, pow) in term.monomial.factors() {
                let var_expr = CanonicalExpr::Var(var);
                if pow == 1 {
                    mul_operands.push(var_expr);
                } else {
                    mul_operands.push(CanonicalExpr::Pow(Box::new(var_expr), pow as i32));
                }
            }

            let term_expr = if mul_operands.is_empty() {
                CanonicalExpr::Const(Rational::one())
            } else if mul_operands.len() == 1 {
                mul_operands.remove(0)
            } else {
                CanonicalExpr::Mul(mul_operands)
            };

            add_operands.push(term_expr);
        }

        if add_operands.is_empty() {
            CanonicalExpr::Const(Rational::zero())
        } else if add_operands.len() == 1 {
            add_operands.remove(0)
        } else {
            CanonicalExpr::Add(add_operands)
        }
    }

    /// بناء كثير حدود من شجرة تعبيرات كنسية (E-Graph AST Importer)
    pub fn from_canonical_expr(
        expr: &CanonicalExpr,
        order: MonomialOrder,
    ) -> Result<Self, FormalContradictionError> {
        match expr {
            CanonicalExpr::Const(c) => Ok(Self::constant_with_order(c.clone(), order)),
            CanonicalExpr::Var(v) => Ok(Self::var_with_order(*v, order)),
            CanonicalExpr::Neg(inner) => {
                let p = Self::from_canonical_expr(inner, order)?;
                Ok(-p)
            }
            CanonicalExpr::Add(operands) => {
                let mut sum = Self::zero_with_order(order);
                for op in operands {
                    let sub_p = Self::from_canonical_expr(op, order)?;
                    sum = sum.add_poly(&sub_p);
                }
                Ok(sum)
            }
            CanonicalExpr::Mul(operands) => {
                let mut prod = Self::one_with_order(order);
                for op in operands {
                    let sub_p = Self::from_canonical_expr(op, order)?;
                    prod = prod.mul_poly(&sub_p);
                }
                Ok(prod)
            }
            CanonicalExpr::Div(num, den) => {
                let num_p = Self::from_canonical_expr(num, order)?;
                let den_p = Self::from_canonical_expr(den, order)?;
                if den_p.is_zero() {
                    return Err(FormalContradictionError::DivisionByZero);
                }
                let (quots, rem) = num_p.divide_multivariate(std::slice::from_ref(&den_p));
                if !rem.is_zero() {
                    return Err(FormalContradictionError::InvalidExpression(
                        "Division in polynomial ring leaves non-zero remainder (rational fraction required)".into()
                    ));
                }
                Ok(quots[0].clone())
            }
            CanonicalExpr::Pow(base, exp) => {
                if *exp < 0 {
                    return Err(FormalContradictionError::InvalidExpression(
                        "Negative power in polynomial ring is not a standard polynomial".into()
                    ));
                }
                let base_p = Self::from_canonical_expr(base, order)?;
                if *exp == 0 {
                    return Ok(Self::one_with_order(order));
                }
                let mut result = Self::one_with_order(order);
                let mut b = base_p;
                let mut e = *exp as u32;
                while e > 0 {
                    if e % 2 == 1 {
                        result = result.mul_poly(&b);
                    }
                    if e > 1 {
                        b = b.clone().mul_poly(&b);
                    }
                    e /= 2;
                }
                Ok(result)
            }
        }
    }
}

impl Neg for Polynomial {
    type Output = Self;
    fn neg(self) -> Self::Output {
        -(&self)
    }
}

impl Neg for &Polynomial {
    type Output = Polynomial;
    fn neg(self) -> Self::Output {
        let neg_terms = self
            .terms
            .iter()
            .map(|t| Term::new(-&t.coeff, t.monomial.clone()))
            .collect();
        Polynomial {
            terms: neg_terms,
            order: self.order,
        }
    }
}

impl Add for Polynomial {
    type Output = Self;
    #[inline]
    fn add(self, rhs: Self) -> Self::Output {
        self.add_poly(&rhs)
    }
}

impl Sub for Polynomial {
    type Output = Self;
    #[inline]
    fn sub(self, rhs: Self) -> Self::Output {
        self.sub_poly(&rhs)
    }
}

impl Mul for Polynomial {
    type Output = Self;
    #[inline]
    fn mul(self, rhs: Self) -> Self::Output {
        self.mul_poly(&rhs)
    }
}

impl fmt::Display for Polynomial {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        if self.is_zero() {
            return write!(f, "0");
        }
        for (i, term) in self.terms.iter().enumerate() {
            if i == 0 {
                write!(f, "{}", term)?;
            } else if term.coeff.is_negative() {
                let abs_term = Term::new(term.coeff.abs(), term.monomial.clone());
                write!(f, " - {}", abs_term)?;
            } else {
                write!(f, " + {}", term)?;
            }
        }
        Ok(())
    }
}

impl fmt::Debug for Polynomial {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Poly({})", self)
    }
}
