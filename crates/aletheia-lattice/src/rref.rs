use aletheia_algebra::Rational;

/// مصفوفة دقيقة فوق حقل الأعداد النسبية Q
/// تضمن خلو الحذف الغاوسي من أي انزلاق عائم أو أخطاء تقريبية
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct RationalMatrix {
    pub rows: usize,
    pub cols: usize,
    data: Vec<Rational>,
}

impl RationalMatrix {
    /// إنشاء مصفوفة صفرية بحجم rows x cols
    pub fn new(rows: usize, cols: usize) -> Self {
        Self {
            rows,
            cols,
            data: vec![Rational::zero(); rows * cols],
        }
    }

    /// إنشاء مصفوفة من صفوف صريحة
    pub fn from_rows(rows_vec: Vec<Vec<Rational>>) -> Self {
        let rows = rows_vec.len();
        let cols = if rows > 0 { rows_vec[0].len() } else { 0 };
        let mut data = Vec::with_capacity(rows * cols);
        for row in rows_vec {
            assert_eq!(row.len(), cols, "All rows must have the same number of columns");
            data.extend(row);
        }
        Self { rows, cols, data }
    }

    #[inline]
    fn idx(&self, r: usize, c: usize) -> usize {
        debug_assert!(r < self.rows && c < self.cols);
        r * self.cols + c
    }

    #[inline]
    pub fn get(&self, r: usize, c: usize) -> &Rational {
        &self.data[self.idx(r, c)]
    }

    #[inline]
    pub fn set(&mut self, r: usize, c: usize, val: Rational) {
        let idx = self.idx(r, c);
        self.data[idx] = val;
    }

    /// تبديل صفين
    pub fn swap_rows(&mut self, r1: usize, r2: usize) {
        if r1 == r2 {
            return;
        }
        for c in 0..self.cols {
            let idx1 = self.idx(r1, c);
            let idx2 = self.idx(r2, c);
            self.data.swap(idx1, idx2);
        }
    }

    /// خوارزمية الاختزال الصفي المتدرج الدقيق (Exact RREF Algorithm)
    /// تُرجع (رتبة المصفوفة Rank، قائمة أعمدة المحاور Pivot Columns)
    pub fn rref(&mut self) -> (usize, Vec<usize>) {
        let mut lead_col = 0;
        let mut pivot_cols = Vec::new();

        for r in 0..self.rows {
            if lead_col >= self.cols {
                break;
            }

            // البحث عن عنصر ارتكاز غير صفري
            let mut pivot_row = None;
            for i in r..self.rows {
                if !self.get(i, lead_col).is_zero() {
                    pivot_row = Some(i);
                    break;
                }
            }

            let p_row = match pivot_row {
                Some(p) => p,
                None => {
                    // الانتقال للعمود التالي إذا كان العمود الحالي كله أصفاراً
                    lead_col += 1;
                    continue;
                }
            };

            // تبديل صف الارتكاز إلى الصف الحالي r
            self.swap_rows(r, p_row);

            // جعل عنصر الارتكاز = 1 بالضبط بقسمة كامل الصف على قيمة الارتكاز
            let pivot_val = self.get(r, lead_col).clone();
            let inv_pivot = pivot_val.inv().unwrap();
            for c in lead_col..self.cols {
                let scaled = self.get(r, c) * &inv_pivot;
                self.set(r, c, scaled);
            }

            // تصفير كامل عناصر العمود lead_col في جميع الصفوف الأخرى (أعلى وأسفل)
            for i in 0..self.rows {
                if i != r {
                    let factor = self.get(i, lead_col).clone();
                    if !factor.is_zero() {
                        for c in lead_col..self.cols {
                            let sub_val = self.get(r, c) * &factor;
                            let new_val = self.get(i, c) - &sub_val;
                            self.set(i, c, new_val);
                        }
                    }
                }
            }

            pivot_cols.push(lead_col);
            lead_col += 1;
        }

        let rank = pivot_cols.len();
        (rank, pivot_cols)
    }

    /// حساب أساس الفضاء الصفري النسبي الدقيق (Rational Nullspace / Kernel)
    /// لحل المعادلة المتجانسة: M * gamma = 0
    /// يُرجع قائمة متجهات أساسية تشكل جميع حلول الفضاء الصفري
    pub fn nullspace(&self) -> Vec<Vec<Rational>> {
        let mut rref_mat = self.clone();
        let (_rank, pivot_cols) = rref_mat.rref();

        let n = self.cols;
        // المتغيرات الحرة (Free Columns) = كل الأعمدة ما عدا أعمدة الارتكاز
        let free_cols: Vec<usize> = (0..n).filter(|c| !pivot_cols.contains(c)).collect();

        let nullity = free_cols.len();
        let mut basis = Vec::with_capacity(nullity);

        for &free_col in &free_cols {
            let mut sol = vec![Rational::zero(); n];
            // وضع المتغير الحر الحالي = 1
            sol[free_col] = Rational::one();

            // حساب قيم متغيرات الارتكاز المقابلة: x_{p_i} = -R[i, free_col]
            for (i, &p_col) in pivot_cols.iter().enumerate() {
                let coeff = rref_mat.get(i, free_col);
                sol[p_col] = -coeff;
            }

            basis.push(sol);
        }

        basis
    }

    /// التحقق من أن متجه معين ينتمي للفضاء الصفري للمصفوفة الأصلية (M * v == 0)
    pub fn verifies_nullspace_vector(&self, vec: &[Rational]) -> bool {
        assert_eq!(vec.len(), self.cols);
        for r in 0..self.rows {
            let mut dot = Rational::zero();
            for (c, val) in vec.iter().enumerate().take(self.cols) {
                dot += self.get(r, c) * val;
            }
            if !dot.is_zero() {
                return false;
            }
        }
        true
    }
}
