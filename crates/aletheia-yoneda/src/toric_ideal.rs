use aletheia_algebra::Rational;

/// نتيجة فحص وحل المثاليات التوريكية وغير الخطية
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum ToricResolutionResult {
    /// تم الحل بنجاح عبر المسار التوريكي السريع بـ SNF
    Solved {
        exponents: Vec<Rational>,
        dof: Rational,
    },
    /// المسألة تجاوزت سقف ماكولاي الاستباقي: تحال فورياً للحجر الآمن لمنع التجميد (Anti-DoS)
    HighComplexitySafeQuarantine {
        macaulay_degree: usize,
        budget: usize,
    },
    /// مثالي غير متسق
    Inconsistent,
}

/// مصنف المثاليات التوريكية وحارس سقف ماكولاي الاستباقي
pub struct ToricIdealClassifier;

impl ToricIdealClassifier {
    /// حساب سقف ماكولاي الاستباقي لكثيرات الحدود: D_Macaulay = sum(deg(P_i) - 1) + 1
    #[inline]
    pub fn compute_macaulay_bound(degrees: &[usize]) -> usize {
        if degrees.is_empty() {
            return 1;
        }
        let mut sum = 0;
        for &d in degrees {
            sum += d.saturating_sub(1);
        }
        sum + 1
    }

    /// فحص سقف ماكولاي مقابل الميزانية الآمنة لمنع انفجار الذاكرة
    pub fn check_macaulay_budget(degrees: &[usize], budget: usize) -> Result<usize, usize> {
        let bound = Self::compute_macaulay_bound(degrees);
        if bound > budget {
            Err(bound)
        } else {
            Ok(bound)
        }
    }

    /// حل علاقة توريكية ثنائية الحدود (Binomial Power-Law Relation: y = prod x_i^alpha_i)
    /// عبر صيغة سميث المعيارية المختزلة في زمن متعدد الحدود (Polynomial Time)
    #[allow(clippy::needless_range_loop)]
    pub fn solve_power_law_relation(
        target_exponents: &[Rational],
        candidate_matrix: &[Vec<Rational>],
        degrees: &[usize],
        budget: usize,
    ) -> ToricResolutionResult {
        // 1. فحص سقف ماكولاي الاستباقي أولاً لحماية النواة
        if let Err(macaulay_degree) = Self::check_macaulay_budget(degrees, budget) {
            return ToricResolutionResult::HighComplexitySafeQuarantine {
                macaulay_degree,
                budget,
            };
        }

        // 2. حل لوغاريتمي للمعاملات في فضاء الأسس
        if candidate_matrix.is_empty() || target_exponents.is_empty() {
            return ToricResolutionResult::Solved {
                exponents: Vec::new(),
                dof: Rational::zero(),
            };
        }

        let num_rows = target_exponents.len();
        let num_cols = candidate_matrix.len();

        // مصفوفة الأسس الموسعة [M | target]
        let mut matrix: Vec<Vec<Rational>> = Vec::with_capacity(num_rows);
        for r in 0..num_rows {
            let mut row = Vec::with_capacity(num_cols + 1);
            for c in candidate_matrix {
                row.push(c.get(r).cloned().unwrap_or_else(Rational::zero));
            }
            row.push(target_exponents[r].clone());
            matrix.push(row);
        }

        // اختزال غاوسي-سميث في حقل الأعداد النسبية Q
        let mut pivot_row = 0;
        let mut pivot_cols = Vec::new();

        for col in 0..num_cols {
            if pivot_row >= num_rows {
                break;
            }

            let mut selected = None;
            for r in pivot_row..num_rows {
                if !matrix[r][col].is_zero() {
                    selected = Some(r);
                    break;
                }
            }

            if let Some(r) = selected {
                matrix.swap(pivot_row, r);
                let pivot_val = matrix[pivot_row][col].clone();
                for c in col..=num_cols {
                    matrix[pivot_row][c] = &matrix[pivot_row][c] / &pivot_val;
                }

                for r in 0..num_rows {
                    if r != pivot_row && !matrix[r][col].is_zero() {
                        let factor = matrix[r][col].clone();
                        for c in col..=num_cols {
                            let term = &factor * &matrix[pivot_row][c];
                            matrix[r][c] = &matrix[r][c] - &term;
                        }
                    }
                }

                pivot_cols.push(col);
                pivot_row += 1;
            }
        }

        let rank = pivot_row;

        // فحص الاتساق
        for r in rank..num_rows {
            if !matrix[r][num_cols].is_zero() {
                return ToricResolutionResult::Inconsistent;
            }
        }

        let mut exponents = vec![Rational::zero(); num_cols];
        for (idx, &c) in pivot_cols.iter().enumerate() {
            exponents[c] = matrix[idx][num_cols].clone();
        }

        let nullity = num_cols.saturating_sub(rank);
        let dof = Rational::from_i64(nullity as i64);

        ToricResolutionResult::Solved { exponents, dof }
    }
}
