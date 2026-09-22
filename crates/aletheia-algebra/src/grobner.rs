use crate::error::FormalContradictionError;
use crate::polynomial::{Polynomial, Term};
use std::collections::VecDeque;

/// إعدادات خوارزمية أسس غروبنر وميزانية الحساب لمنع الانفجار التوافقي
#[derive(Copy, Clone, Debug, PartialEq, Eq)]
pub struct GrobnerConfig {
    /// سقف درجة ماكولاي (Macaulay degree ceiling): تجاهل أزواج S-poly التي تتجاوز هذه الدرجة
    pub max_degree: Option<u32>,
    /// ميزانية عدد خطوات الاختزال القصوى
    pub step_budget: Option<usize>,
}

impl Default for GrobnerConfig {
    fn default() -> Self {
        Self {
            max_degree: None,
            step_budget: Some(10_000),
        }
    }
}

/// حساب كثير حدود S (S-Polynomial) لزوج من كثيرات الحدود (f, g)
/// S(f, g) = (LCM / LT(f)) * f - (LCM / LT(g)) * g
pub fn s_polynomial(f: &Polynomial, g: &Polynomial) -> Polynomial {
    if f.is_zero() || g.is_zero() {
        return Polynomial::zero_with_order(f.order());
    }

    let lt_f = f.leading_term().unwrap();
    let lt_g = g.leading_term().unwrap();

    let lcm_mono = lt_f.monomial.lcm(&lt_g.monomial);

    // LCM / LM(f)
    let m_f = lcm_mono.checked_div(&lt_f.monomial).unwrap();
    // 1 / LC(f)
    let c_f = lt_f.coeff.inv().unwrap();
    let term_f = Term::new(c_f, m_f);

    // LCM / LM(g)
    let m_g = lcm_mono.checked_div(&lt_g.monomial).unwrap();
    // 1 / LC(g)
    let c_g = lt_g.coeff.inv().unwrap();
    let term_g = Term::new(c_g, m_g);

    let poly_f = f.mul_term(&term_f);
    let poly_g = g.mul_term(&term_g);

    poly_f.sub_poly(&poly_g)
}

/// خوارزمية بوشبرغر (Buchberger's Algorithm) لحساب أساس غروبنر
/// تدعم معيار بوشبرغر الأول وسقف ماكولاي وميزانية الخطوات
pub fn buchberger(
    generators: &[Polynomial],
    config: &GrobnerConfig,
) -> Result<Vec<Polynomial>, FormalContradictionError> {
    if generators.is_empty() {
        return Ok(Vec::new());
    }

    let order = generators[0].order();
    let mut basis: Vec<Polynomial> = generators
        .iter()
        .filter(|p| !p.is_zero())
        .cloned()
        .collect();

    if basis.is_empty() {
        return Ok(Vec::new());
    }

    // إذا وجد ثابت غير صفري، فالمثالي هو <1>
    for p in &basis {
        if p.is_constant() && !p.is_zero() {
            return Ok(vec![Polynomial::one_with_order(order)]);
        }
    }

    // قائمة الأزواج (i, j)
    let mut pairs: VecDeque<(usize, usize)> = VecDeque::new();
    for i in 0..basis.len() {
        for j in (i + 1)..basis.len() {
            pairs.push_back((i, j));
        }
    }

    let mut steps_used = 0usize;

    while let Some((i, j)) = pairs.pop_front() {
        if let Some(budget) = config.step_budget {
            if steps_used >= budget {
                return Err(FormalContradictionError::StepBudgetExceeded { budget });
            }
        }
        steps_used += 1;

        let f = &basis[i];
        let g = &basis[j];

        let lm_f = f.leading_monomial();
        let lm_g = g.leading_monomial();

        // معيار بوشبرغر الأول: إذا كان GCD(LM(f), LM(g)) = 1، فإن S(f, g) يختزل حتماً إلى الصفر
        if lm_f.gcd(&lm_g).is_one() {
            continue;
        }

        // سقف ماكولاي: إذا تجاوزت درجة الـ LCM السقف، نتجاوز الزوج
        let lcm_deg = lm_f.lcm(&lm_g).total_degree();
        if let Some(max_deg) = config.max_degree {
            if lcm_deg > max_deg {
                continue;
            }
        }

        let s_poly = s_polynomial(f, g);
        let rem = s_poly.reduce_by(&basis);

        if !rem.is_zero() {
            // إذا كان الباقي ثابتاً غير صفري، فإن الأساس يحتوي على 1
            if rem.is_constant() {
                return Ok(vec![Polynomial::one_with_order(order)]);
            }

            let new_idx = basis.len();
            for k in 0..new_idx {
                pairs.push_back((k, new_idx));
            }
            basis.push(rem);
        }
    }

    Ok(basis)
}

/// خوارزمية استخراج أساس غروبنر المختزل الفريد (Reduced Gröbner Basis)
/// 1. إزالة كثيرات الحدود الزائدة التي يقبل مونومها القائد القسمة على مونوم قائد لكثير حدود آخر
/// 2. جعل المعامل القائد لكل عنصر يساوي 1 (Monic)
/// 3. اختزال ذيول كثيرات الحدود بالكامل بالنسبة لباقي عناصر الأساس
pub fn reduced_grobner_basis(
    generators: &[Polynomial],
    config: &GrobnerConfig,
) -> Result<Vec<Polynomial>, FormalContradictionError> {
    let raw_basis = buchberger(generators, config)?;
    if raw_basis.is_empty() {
        return Ok(Vec::new());
    }

    let order = raw_basis[0].order();

    // فحص الثابت 1
    for p in &raw_basis {
        if p.is_constant() && !p.is_zero() {
            return Ok(vec![Polynomial::one_with_order(order)]);
        }
    }

    // الخطوة 1: حذف العناصر الزائدة التي يقبل LM الخاص بها القسمة على LM لعنصر آخر
    let mut minimal: Vec<Polynomial> = Vec::new();
    for (i, p) in raw_basis.iter().enumerate() {
        let lm_p = p.leading_monomial();
        let mut redundant = false;
        for (j, other) in raw_basis.iter().enumerate() {
            if i != j && lm_p.is_divisible_by(&other.leading_monomial()) {
                // في حالة تساوي الـ LM، نحتفظ فقط بالعنصر ذي الفهرس الأصغر
                if lm_p != other.leading_monomial() || j < i {
                    redundant = true;
                    break;
                }
            }
        }
        if !redundant {
            // جعل المعامل القائد = 1 (Monic)
            let lc = p.leading_coeff();
            let monic = p.scale(&lc.inv().unwrap());
            minimal.push(monic);
        }
    }

    // الخطوة 2: اختزال الذيول تماماً (Completely Reduced Tails)
    let mut reduced: Vec<Polynomial> = Vec::with_capacity(minimal.len());

    for i in 0..minimal.len() {
        let p = &minimal[i];
        let lt_p = p.leading_term().unwrap().clone();
        let tail_terms = &p.terms()[1..];
        let tail_poly = Polynomial::from_terms(tail_terms.iter().cloned(), order);

        // مقسومات الاختزال هي كل عناصر الأساس الأخرى
        let other_divisors: Vec<Polynomial> = minimal
            .iter()
            .enumerate()
            .filter(|&(j, _)| j != i)
            .map(|(_, g)| g.clone())
            .collect();

        let reduced_tail = tail_poly.reduce_by(&other_divisors);

        // إعادة تجميع الحد القائد مع الذيل المختزل
        let mut full_terms = vec![lt_p];
        full_terms.extend(reduced_tail.terms().iter().cloned());
        let final_poly = Polynomial::from_terms(full_terms, order);
        reduced.push(final_poly);
    }

    // فرز النتيجة كنسياً
    reduced.sort_unstable_by(|a, b| b.leading_monomial().cmp_with_order(&a.leading_monomial(), order));

    Ok(reduced)
}
