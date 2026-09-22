use aletheia_algebra::{Rational, VariableId};
use aletheia_yoneda::CandidateSovereignLawAST;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// المنطق الإبستمولوجي الثلاثي الشبيكي T = <{P, R, U}, sqsubseteq> بالإضافة لحالة النزاع
#[derive(Copy, Clone, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum EpistemicStatus {
    /// مبرهن قطعي (Proven): اجتاز كافة الأقفال الأربعة بإجماع تام واستوفى قيوده dof = 0
    Proven,
    /// مفند برهانياً (Refuted): اصطدم بتناقض صلب 1 = 0 أو تناقض بعدي لا يمكن جبره
    Refuted,
    /// معلق في الفضاء السالب (Uncertain): سليم بنيوياً وبعدياً ولديه درجات حرية موجبة dof > 0
    Uncertain,
    /// قيد المحاكمة والنزاع المعرفي (Disputed): تعارض مع قاعدة مكرسة في شجرة الـ E-Graph
    Disputed,
}

/// نمطا تشغيل بوابات الحقيقة
#[derive(Copy, Clone, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum GatekeeperMode {
    /// النمط التشخيصي (المحور 6): فحص توازي بزمن O(1) دون قطع فوري، لاستخراج متجه العجز الرباعي كاملاً
    DiagnosticScanner,
    /// النمط السيادي (المحور 7): خط أنابيب تعاملي متسلسل صارم يقطع فورياً عند أول تعثر
    SovereignGate,
}

/// العقد الموحد لمدخلات التدقيق الإبستمولوجي (AuditTarget)
/// يستوعب أنظمة القيود الخطية من الحجر والقوانين الكنسية المرشحة للسيادة
#[derive(Clone, Debug, PartialEq)]
pub enum AuditTarget {
    /// نظام قيود خطي متراكم مع حل للمجاهيل من الحجر الصحي
    ConstraintSystem {
        candidate_id: [u8; 32],
        matrix: Vec<Vec<Rational>>,
        rhs: Vec<Rational>,
        solution: HashMap<VariableId, Rational>,
        variables: Vec<VariableId>,
    },
    /// تعبير كنسي مصادق عليه مرشح للسيادة قادم من المرحلة الخامسة
    SovereignCandidate(Box<CandidateSovereignLawAST>),
}

impl AuditTarget {
    /// إنشاء هدف تدقيق لمرشح سيادي
    pub fn sovereign(cand: CandidateSovereignLawAST) -> Self {
        AuditTarget::SovereignCandidate(Box::new(cand))
    }

    /// استرجاع البصمة الفريدة للهدف المدقق
    pub fn candidate_id(&self) -> [u8; 32] {
        match self {
            AuditTarget::ConstraintSystem { candidate_id, .. } => *candidate_id,
            AuditTarget::SovereignCandidate(cand) => cand.canonical_id,
        }
    }
}
