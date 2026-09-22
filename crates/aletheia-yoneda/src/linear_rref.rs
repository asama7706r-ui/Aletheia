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
    #[allow(clippy::needless_range_loop)]
    pub fn solve_linear_system(
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
        let dof = Rational::from_i64(nullity as i64);

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
