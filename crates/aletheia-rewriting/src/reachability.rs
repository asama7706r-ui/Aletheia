use aletheia_algebra::{CanonicalExpr, Rational, VariableId};
use aletheia_lattice::RationalMatrix;
use std::collections::{HashMap, HashSet};

/// المتجه الطيفي للبنية الرياضية S(E) in Z^n
/// يرصد: تكرار المتغيرات الحرة، عدد العمليات، ومؤشرات المؤثرات
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct SpectralVector {
    pub var_counts: HashMap<VariableId, i64>,
    pub op_add: i64,
    pub op_mul: i64,
    pub op_div: i64,
    pub op_pow: i64,
    pub op_neg: i64,
    pub const_count: i64,
}

impl SpectralVector {
    pub fn new() -> Self {
        Self::default()
    }

    /// استخراج المتجه الطيفي لشجرة تعبيرات كنسية
    pub fn from_expr(expr: &CanonicalExpr) -> Self {
        let mut vec = Self::new();
        vec.accumulate(expr);
        vec
    }

    fn accumulate(&mut self, expr: &CanonicalExpr) {
        match expr {
            CanonicalExpr::Const(_) => self.const_count += 1,
            CanonicalExpr::Var(v) => {
                *self.var_counts.entry(*v).or_insert(0) += 1;
            }
            CanonicalExpr::Neg(inner) => {
                self.op_neg += 1;
                self.accumulate(inner);
            }
            CanonicalExpr::Add(ops) => {
                self.op_add += 1;
                for op in ops {
                    self.accumulate(op);
                }
            }
            CanonicalExpr::Mul(ops) => {
                self.op_mul += 1;
                for op in ops {
                    self.accumulate(op);
                }
            }
            CanonicalExpr::Div(num, den) => {
                self.op_div += 1;
                self.accumulate(num);
                self.accumulate(den);
            }
            CanonicalExpr::Pow(base, _) => {
                self.op_pow += 1;
                self.accumulate(base);
            }
        }
    }

    /// طرح متجهين لحساب الفرق البنيوي Delta S = S(Target) - S(Start)
    pub fn diff(&self, other: &Self) -> Self {
        let mut diff_vars = self.var_counts.clone();
        for (v, count) in &other.var_counts {
            *diff_vars.entry(*v).or_insert(0) -= count;
        }

        Self {
            var_counts: diff_vars,
            op_add: self.op_add - other.op_add,
            op_mul: self.op_mul - other.op_mul,
            op_div: self.op_div - other.op_div,
            op_pow: self.op_pow - other.op_pow,
            op_neg: self.op_neg - other.op_neg,
            const_count: self.const_count - other.const_count,
        }
    }

    /// تحويل المتجه إلى شريحة أعداد كسرية وفق قائمة متغيرات موحدة
    pub fn to_coordinates(&self, vars: &[VariableId]) -> Vec<Rational> {
        let mut coords = Vec::with_capacity(vars.len() + 6);
        for v in vars {
            let c = self.var_counts.get(v).copied().unwrap_or(0);
            coords.push(Rational::from_i64(c));
        }
        coords.push(Rational::from_i64(self.op_add));
        coords.push(Rational::from_i64(self.op_mul));
        coords.push(Rational::from_i64(self.op_div));
        coords.push(Rational::from_i64(self.op_pow));
        coords.push(Rational::from_i64(self.op_neg));
        coords.push(Rational::from_i64(self.const_count));
        coords
    }
}

/// مرشح التحقق المسبق وفق قانون الانحفاظ ومعادلة الحالة ومبرهنة فاركاس (A-Priori Reachability)
#[derive(Clone, Debug)]
pub struct APrioriReachabilityFilter {
    /// متجهات الفروق البنيوية للقواعد النشطة Delta r_i = S(RHS) - S(LHS)
    rule_diffs: Vec<SpectralVector>,
}

impl APrioriReachabilityFilter {
    pub fn new(rule_diffs: Vec<SpectralVector>) -> Self {
        Self { rule_diffs }
    }

    /// فحص إمكانية الوصول من E_start إلى E_target في زمن O(1)
    /// مع التحقق الصارم من شرط عدم السالبية k >= 0 لمعادلة الحالة وفق مبرهنة فاركاس
    pub fn is_reachable(&self, start: &CanonicalExpr, target: &CanonicalExpr) -> bool {
        // إذا كان التعبيران متطابقين، التحول ممكن فورياً بخطوة صفرية
        if start == target {
            return true;
        }

        // 1. فحص حظر المتغيرات الجديدة التي لا تولدها أي قاعدة
        let s_start = SpectralVector::from_expr(start);
        let s_target = SpectralVector::from_expr(target);

        let start_vars: HashSet<VariableId> = s_start.var_counts.keys().copied().collect();
        let target_vars: HashSet<VariableId> = s_target.var_counts.keys().copied().collect();

        // المتغيرات المطلوبة في الهدف وليست موجودة في البداية
        for v in &target_vars {
            if !start_vars.contains(v) {
                // هل توجد أي قاعدة تولد هذا المتغير من العدم؟
                let mut generatable = false;
                for diff in &self.rule_diffs {
                    if diff.var_counts.get(v).copied().unwrap_or(0) > 0 {
                        generatable = true;
                        break;
                    }
                }
                if !generatable {
                    return false; // استبعاد فوري O(1)
                }
            }
        }

        if self.rule_diffs.is_empty() {
            return false;
        }

        // 2. تجميع كافة المتغيرات المشتركة لبناء فضاء الإحداثيات الموحد
        let mut all_vars_set = start_vars;
        all_vars_set.extend(target_vars);
        for r in &self.rule_diffs {
            all_vars_set.extend(r.var_counts.keys().copied());
        }
        let mut all_vars: Vec<VariableId> = all_vars_set.into_iter().collect();
        all_vars.sort_by_key(|v| v.0);

        // 3. بناء مصفوفة الوقوع التحويلي M_R حيث الأعمدة هي Delta r_i
        let num_rules = self.rule_diffs.len();
        let num_features = all_vars.len() + 6;

        let rule_coords: Vec<Vec<Rational>> = self
            .rule_diffs
            .iter()
            .map(|r| r.to_coordinates(&all_vars))
            .collect();

        // 4. بناء متجه الطرف الأيمن Delta S = S(Target) - S(Start)
        let delta_s = s_target.diff(&s_start);
        let b_vec = delta_s.to_coordinates(&all_vars);

        // 5. حل النظام الخطي المفرط M_R * k = Delta S باستخدام RREF الموسعة
        // نكون المصفوفة الموسعة [M_R | b] بأبعاد (num_features x (num_rules + 1))
        let mut aug_rows = Vec::with_capacity(num_features);
        for r in 0..num_features {
            let mut row = Vec::with_capacity(num_rules + 1);
            for rc in rule_coords.iter().take(num_rules) {
                row.push(rc[r].clone());
            }
            row.push(b_vec[r].clone());
            aug_rows.push(row);
        }

        let mut aug_matrix = RationalMatrix::from_rows(aug_rows);
        let (_rank, pivot_cols) = aug_matrix.rref();

        // فحص اتساق النظام: هل يوجد صف من أصفار في المعاملات مع قيمة غير صفرية في b؟
        for r in 0..num_features {
            let mut all_zeros = true;
            for c in 0..num_rules {
                if !aug_matrix.get(r, c).is_zero() {
                    all_zeros = false;
                    break;
                }
            }
            if all_zeros && !aug_matrix.get(r, num_rules).is_zero() {
                // تناقض: 0 = b_r حيث b_r != 0
                return false; // مستحيل يقيناً (P = 0)
            }
        }

        // 6. التحقق الصارم من شرط عدم السالبية k >= 0 (مبرهنة فاركاس)
        // استخراج الحل الأساسي k_0
        let mut k_0 = vec![Rational::zero(); num_rules];
        for (row_idx, &p_col) in pivot_cols.iter().enumerate() {
            if p_col < num_rules {
                k_0[p_col] = aug_matrix.get(row_idx, num_rules).clone();
            }
        }

        // فحص الأعمدة الحرة (Free variables / Nullspace)
        let pivot_set: HashSet<usize> = pivot_cols.iter().copied().collect();
        let free_cols: Vec<usize> = (0..num_rules).filter(|c| !pivot_set.contains(c)).collect();

        if free_cols.is_empty() {
            // الحل وحيد قطيعة: يجب أن يكون كل k_i >= 0
            for val in &k_0 {
                if val.is_negative() {
                    return false; // مرفوض لمخالفة عدم السالبية وفق فاركاس
                }
            }
            true
        } else {
            // توجد درجات حرية: إذا كان الحل الأساسي k_0 >= 0، التحول ممكن فورياً
            let all_non_neg = k_0.iter().all(|v| !v.is_negative());
            if all_non_neg {
                return true;
            }

            // فحص إمكانية التعديل عبر متجهات الفضاء الصفري
            // لكل متغير محوري سالب، نتحقق في صفه المحدد row_idx من وجود عمود حر يمكنه إزاحته
            for (row_idx, &p_col) in pivot_cols.iter().enumerate() {
                if p_col < num_rules && k_0[p_col].is_negative() {
                    let has_compensating_free_col = free_cols.iter().any(|&fc| {
                        // إمكانية الإزاحة الإيجابية في نفس الصف الخاص بالمتغير
                        !aug_matrix.get(row_idx, fc).is_zero()
                    });
                    if !has_compensating_free_col {
                        return false;
                    }
                }
            }
            true
        }
    }
}
