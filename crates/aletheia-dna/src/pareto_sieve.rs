use aletheia_algebra::{CanonicalExpr, Rational};
use aletheia_rewriting::Cost;
use std::cmp::Ordering;

/// مرشح قانون فيزيائي/معرفي لغربال باريتو
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ParetoLawCandidate {
    pub candidate_id: String,
    pub ast: CanonicalExpr,
    pub mdl_cost: Cost,
    pub residual_score: Rational,
    pub domain_id: u16,
    pub epoch: u64,
}

impl ParetoLawCandidate {
    pub fn new(
        candidate_id: impl Into<String>,
        ast: CanonicalExpr,
        mdl_cost: Cost,
        residual_score: Rational,
        domain_id: u16,
        epoch: u64,
    ) -> Self {
        Self {
            candidate_id: candidate_id.into(),
            ast,
            mdl_cost,
            residual_score,
            domain_id,
            epoch,
        }
    }

    /// تحويل كلفة التعقيد الوصفي الأدنى (MDL) إلى كمية قياسية في فضاء الأعداد الكسرية Q
    /// الحجم + 2 * الدرجة + التعقيد البتي + 4 * الحدود المتسامية
    pub fn scalar_mdl(&self) -> Rational {
        let val = self.mdl_cost.size as i64
            + 2 * self.mdl_cost.degree as i64
            + self.mdl_cost.bit_complexity as i64
            + 4 * self.mdl_cost.transcendental as i64;
        Rational::from_i64(val)
    }

    /// كلفة أوكام ثنائية الهدف الموزونة في فضاء Q الصرف:
    /// J = alpha * MDL + beta * Residual
    pub fn occam_cost(&self, alpha: Rational, beta: Rational) -> Rational {
        alpha * self.scalar_mdl() + beta * self.residual_score.clone()
    }
}

/// علاقة الهيمنة الصارمة لباريتو (Strict Pareto Dominance in Q^2)
/// المرشح A يهيمن على B (A <_P B) إذا وفقط إذا:
/// (MDL(A) <= MDL(B) and Res(A) <= Res(B)) and (MDL(A) < MDL(B) or Res(A) < Res(B))
pub fn pareto_dominates(a: &ParetoLawCandidate, b: &ParetoLawCandidate) -> bool {
    let mdl_a = a.scalar_mdl();
    let mdl_b = b.scalar_mdl();
    let res_a = &a.residual_score;
    let res_b = &b.residual_score;

    let no_worse = mdl_a <= mdl_b && res_a <= res_b;
    let strictly_better = mdl_a < mdl_b || res_a < res_b;

    no_worse && strictly_better
}

/// غربال باريتو ثنائي الهدف لاستخراج جبهة القوانين غير المهيمنة (Skyline Operator)
pub struct ParetoSieve;

impl ParetoSieve {
    /// تصفية المرشحين واستخراج جبهة باريتو (Skyline Frontier)
    /// يستبعد أي مرشح يهيمن عليه مرشح آخر بشكل صارم
    pub fn extract_frontier(candidates: &[ParetoLawCandidate]) -> Vec<ParetoLawCandidate> {
        let mut frontier = Vec::new();

        for (i, cand_a) in candidates.iter().enumerate() {
            let mut is_dominated = false;
            for (j, cand_b) in candidates.iter().enumerate() {
                if i != j && pareto_dominates(cand_b, cand_a) {
                    is_dominated = true;
                    break;
                }
            }
            if !is_dominated {
                frontier.push(cand_a.clone());
            }
        }

        frontier
    }

    /// استخراج جبهة باريتو وترتيبها تصاعدياً وفق كلفة أوكام J = alpha * MDL + beta * Residual
    pub fn rank_frontier(
        candidates: &[ParetoLawCandidate],
        alpha: Rational,
        beta: Rational,
    ) -> Vec<(ParetoLawCandidate, Rational)> {
        let frontier = Self::extract_frontier(candidates);
        let mut scored: Vec<(ParetoLawCandidate, Rational)> = frontier
            .into_iter()
            .map(|cand| {
                let j_cost = cand.occam_cost(alpha.clone(), beta.clone());
                (cand, j_cost)
            })
            .collect();

        scored.sort_by(|(_, cost_a), (_, cost_b)| {
            cost_a.partial_cmp(cost_b).unwrap_or(Ordering::Equal)
        });

        scored
    }
}
