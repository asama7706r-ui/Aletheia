use aletheia_algebra::Rational;
use aletheia_lattice::DimensionVector;
use smallvec::SmallVec;

/// نتيجة حل نظام المعادلات البعدية الخطية في فضاء الأعداد النسبية Q
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct LinearResolutionResult {
    /// هل النظام الخطي متسق وقابل للحل؟
    pub is_consistent: bool,
    /// رتبة مصفوفة القيود Rank(M)
    pub rank: usize,
    /// درجات الحرية الصافية dof = n - Rank(M) ككسر نسبي في Q
    pub dof: Rational,
    /// حل خاص للنظام إن وجد (Particular Solution)
    pub particular_solution: Option<Vec<Rational>>,
    /// قاعدة فضاء الإلغاء (Nullspace Basis Vectors)
    pub nullspace_basis: Vec<Vec<Rational>>,
    /// متجه العجز البعدي المتبقي في Q^N
    pub deficit_vector: DimensionVector,
}

/// محرك حل العجز البعدي وتجانس الحدود المتعددة عبر RREF الدقيق في Q
pub struct LinearRREFEngine;

impl LinearRREFEngine {
    /// حل تجانس حدود معادلة جمعية متعددة الأطراف (T_1 + T_2 + ... + T_m = 0)
    /// بمقارنة كافة الحدود مع الحد المرجعي T_1 واستخراج فضاء العجز
    pub fn solve_homogeneity(
        terms: &[DimensionVector],
        candidate_bases: &[DimensionVector],
    ) -> LinearResolutionResult {
        if terms.len() <= 1 {
            return LinearResolutionResult {
                is_consistent: true,
                rank: 0,
                dof: Rational::zero(),
                particular_solution: Some(Vec::new()),
                nullspace_basis: Vec::new(),
                deficit_vector: DimensionVector::dimensionless(),
            };
        }

        let ref_dim = &terms[0];

        // فحص التجانس الفردي الصارم: التحقق من أن كل حد يطابق الحد المرجعي فردياً لمنع التلاشي العرضي للفروق المتعاكسة
        if terms.iter().all(|term| term == ref_dim) {
            return LinearResolutionResult {
                is_consistent: true,
                rank: 0,
                dof: Rational::zero(),
                particular_solution: Some(vec![Rational::zero(); candidate_bases.len()]),
                nullspace_basis: Vec::new(),
                deficit_vector: DimensionVector::dimensionless(),
            };
        }

        // استخراج العجز البعدي للحد غير المتطابق بالمقارنة المباشرة مع الحد المرجعي
        let target_deficit = terms
            .iter()
            .find(|term| *term != ref_dim)
            .map(|term| term - ref_dim)
            .unwrap_or_else(DimensionVector::dimensionless);

        Self::solve_linear_system(candidate_bases, &target_deficit)
    }

    /// حل النظام الخطي M_dim * x = delta_d فوق حقل الأعداد النسبية Q
    /// مع تطبيق نصل أوكام (Occam's Razor / MDL) للبحث عن الحد الأدنى من قواعد الأساس المستقلة خطياً
    pub fn solve_linear_system(
        candidate_bases: &[DimensionVector],
        target_deficit: &DimensionVector,
    ) -> LinearResolutionResult {
        let num_cols = candidate_bases.len();

        if target_deficit.is_dimensionless() {
            return LinearResolutionResult {
                is_consistent: true,
                rank: 0,
                dof: Rational::zero(),
                particular_solution: Some(vec![Rational::zero(); num_cols]),
                nullspace_basis: Vec::new(),
                deficit_vector: target_deficit.clone(),
            };
        }

        if num_cols == 0 {
            return LinearResolutionResult {
                is_consistent: false,
                rank: 0,
                dof: Rational::from_i64(target_deficit.effective_len() as i64),
                particular_solution: None,
                nullspace_basis: Vec::new(),
                deficit_vector: target_deficit.clone(),
            };
        }

        // 1. فحص القواعد المفردة k = 1 (أبسط حل ممكن وفق نصل أوكام)
        let mut best_k1 = None;
        for i in 0..num_cols {
            if let Some((sol, score)) = Self::solve_subset_rref(&[i], candidate_bases, target_deficit) {
                if best_k1.as_ref().map_or(true, |(_, best_score)| score < *best_score) {
                    best_k1 = Some((vec![(i, sol[0].clone())], score));
                }
            }
        }
        if let Some((sol_entries, _)) = best_k1 {
            let mut particular = vec![Rational::zero(); num_cols];
            for (idx, val) in sol_entries {
                particular[idx] = val;
            }
            return LinearResolutionResult {
                is_consistent: true,
                rank: 1,
                dof: Rational::zero(),
                particular_solution: Some(particular),
                nullspace_basis: Vec::new(),
                deficit_vector: target_deficit.clone(),
            };
        }

        // 2. فحص أزواج القواعد k = 2 (جسور الاقتران الثنائية مثل hbar/c أو G/c^2)
        let mut best_k2 = None;
        for i in 0..num_cols {
            for j in (i + 1)..num_cols {
                if let Some((sol, score)) = Self::solve_subset_rref(&[i, j], candidate_bases, target_deficit) {
                    if best_k2.as_ref().map_or(true, |(_, best_score)| score < *best_score) {
                        best_k2 = Some((vec![(i, sol[0].clone()), (j, sol[1].clone())], score));
                    }
                }
            }
        }
        if let Some((sol_entries, _)) = best_k2 {
            let mut particular = vec![Rational::zero(); num_cols];
            for (idx, val) in sol_entries {
                particular[idx] = val;
            }
            return LinearResolutionResult {
                is_consistent: true,
                rank: 2,
                dof: Rational::zero(),
                particular_solution: Some(particular),
                nullspace_basis: Vec::new(),
                deficit_vector: target_deficit.clone(),
            };
        }

        // 3. فحص ثلاثيات القواعد k = 3 (الاقترانات الثلاثية المستقلة)
        let mut best_k3 = None;
        for i in 0..num_cols {
            for j in (i + 1)..num_cols {
                for l in (j + 1)..num_cols {
                    if let Some((sol, score)) = Self::solve_subset_rref(&[i, j, l], candidate_bases, target_deficit) {
                        if best_k3.as_ref().map_or(true, |(_, best_score)| score < *best_score) {
                            best_k3 = Some((vec![(i, sol[0].clone()), (j, sol[1].clone()), (l, sol[2].clone())], score));
                        }
                    }
                }
            }
        }
        if let Some((sol_entries, _)) = best_k3 {
            let mut particular = vec![Rational::zero(); num_cols];
            for (idx, val) in sol_entries {
                particular[idx] = val;
            }
            return LinearResolutionResult {
                is_consistent: true,
                rank: 3,
                dof: Rational::zero(),
                particular_solution: Some(particular),
                nullspace_basis: Vec::new(),
                deficit_vector: target_deficit.clone(),
            };
        }

        // 4. إذا لم يوجد أي أساس جزئي مستقل يغلق العجز بـ dof = 0، نحل النظام الكامل
        Self::solve_full_linear_system(candidate_bases, target_deficit)
    }

    /// حل نظام جزئي محدد والتحقق من رتبته واستقلاله التام (Rank == k => dof == 0)
    fn solve_subset_rref(
        indices: &[usize],
        candidate_bases: &[DimensionVector],
        target_deficit: &DimensionVector,
    ) -> Option<(Vec<Rational>, (bool, i64, usize))> {
        let subset_bases: Vec<DimensionVector> = indices.iter().map(|&i| candidate_bases[i].clone()).collect();
        let res = Self::solve_full_linear_system(&subset_bases, target_deficit);

        if res.is_consistent && res.rank == indices.len() {
            if let Some(sol) = res.particular_solution {
                let has_fractional = sol.iter().any(|r| !r.is_integer());
                // الفيزيائية الدستورية الصارمة (Notion Axis 6 & Seal 1):
                // ثوابت الاقتران لسد العجز البعدي في القوانين المادية يجب أن تكون أسساً صحيحة في Z^N
                // الأسس الكسرية تمثل عجزاً غير مغلق بشبكية الثوابت وتتطلب حجراً صحياً أو رتبة طوبولوجية
                if has_fractional {
                    return None;
                }
                let abs_exponent_sum: i64 = sol
                    .iter()
                    .map(|r| r.to_i64().map(|v| v.abs()).unwrap_or(10))
                    .sum();
                let index_sum: usize = indices.iter().sum();
                return Some((sol, (has_fractional, abs_exponent_sum, index_sum)));
            }
        }
        None
    }

    /// حل النظام الخطي الكامل لجميع القواعد دون تقليم عبر الحذف الغاوسي-الأردني الصارم RREF
    #[allow(clippy::needless_range_loop)]
    pub fn solve_full_linear_system(
        candidate_bases: &[DimensionVector],
        target_deficit: &DimensionVector,
    ) -> LinearResolutionResult {
        let max_dim = candidate_bases
            .iter()
            .map(|b| b.effective_len())
            .max()
            .unwrap_or(0)
            .max(target_deficit.effective_len());

        let num_rows = max_dim;
        let num_cols = candidate_bases.len();

        if num_rows == 0 || num_cols == 0 {
            let consistent = target_deficit.is_dimensionless();
            return LinearResolutionResult {
                is_consistent: consistent,
                rank: 0,
                dof: Rational::from_i64(num_cols as i64),
                particular_solution: if consistent { Some(vec![Rational::zero(); num_cols]) } else { None },
                nullspace_basis: Vec::new(),
                deficit_vector: target_deficit.clone(),
            };
        }

        // بناء المصفوفة الموسعة [M | target_deficit] بحجم num_rows x (num_cols + 1)
        let mut matrix: Vec<Vec<Rational>> = Vec::with_capacity(num_rows);
        for r in 0..num_rows {
            let mut row = Vec::with_capacity(num_cols + 1);
            for b in candidate_bases {
                row.push(b.get_coord(r));
            }
            row.push(target_deficit.get_coord(r));
            matrix.push(row);
        }

        // الحذف الغاوسي-الأردني الصارم (RREF) في حقل الأعداد النسبية Q
        let mut pivot_row = 0;
        let mut pivot_cols = SmallVec::<[usize; 8]>::new();

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

        // فحص اتساق النظام
        let mut is_consistent = true;
        for r in rank..num_rows {
            if !matrix[r][num_cols].is_zero() {
                is_consistent = false;
                break;
            }
        }

        if !is_consistent {
            return LinearResolutionResult {
                is_consistent: false,
                rank,
                dof: Rational::zero(),
                particular_solution: None,
                nullspace_basis: Vec::new(),
                deficit_vector: target_deficit.clone(),
            };
        }

        let mut particular = vec![Rational::zero(); num_cols];
        for (idx, &c) in pivot_cols.iter().enumerate() {
            particular[c] = matrix[idx][num_cols].clone();
        }

        let mut nullspace_basis = Vec::new();
        for col in 0..num_cols {
            if !pivot_cols.contains(&col) {
                let mut basis_vec = vec![Rational::zero(); num_cols];
                basis_vec[col] = Rational::one();
                for (p_idx, &p_col) in pivot_cols.iter().enumerate() {
                    basis_vec[p_col] = -&matrix[p_idx][col];
                }
                nullspace_basis.push(basis_vec);
            }
        }

        let nullity = num_cols.saturating_sub(rank);
        let mut dof = Rational::from_i64(nullity as i64);

        // إذا كان الحل الخاص يحتوي على أسس كسرية لثوابت الاقتران، فإنه لا ينتمي للشبكية الصحيحة Z^N
        // وبالتالي لا يعتبر عجزاً مغلقاً (DoF >= 1) ويجب إحالته للحجر الصحي
        if particular.iter().any(|r| !r.is_integer()) && dof.is_zero() {
            dof = Rational::one();
        }

        LinearResolutionResult {
            is_consistent: true,
            rank,
            dof,
            particular_solution: Some(particular),
            nullspace_basis,
            deficit_vector: target_deficit.clone(),
        }
    }
}
