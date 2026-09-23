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

/// خارطة الطريق الاستباقية المشتقة من حل مصفوفة الوقوع M_R * k = Delta S
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct RoadmapPlan {
    /// مؤشرات القواعد النشطة في المسار فقط (k_i > 0)
    pub active_rule_indices: HashSet<usize>,
    /// الميزانية المحددة لكل قاعدة
    pub rule_budgets: Vec<usize>,
    /// التقدير الأدنى لطول مسار البرهان
    pub estimated_steps: usize,
}

impl RoadmapPlan {
    pub fn is_rule_active(&self, rule_idx: usize) -> bool {
        self.active_rule_indices.contains(&rule_idx)
    }
}

/// مرشح التحقق المسبق وخارطة الطريق وفق قانون الانحفاظ ومبرهنة فاركاس (A-Priori Reachability)
#[derive(Clone, Debug)]
pub struct APrioriReachabilityFilter {
    /// متجهات الفروق البنيوية للقواعد النشطة Delta r_i = S(RHS) - S(LHS)
    rule_diffs: Vec<SpectralVector>,
}

impl APrioriReachabilityFilter {
    pub fn new(rule_diffs: Vec<SpectralVector>) -> Self {
        Self { rule_diffs }
    }

    /// استخراج مرشح إمكانية الوصول المسبقة مباشرة من قائمة القواعد الكنسية
    pub fn from_rules(rules: &[crate::rule::RewriteRule]) -> Self {
        let rule_diffs: Vec<SpectralVector> = rules
            .iter()
            .map(|r| {
                let s_lhs = SpectralVector::from_expr(&r.lhs.to_canonical_dummy());
                let s_rhs = SpectralVector::from_expr(&r.rhs.to_canonical_dummy());
                s_rhs.diff(&s_lhs)
            })
            .collect();
        Self::new(rule_diffs)
    }

    /// استخراج خارطة طريق استباقية وميزانية القواعد في زمن O(1)
    pub fn extract_roadmap_plan(
        &self,
        start: &CanonicalExpr,
        target: &CanonicalExpr,
    ) -> Option<RoadmapPlan> {
        // إذا كان التعبيران متطابقين، التحول منجز بخطوة صفرية
        if start == target {
            return Some(RoadmapPlan {
                active_rule_indices: HashSet::new(),
                rule_budgets: vec![0; self.rule_diffs.len()],
                estimated_steps: 0,
            });
        }

        // 1. فحص حظر المتغيرات الجديدة التي لا تولدها أي قاعدة
        let s_start = SpectralVector::from_expr(start);
        let s_target = SpectralVector::from_expr(target);

        let start_vars: HashSet<VariableId> = s_start.var_counts.keys().copied().collect();
        let target_vars: HashSet<VariableId> = s_target.var_counts.keys().copied().collect();

        for v in &target_vars {
            if !start_vars.contains(v) {
                let mut generatable = false;
                for diff in &self.rule_diffs {
                    if diff.var_counts.get(v).copied().unwrap_or(0) > 0 {
                        generatable = true;
                        break;
                    }
                }
                if !generatable {
                    return None; // استبعاد فوري O(1)
                }
            }
        }

        if self.rule_diffs.is_empty() {
            return None;
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

        // 5. حل النظام الخطي M_R * k = Delta S باستخدام RREF الموسعة
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

        // فحص اتساق النظام (0 = b_r حيث b_r != 0)
        for r in 0..num_features {
            let mut all_zeros = true;
            for c in 0..num_rules {
                if !aug_matrix.get(r, c).is_zero() {
                    all_zeros = false;
                    break;
                }
            }
            if all_zeros && !aug_matrix.get(r, num_rules).is_zero() {
                return None; // تناقض: مستحيل يقيناً
            }
        }

        // 6. استخراج الحل الأساسي k_0 وفحص عدم السالبية (مبرهنة فاركاس)
        let mut k_0 = vec![Rational::zero(); num_rules];
        for (row_idx, &p_col) in pivot_cols.iter().enumerate() {
            if p_col < num_rules {
                k_0[p_col] = aug_matrix.get(row_idx, num_rules).clone();
            }
        }

        let pivot_set: HashSet<usize> = pivot_cols.iter().copied().collect();
        let free_cols: Vec<usize> = (0..num_rules).filter(|c| !pivot_set.contains(c)).collect();

        let is_valid = if free_cols.is_empty() {
            k_0.iter().all(|val| !val.is_negative())
        } else {
            let all_non_neg = k_0.iter().all(|v| !v.is_negative());
            if all_non_neg {
                true
            } else {
                let mut possible = true;
                for (row_idx, &p_col) in pivot_cols.iter().enumerate() {
                    if p_col < num_rules && k_0[p_col].is_negative() {
                        let has_compensating_free_col = free_cols.iter().any(|&fc| {
                            !aug_matrix.get(row_idx, fc).is_zero()
                        });
                        if !has_compensating_free_col {
                            possible = false;
                            break;
                        }
                    }
                }
                possible
            }
        };

        if !is_valid {
            return None;
        }

        let mut active_rule_indices = HashSet::new();
        let mut rule_budgets = vec![0; num_rules];
        let mut estimated_steps = 0;

        for (i, val) in k_0.iter().enumerate() {
            if !val.is_zero() && !val.is_negative() {
                active_rule_indices.insert(i);
                let b = val.to_i64().map(|v| v.unsigned_abs() as usize).unwrap_or(1).max(1);
                rule_budgets[i] = b;
                estimated_steps += b;
            }
        }

        // الأعمدة الحرة التي يمكن استخدامها لتعديل الحل
        for &fc in &free_cols {
            active_rule_indices.insert(fc);
            if rule_budgets[fc] == 0 {
                rule_budgets[fc] = 2; // ميزانية استكشافية حرة
                estimated_steps += 2;
            }
        }

        Some(RoadmapPlan {
            active_rule_indices,
            rule_budgets,
            estimated_steps: estimated_steps.max(1),
        })
    }

    /// فحص إمكانية الوصول من E_start إلى E_target في زمن O(1)
    pub fn is_reachable(&self, start: &CanonicalExpr, target: &CanonicalExpr) -> bool {
        self.extract_roadmap_plan(start, target).is_some()
    }
}
