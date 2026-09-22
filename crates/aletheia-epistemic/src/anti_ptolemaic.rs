use crate::error::EpistemicError;
use crate::seal_anchoring::NoetherRegistry;
use aletheia_algebra::Rational;
use aletheia_rewriting::Cost;
use std::cmp::Ordering;

/// تقرير تقييم غربال مناهضة بطليموس (Ptolemaic Evaluation Report)
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PtolemaicEvaluation {
    /// هل تم إطفاء درجات الحرية بالكامل (dof == 0)
    pub dof_zero: bool,
    /// هل يمتثل القانون لتناظرات نويثر المعتمدة
    pub noether_compliant: bool,
    /// هل يتفوق القانون في نصل أوكام (MDL Complexity)
    pub occam_superior: bool,
    /// الحيثيات والتعليل الرياضي
    pub rationale: String,
}

/// غربال مناهضة بطليموس (Anti-Ptolemaic Overfitting Sieve)
/// يحمي النواة من ترقيع النماذج بدوائر التدوير البطليموسية (Epicycles) أو المعاملات الحرة غير المقيدة
pub struct AntiPtolemaicSieve;

impl AntiPtolemaicSieve {
    /// 1. التحقق الصارم من إطفاء درجات الحرية dof == 0
    ///
    /// أي قانون سيادي يجب أن يكون مقيداً بنيوياً بالكامل؛ وجود dof > 0 يُعتبر محاولة ترقيع حر
    pub fn verify_dof_quenched(dof: &Rational) -> Result<(), EpistemicError> {
        if !dof.is_zero() {
            return Err(EpistemicError::PtolemaicOverfitting(format!(
                "رصد درجات حرية حرة موجبة (dof = {}). القوانين السيادية تشترط التقييد التام dof == 0 لمنع الترقيع البطليموسي.",
                dof
            )));
        }
        Ok(())
    }

    /// 2. فحص تناظرات نويثر المحفوظة
    ///
    /// التحقق من أن التناظرات المعلنة لا تخرق سجل نويثر المعتمد في الفيزياء الأساسية
    pub fn verify_noether_invariants(
        declared_invariants: &[String],
        registry: &NoetherRegistry,
    ) -> Result<(), EpistemicError> {
        registry
            .verify_invariants(declared_invariants)
            .map_err(|msg| {
                EpistemicError::PtolemaicOverfitting(format!(
                    "خرق في تناظرات نويثر المصانة: {}",
                    msg
                ))
            })
    }

    /// 3. مقارنة تعقيد نصل أوكام (Occam MDL Complexity)
    ///
    /// يُرجع Ordering::Less إذا كان المرشح أبسط من القائم (تفضيل نصل أوكام الصارم)
    pub fn compare_occam_mdl(existing_cost: &Cost, candidate_cost: &Cost) -> Ordering {
        candidate_cost.cmp(existing_cost)
    }

    /// 4. التقييم الشامل للغربال
    pub fn evaluate_candidate(
        candidate_dof: &Rational,
        candidate_cost: &Cost,
        candidate_invariants: &[String],
        existing_cost_opt: Option<&Cost>,
        registry: &NoetherRegistry,
    ) -> Result<PtolemaicEvaluation, EpistemicError> {
        // فحص تصفير درجات الحرية
        Self::verify_dof_quenched(candidate_dof)?;

        // فحص الامتثال لنويثر
        Self::verify_noether_invariants(candidate_invariants, registry)?;

        // فحص نصل أوكام إن وجد قانون قائم للمقارنة
        let occam_superior = if let Some(existing_cost) = existing_cost_opt {
            candidate_cost < existing_cost
        } else {
            true
        };

        let rationale = if occam_superior {
            "اجتاز القانون المرشح غربال مناهضة بطليموس: درجات حرية صفرية، متوافق مع نويثر، ومتفوق في نصل أوكام.".to_string()
        } else {
            "اجتاز القانون شروط نويثر و dof == 0، ولكنه مساوٍ أو أعلى تعقيداً من النموذج القائم.".to_string()
        };

        Ok(PtolemaicEvaluation {
            dof_zero: true,
            noether_compliant: true,
            occam_superior,
            rationale,
        })
    }
}
