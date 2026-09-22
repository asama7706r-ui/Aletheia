use crate::logic::{EpistemicStatus, GatekeeperMode};
use aletheia_algebra::Rational;
use blake3::Hasher;
use serde::{Deserialize, Serialize};

/// معرفات الأقفال الإبستمولوجية الأربعة
#[derive(Copy, Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum LockType {
    /// القفل 1: غربال البواقي الصفرية (epsilon == 0)
    ResidualSieve = 1,
    /// القفل 2: غربال التجانس البعدي والأنطولوجي في Q^N
    DimensionalLattice = 2,
    /// القفل 3: غربال عزل المجالات ومصادقة الجسور متعدية النقل
    DomainIsolationBridge = 3,
    /// القفل 4: غربال التجذير الأنطولوجي والتجربة الفكرية المانعة للتسميم
    OntologicalAnchor = 4,
}

/// إيصال تدقيق غير قابل للتعديل يوثق نتيجة فحص قفل معين
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct LockReceipt {
    pub lock_id: LockType,
    pub name: String,
    pub passed: bool,
    pub details: String,
    pub violation_metric: Option<Rational>,
}

impl LockReceipt {
    pub fn new(
        lock_id: LockType,
        name: impl Into<String>,
        passed: bool,
        details: impl Into<String>,
        violation_metric: Option<Rational>,
    ) -> Self {
        Self {
            lock_id,
            name: name.into(),
            passed,
            details: details.into(),
            violation_metric,
        }
    }
}

/// السجل الإبستمولوجي الشامل للفرضية بعد عبور البوابات
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct EpistemicAuditRecord {
    pub candidate_id: [u8; 32],
    pub mode: GatekeeperMode,
    pub receipts: Vec<LockReceipt>,
    pub overall_status: EpistemicStatus,
    pub diagnostic_vector: Option<[usize; 4]>,
    pub audit_hash: [u8; 32],
}

impl EpistemicAuditRecord {
    /// إنشاء سجل إبستمولوجي جديد وحساب بصمته التشفيرية المشفرة بـ BLAKE3 تلقائياً
    pub fn new(
        candidate_id: [u8; 32],
        mode: GatekeeperMode,
        receipts: Vec<LockReceipt>,
        overall_status: EpistemicStatus,
        diagnostic_vector: Option<[usize; 4]>,
    ) -> Self {
        let audit_hash = Self::compute_hash(
            &candidate_id,
            mode,
            overall_status,
            &receipts,
            &diagnostic_vector,
        );
        Self {
            candidate_id,
            mode,
            receipts,
            overall_status,
            diagnostic_vector,
            audit_hash,
        }
    }

    /// حساب البصمة التشفيرية الصارمة لبيانات التدقيق
    pub fn compute_hash(
        candidate_id: &[u8; 32],
        mode: GatekeeperMode,
        status: EpistemicStatus,
        receipts: &[LockReceipt],
        diag: &Option<[usize; 4]>,
    ) -> [u8; 32] {
        let mut hasher = Hasher::new();
        hasher.update(b"ALETH_EPISTEMIC_AUDIT_V1");
        hasher.update(candidate_id);
        hasher.update(format!("{:?}", mode).as_bytes());
        hasher.update(format!("{:?}", status).as_bytes());

        for r in receipts {
            hasher.update(&(r.lock_id as u8).to_le_bytes());
            hasher.update(&[r.passed as u8]);
            hasher.update(r.details.as_bytes());
            if let Some(ref metric) = r.violation_metric {
                hasher.update(metric.numer().to_string().as_bytes());
                hasher.update(metric.denom().to_string().as_bytes());
            }
        }

        if let Some(d) = diag {
            for val in d {
                hasher.update(&val.to_le_bytes());
            }
        }

        *hasher.finalize().as_bytes()
    }

    /// هل اجتازت الفرضية كافة الأقفال الأربعة بنجاح قطعي يؤهلها للسيادة؟
    #[inline]
    pub fn is_fully_sovereign(&self) -> bool {
        self.overall_status == EpistemicStatus::Proven
            && self.receipts.len() == 4
            && self.receipts.iter().all(|r| r.passed)
    }
}
