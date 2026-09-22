use crate::error::EpistemicError;
use crate::seal_bridge::DomainTag;
use aletheia_algebra::{CanonicalExpr, Rational};
use aletheia_lattice::DimensionVector;
use aletheia_rewriting::Cost;
use aletheia_yoneda::AsymptoticLimitCertificate;
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet, VecDeque};

/// الحالة المعرفية والسيادية للقانون الفيزيائي / الرياضي
#[derive(Copy, Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum LawStatus {
    /// قانون سيادي نافذ ومسلم به كبديهية نشطة (Active Axiom)
    ActiveAxiom,
    /// قانون مخفض لحالة حدية تقاربية صالحة فقط ضمن نطاق محدد (Conditional Limit)
    ConditionalLimit,
    /// قانون مخلوع تم إسقاطه ونقضه بنصل أوكام أو التجربة (Overthrown)
    Overthrown,
    /// قانون معلق إبستمولوجياً في الحجر الصحي بحصانة الإبوخيه (Quarantined Epoché)
    QuarantinedEpoche,
    /// قانون محدد بنطاق أنطولوجي معزول بجدار ترسيم الحدود (Demarcated Boundary)
    DemarcatedBoundary,
}

/// توصيف القانون المتنازع في المحكم الإبستمولوجي (LawDescriptor)
#[derive(Clone, Debug, PartialEq)]
pub struct LawDescriptor {
    pub law_id: String,
    pub name: String,
    pub ast: CanonicalExpr,
    pub domain: DomainTag,
    pub dimension: DimensionVector,
    pub dof: Rational,
    pub cost: Cost,
    pub invariants: HashSet<String>,
    pub child_dependencies: HashSet<String>,
}

impl LawDescriptor {
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        law_id: impl Into<String>,
        name: impl Into<String>,
        ast: CanonicalExpr,
        domain: DomainTag,
        dimension: DimensionVector,
        dof: Rational,
        cost: Cost,
        invariants: HashSet<String>,
    ) -> Self {
        Self {
            law_id: law_id.into(),
            name: name.into(),
            ast,
            domain,
            dimension,
            dof,
            cost,
            invariants,
            child_dependencies: HashSet::new(),
        }
    }

    pub fn with_child_dependency(mut self, dep: impl Into<String>) -> Self {
        self.child_dependencies.insert(dep.into());
        self
    }
}

/// المسارات الإبستمولوجية الخمسة لحسم النزاعات والثورات العلمية
#[derive(Copy, Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum ArbitrationPath {
    /// المسار 1: الاستيعاب التقاربي (نموذج آينشتاين / نيوتن)
    Subsumption,
    /// المسار 2: مصالحة العجز الخفي (نموذج باولي / فيرمي - نيوترينو)
    NeutrinoDeficit,
    /// المسار 3: ترسيم الحدود المعرفية (نموذج الكوانتم / الكلاسيك)
    DomainDemarcation,
    /// المسار 4: الانقلاب الجذري والتراجع المتتالي (نموذج لافوازييه / فلوجستون)
    Overthrow,
    /// المسار 5: التعليق الإبستمولوجي المحايد وحصانة الإبوخيه (Epoché)
    DualSuspension,
}

/// حكم وقرار المحكم الإبستمولوجي (ArbitrationVerdict)
#[derive(Clone, Debug, PartialEq)]
pub struct ArbitrationVerdict {
    pub path: ArbitrationPath,
    pub victorious_law: Option<LawDescriptor>,
    pub demoted_law: Option<LawDescriptor>,
    pub new_status_victorious: Option<LawStatus>,
    pub new_status_demoted: Option<LawStatus>,
    pub retracted_dependencies: Vec<String>,
    pub reconciled_variable: Option<String>,
    pub rationale: String,
}

/// المحكم الإبستمولوجي للثورات العلمية وإدارة مخطط الاعتماديات المعرفية
#[derive(Clone, Debug, Default)]
pub struct EpistemicArbitrator {
    /// مخطط الاعتماديات المعرفية G_dep: الأصل -> مجموعة النظريات المشتقة منه
    dependency_graph: HashMap<String, HashSet<String>>,
    /// الحالات المعرفية الحالية للقوانين المسجلة
    law_statuses: HashMap<String, LawStatus>,
}

impl EpistemicArbitrator {
    pub fn new() -> Self {
        Self {
            dependency_graph: HashMap::new(),
            law_statuses: HashMap::new(),
        }
    }

    /// تسجيل حالة قانون في المحكم
    pub fn register_law(&mut self, law_id: impl Into<String>, status: LawStatus) {
        self.law_statuses.insert(law_id.into(), status);
    }

    /// جلب الحالة المعرفية الحالية لقانون معين
    pub fn get_status(&self, law_id: &str) -> Option<LawStatus> {
        self.law_statuses.get(law_id).copied()
    }

    /// تسجيل علاقة اشتقاق/اعتمادية في المخطط (parent_law -> child_law)
    pub fn register_dependency(
        &mut self,
        parent_law_id: impl Into<String>,
        child_law_id: impl Into<String>,
    ) {
        let parent = parent_law_id.into();
        let child = child_law_id.into();
        self.dependency_graph
            .entry(parent)
            .or_default()
            .insert(child);
    }

    /// استخراج كافة النظريات والنتائج المشتقة متعدياً (Transitive Dependents) عبر BFS
    pub fn get_transitive_dependents(&self, root_id: &str) -> Vec<String> {
        let mut visited = HashSet::new();
        let mut queue = VecDeque::new();
        let mut result = Vec::new();

        if let Some(children) = self.dependency_graph.get(root_id) {
            for child in children {
                if visited.insert(child.clone()) {
                    queue.push_back(child.clone());
                }
            }
        }

        while let Some(curr) = queue.pop_front() {
            result.push(curr.clone());
            if let Some(children) = self.dependency_graph.get(&curr) {
                for child in children {
                    if visited.insert(child.clone()) {
                        queue.push_back(child.clone());
                    }
                }
            }
        }

        result
    }

    /// تحكيم النزاع العلمي بين قانون قائم وقانون مرشح وتحديد مسار الثورة العلمية
    pub fn adjudicate(
        &mut self,
        existing: &LawDescriptor,
        candidate: &LawDescriptor,
        asymptotic_cert: Option<&AsymptoticLimitCertificate>,
    ) -> Result<ArbitrationVerdict, EpistemicError> {
        // -------------------------------------------------------------
        // المسار 1: الاستيعاب التقاربي (Subsumption) - نموذج أينشتاين / نيوتن
        // -------------------------------------------------------------
        // إذا كان المرشح يحمل شهادة انكماش جبر لي ناعمة ومثبتة برهانياً (مثل v/c -> 0)
        if let Some(cert) = asymptotic_cert {
            if cert.is_smooth_reduction && cert.jacobi_verified {
                self.law_statuses
                    .insert(candidate.law_id.clone(), LawStatus::ActiveAxiom);
                self.law_statuses
                    .insert(existing.law_id.clone(), LawStatus::ConditionalLimit);

                return Ok(ArbitrationVerdict {
                    path: ArbitrationPath::Subsumption,
                    victorious_law: Some(candidate.clone()),
                    demoted_law: Some(existing.clone()),
                    new_status_victorious: Some(LawStatus::ActiveAxiom),
                    new_status_demoted: Some(LawStatus::ConditionalLimit),
                    retracted_dependencies: Vec::new(),
                    reconciled_variable: None,
                    rationale: format!(
                        "استيعاب تقاربي مؤكد عبر انكماش زمر لي عند المعامل '{}'. يُخفض القانون القديم إلى CONDITIONAL_LIMIT ويُتوج الجديد كـ ACTIVE_AXIOM.",
                        cert.parameter_name
                    ),
                });
            }
        }

        // -------------------------------------------------------------
        // المسار 2: مصالحة العجز الخفي (Neutrino Deficit) - نموذج باولي / فيرمي
        // -------------------------------------------------------------
        // إذا كان القانونان في نفس المجال ولديهما درجات حرية غير مصفّرة (dof > 0) أو عجز في معادلة حفظ
        if existing.domain == candidate.domain
            && (!existing.dof.is_zero() || !candidate.dof.is_zero())
        {
            let hidden_var = format!("psi_hidden_{}_{}", existing.law_id, candidate.law_id);

            return Ok(ArbitrationVerdict {
                path: ArbitrationPath::NeutrinoDeficit,
                victorious_law: None,
                demoted_law: None,
                new_status_victorious: None,
                new_status_demoted: None,
                retracted_dependencies: Vec::new(),
                reconciled_variable: Some(hidden_var.clone()),
                rationale: format!(
                    "رصد عجز خفي في المجال الأنطولوجي ذاته ({:?}). يُحال النزاع لمحرك دمج النيوترينو مع المتغير الكامن '{}' لإطفاء درجات الحرية المشتركة.",
                    existing.domain, hidden_var
                ),
            });
        }

        // -------------------------------------------------------------
        // المسار 3: ترسيم الحدود المعرفية (Domain Demarcation) - نموذج الكوانتم / الكلاسيك
        // -------------------------------------------------------------
        // إذا كان القانونان ينتميان لمجالين معرفيين مستقلين ولا يوجد انكماش تقاربي بينهما
        if existing.domain != candidate.domain {
            self.law_statuses
                .insert(candidate.law_id.clone(), LawStatus::DemarcatedBoundary);
            self.law_statuses
                .insert(existing.law_id.clone(), LawStatus::DemarcatedBoundary);

            return Ok(ArbitrationVerdict {
                path: ArbitrationPath::DomainDemarcation,
                victorious_law: Some(candidate.clone()),
                demoted_law: Some(existing.clone()),
                new_status_victorious: Some(LawStatus::DemarcatedBoundary),
                new_status_demoted: Some(LawStatus::DemarcatedBoundary),
                retracted_dependencies: Vec::new(),
                reconciled_variable: None,
                rationale: format!(
                    "اختلاف في المجالات الأنطولوجية ({:?} مقابل {:?}). يتم بناء جدار عزل وسومي لمنع التداخل والتصادم الفئوي.",
                    existing.domain, candidate.domain
                ),
            });
        }

        // -------------------------------------------------------------
        // المسار 4: الانقلاب الجذري والتراجع المتتالي (Overthrow) - نموذج لافوازييه / فلوجستون
        // -------------------------------------------------------------
        // إذا كان المرشح محققاً dof == 0 ويتفوق قطيعة على القائم بنصل أوكام (MDL_cand < MDL_exist)
        if candidate.dof.is_zero() && candidate.cost < existing.cost {
            let retracted = self.get_transitive_dependents(&existing.law_id);

            self.law_statuses
                .insert(candidate.law_id.clone(), LawStatus::ActiveAxiom);
            self.law_statuses
                .insert(existing.law_id.clone(), LawStatus::Overthrown);

            // إسقاط كافة النظريات المشتقة من القانون المخلوع
            for dep in &retracted {
                self.law_statuses.insert(dep.clone(), LawStatus::Overthrown);
            }

            return Ok(ArbitrationVerdict {
                path: ArbitrationPath::Overthrow,
                victorious_law: Some(candidate.clone()),
                demoted_law: Some(existing.clone()),
                new_status_victorious: Some(LawStatus::ActiveAxiom),
                new_status_demoted: Some(LawStatus::Overthrown),
                retracted_dependencies: retracted.clone(),
                reconciled_variable: None,
                rationale: format!(
                    "انقلاب معرفي جذري: المرشح '{}' يتفوق على '{}' في نصل أوكام (MDL: {} مقابل {}). تم سحب سيادة القديم وإسقاط {} نظرية مشتقة متعدية.",
                    candidate.law_id, existing.law_id, candidate.cost, existing.cost, retracted.len()
                ),
            });
        }

        // -------------------------------------------------------------
        // المسار 5: التعليق الإبستمولوجي المحايد وحصانة الإبوخيه (Dual Suspension / Epoché)
        // -------------------------------------------------------------
        // تكافؤ الأدلة والتعقيد: عزل الطرفين في الحجر لمنع الاغتيال التعسفي
        self.law_statuses
            .insert(candidate.law_id.clone(), LawStatus::QuarantinedEpoche);
        self.law_statuses
            .insert(existing.law_id.clone(), LawStatus::QuarantinedEpoche);

        Ok(ArbitrationVerdict {
            path: ArbitrationPath::DualSuspension,
            victorious_law: None,
            demoted_law: None,
            new_status_victorious: Some(LawStatus::QuarantinedEpoche),
            new_status_demoted: Some(LawStatus::QuarantinedEpoche),
            retracted_dependencies: Vec::new(),
            reconciled_variable: None,
            rationale: "تكافؤ الأدلة والتعقيد أو عدم تفوق المرشح بأوكام. تفعيل التعليق الإبستمولوجي (Epoché) وحجز الطرفين في الحجر لحين ورود برهان حاسم.".to_string(),
        })
    }
}
