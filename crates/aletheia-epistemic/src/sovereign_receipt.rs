use crate::arbitration::LawStatus;
use crate::receipt::LockReceipt;
use crate::seal_bridge::DomainTag;
use aletheia_algebra::CanonicalExpr;
use aletheia_lattice::DimensionVector;
use aletheia_rewriting::Cost;
use blake3::Hasher;

/// صك السيادة المعرفية المعتمد (SovereignReceipt)
/// الوثيقة الدستورية المشفرة غير القابلة للتزوير التي تمنح القانون مرتبة الحقيقة النافذة في النواة
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct SovereignReceipt {
    /// البصمة التشفيرية المعتمدة للصك (BLAKE3 Merkle Hash)
    pub receipt_id: [u8; 32],
    /// المعرف الفريد للقانون
    pub law_id: String,
    /// البصمة الكنسية للتعبير الرياضي (Canonical AST Hash)
    pub canonical_id: [u8; 32],
    /// التعبير الرياضي الكنسي الصافي
    pub ast: CanonicalExpr,
    /// المجال الأنطولوجي المعتمد للقانون
    pub domain: DomainTag,
    /// التوقيع البعدي المصادق عليه في شبيكة Q^N
    pub dimension: DimensionVector,
    /// تكلفة التعقيد المعرفي وفق نصل أوكام (MDL)
    pub cost: Cost,

    // --- الحقول الدستورية الإلزامية لمسار الاستيعاب (Notion 4.2) ---
    /// رتبة القانون السيادية (ActiveAxiom أو ConditionalLimit)
    pub status: LawStatus,
    /// نطاق الصلاحية المشروط (مثل "v/c << 1" عند خفض رتبة القانون القديم)
    pub validity_regime: Option<String>,
    /// معرف القانون المظلي الجديد الذي استوعبه تقاربياً
    pub parent_law_id: Option<String>,
    // -------------------------------------------------------------

    /// سلسلة التواقيع البرهانية المتسلسلة (Merkle Hash Chain)
    /// [Quarantine Record ID -> Gatekeeper Audit Hash -> Arbitration Verdict Hash -> ...]
    pub proof_chain: Vec<[u8; 32]>,
    /// إيصالات الأقفال الأربعة المستوفاة
    pub lock_receipts: Vec<LockReceipt>,
    /// بصمة شهادة الانكماش التقاربي (إن تمت الترقية عبر الاستيعاب التقاربي)
    pub asymptotic_reduction: Option<[u8; 32]>,
    /// حقبة التتويج السيادي (Sovereignty Epoch)
    pub sovereignty_epoch: u64,
    /// الطابع الزمني لإصدار الصك
    pub issued_at_timestamp: u64,
}

impl SovereignReceipt {
    /// إصدار صك سيادي لبديهية نشطة (Active Axiom)
    #[allow(clippy::too_many_arguments)]
    pub fn issue_active(
        law_id: impl Into<String>,
        canonical_id: [u8; 32],
        ast: CanonicalExpr,
        domain: DomainTag,
        dimension: DimensionVector,
        cost: Cost,
        proof_chain: Vec<[u8; 32]>,
        lock_receipts: Vec<LockReceipt>,
        asymptotic_reduction: Option<[u8; 32]>,
        epoch: u64,
        timestamp: u64,
    ) -> Self {
        Self::issue(
            law_id,
            canonical_id,
            ast,
            domain,
            dimension,
            cost,
            LawStatus::ActiveAxiom,
            None,
            None,
            proof_chain,
            lock_receipts,
            asymptotic_reduction,
            epoch,
            timestamp,
        )
    }

    /// إصدار صك سيادي لقانون مخفّض كحالة حدية تقاربية (Conditional Limit)
    #[allow(clippy::too_many_arguments)]
    pub fn issue_conditional_limit(
        law_id: impl Into<String>,
        canonical_id: [u8; 32],
        ast: CanonicalExpr,
        domain: DomainTag,
        dimension: DimensionVector,
        cost: Cost,
        validity_regime: impl Into<String>,
        parent_law_id: impl Into<String>,
        proof_chain: Vec<[u8; 32]>,
        lock_receipts: Vec<LockReceipt>,
        asymptotic_reduction: Option<[u8; 32]>,
        epoch: u64,
        timestamp: u64,
    ) -> Self {
        Self::issue(
            law_id,
            canonical_id,
            ast,
            domain,
            dimension,
            cost,
            LawStatus::ConditionalLimit,
            Some(validity_regime.into()),
            Some(parent_law_id.into()),
            proof_chain,
            lock_receipts,
            asymptotic_reduction,
            epoch,
            timestamp,
        )
    }

    /// المنشئ العام لصك السيادة مع الحوسبة التشفيرية لبصمة ميركل المعتمدة
    #[allow(clippy::too_many_arguments)]
    pub fn issue(
        law_id: impl Into<String>,
        canonical_id: [u8; 32],
        ast: CanonicalExpr,
        domain: DomainTag,
        dimension: DimensionVector,
        cost: Cost,
        status: LawStatus,
        validity_regime: Option<String>,
        parent_law_id: Option<String>,
        proof_chain: Vec<[u8; 32]>,
        lock_receipts: Vec<LockReceipt>,
        asymptotic_reduction: Option<[u8; 32]>,
        sovereignty_epoch: u64,
        issued_at_timestamp: u64,
    ) -> Self {
        let law_id_str = law_id.into();
        let receipt_id = Self::compute_receipt_id(
            &law_id_str,
            &canonical_id,
            status,
            validity_regime.as_deref(),
            parent_law_id.as_deref(),
            domain,
            &dimension,
            &cost,
            &proof_chain,
            asymptotic_reduction.as_ref(),
            sovereignty_epoch,
            issued_at_timestamp,
        );

        Self {
            receipt_id,
            law_id: law_id_str,
            canonical_id,
            ast,
            domain,
            dimension,
            cost,
            status,
            validity_regime,
            parent_law_id,
            proof_chain,
            lock_receipts,
            asymptotic_reduction,
            sovereignty_epoch,
            issued_at_timestamp,
        }
    }

    /// حوسبة بصمة BLAKE3 المترابطة ميركلياً للصك السيادي
    #[allow(clippy::too_many_arguments)]
    pub fn compute_receipt_id(
        law_id: &str,
        canonical_id: &[u8; 32],
        status: LawStatus,
        validity_regime: Option<&str>,
        parent_law_id: Option<&str>,
        domain: DomainTag,
        dimension: &DimensionVector,
        cost: &Cost,
        proof_chain: &[[u8; 32]],
        asymptotic_reduction: Option<&[u8; 32]>,
        epoch: u64,
        timestamp: u64,
    ) -> [u8; 32] {
        let mut hasher = Hasher::new();
        hasher.update(b"ALETH_SOVEREIGN_RECEIPT_V1");
        hasher.update(law_id.as_bytes());
        hasher.update(canonical_id);
        hasher.update(&[status as u8]);

        if let Some(regime) = validity_regime {
            hasher.update(&[1u8]);
            hasher.update(regime.as_bytes());
        } else {
            hasher.update(&[0u8]);
        }

        if let Some(parent) = parent_law_id {
            hasher.update(&[1u8]);
            hasher.update(parent.as_bytes());
        } else {
            hasher.update(&[0u8]);
        }

        hasher.update(format!("{:?}", domain).as_bytes());

        for i in 0..dimension.len() {
            hasher.update(dimension.get_coord(i).to_string().as_bytes());
        }

        hasher.update(&cost.size.to_le_bytes());
        hasher.update(&cost.degree.to_le_bytes());
        hasher.update(&cost.bit_complexity.to_le_bytes());
        hasher.update(&cost.transcendental.to_le_bytes());

        for proof_hash in proof_chain {
            hasher.update(proof_hash);
        }

        if let Some(asymp) = asymptotic_reduction {
            hasher.update(&[1u8]);
            hasher.update(asymp);
        } else {
            hasher.update(&[0u8]);
        }

        hasher.update(&epoch.to_le_bytes());
        hasher.update(&timestamp.to_le_bytes());

        *hasher.finalize().as_bytes()
    }

    /// إعادة حوسبة معرف الصك السيادي من حقوله الذاتية للتحقق من النزاهة التشفيرية
    pub fn recompute_receipt_id(&self) -> [u8; 32] {
        Self::compute_receipt_id(
            &self.law_id,
            &self.canonical_id,
            self.status,
            self.validity_regime.as_deref(),
            self.parent_law_id.as_deref(),
            self.domain,
            &self.dimension,
            &self.cost,
            &self.proof_chain,
            self.asymptotic_reduction.as_ref(),
            self.sovereignty_epoch,
            self.issued_at_timestamp,
        )
    }

    /// التحقق الدستوري الصارم من سلامة البصمة وعدم التلاعب بأي حقل
    pub fn verify_integrity(&self) -> bool {
        self.receipt_id == self.recompute_receipt_id()
    }

    /// تسلسل الصك السيادي بالكامل إلى بايتات خام Little-Endian
    pub fn to_bytes(&self) -> Result<Vec<u8>, crate::error::EpistemicError> {
        let mut bytes = Vec::new();
        crate::dna_handshake::SovereignDnaPayload::write_receipt(&mut bytes, self)?;
        Ok(bytes)
    }

    /// فك تسلسل الصك السيادي من بايتات خام مع التحقق من البصمة
    pub fn from_bytes(bytes: &[u8]) -> Result<Self, crate::error::EpistemicError> {
        let mut cursor = std::io::Cursor::new(bytes);
        crate::dna_handshake::SovereignDnaPayload::read_receipt(&mut cursor)
    }

    /// حساب البصمة الكنسية BLAKE3 للتعبير الرياضي والأبعاد دون أي اعتماد على اسم القانون النصي
    pub fn compute_canonical_ast_hash(ast: &CanonicalExpr, dim: &DimensionVector) -> [u8; 32] {
        let mut hasher = Hasher::new();
        hasher.update(b"ALETHEIA_CANONICAL_AST_V1");
        hasher.update(format!("{:?}", ast).as_bytes());
        for i in 0..dim.effective_len() {
            hasher.update(dim.get_coord(i).to_string().as_bytes());
        }
        *hasher.finalize().as_bytes()
    }

    /// حساب البصمة الكنسية BLAKE3 لمعادلة غير مكتملة (LHS, RHS, Deficit)
    pub fn compute_canonical_equation_hash(
        lhs: &CanonicalExpr,
        rhs: &CanonicalExpr,
        deficit: &DimensionVector,
    ) -> [u8; 32] {
        let mut hasher = Hasher::new();
        hasher.update(b"ALETHEIA_CANONICAL_EQUATION_V1");
        let (first, second) = if format!("{:?}", lhs) <= format!("{:?}", rhs) {
            (lhs, rhs)
        } else {
            (rhs, lhs)
        };
        hasher.update(format!("{:?}", first).as_bytes());
        hasher.update(b"=");
        hasher.update(format!("{:?}", second).as_bytes());
        for i in 0..deficit.effective_len() {
            hasher.update(deficit.get_coord(i).to_string().as_bytes());
        }
        *hasher.finalize().as_bytes()
    }
}

