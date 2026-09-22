use crate::arbitration::LawStatus;
use crate::error::EpistemicError;
use crate::receipt::{LockReceipt, LockType};
use crate::seal_bridge::DomainTag;
use crate::sovereign_receipt::SovereignReceipt;
use aletheia_algebra::{CanonicalExpr, Rational, VariableId};
use aletheia_lattice::DimensionVector;
use aletheia_rewriting::Cost;
use blake3::Hasher;
use std::io::{Read, Write};

/// الترويسة السحرية القياسية المعيارية لكبسولة الجينوم المعرفي (8 بايت خام)
pub const MAGIC_HEADER: &[u8; 8] = b"ALETH_D1";

/// كبسولة الجينوم المعرفي السيادية (SovereignDnaPayload)
/// الوعاء المعياري عالي السرعة لنقل الحصيلة المعرفية السيادية إلى المحور الثامن (kernel.dna)
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct SovereignDnaPayload {
    /// إصدار البروتوكول الثنائي
    pub version: u32,
    /// الحقبة الزمنية للجينوم
    pub epoch: u64,
    /// البصمة التشفيرية التراكمية للجينوم بالكامل (BLAKE3 Merkle Root)
    pub genome_merkle_root: [u8; 32],
    /// قائمة الصكوك السيادية النشطة والمخفضة
    pub sovereign_receipts: Vec<SovereignReceipt>,
}

impl SovereignDnaPayload {
    /// تجميع وتعبئة كبسولة الجينوم المعرفي من قائمة صكوك سيادية
    pub fn package(receipts: Vec<SovereignReceipt>, epoch: u64) -> Result<Self, EpistemicError> {
        // التحقق الدستوري: منع تسرب أي صك يحمل حالة مخلوعة أو غير صالحة
        for r in &receipts {
            if r.status != LawStatus::ActiveAxiom
                && r.status != LawStatus::ConditionalLimit
                && r.status != LawStatus::DemarcatedBoundary
            {
                return Err(EpistemicError::FormalContradiction(format!(
                    "محاولة تسريب صك غير سيادي إلى الجينوم المعرفي: '{}' بحالة {:?}",
                    r.law_id, r.status
                )));
            }
        }

        let version = 1;
        let genome_merkle_root = Self::compute_merkle_root(&receipts, epoch, version);

        Ok(Self {
            version,
            epoch,
            genome_merkle_root,
            sovereign_receipts: receipts,
        })
    }

    /// حوسبة جذر ميركل التراكمي للجينوم بـ BLAKE3
    pub fn compute_merkle_root(receipts: &[SovereignReceipt], epoch: u64, version: u32) -> [u8; 32] {
        let mut hasher = Hasher::new();
        hasher.update(MAGIC_HEADER);
        hasher.update(&version.to_le_bytes());
        hasher.update(&epoch.to_le_bytes());
        hasher.update(&(receipts.len() as u32).to_le_bytes());

        for r in receipts {
            hasher.update(&r.recompute_receipt_id());
            hasher.update(&r.canonical_id);
            hasher.update(&[r.status as u8]);
            for proof in &r.proof_chain {
                hasher.update(proof);
            }
        }

        *hasher.finalize().as_bytes()
    }

    /// التسلسل الثنائي الصرف للجينوم المعرفي بالبايتات الخام (Zero-Copy Low-Level Binary Protocol)
    pub fn to_bytes(&self) -> Result<Vec<u8>, EpistemicError> {
        let mut bytes = Vec::new();
        self.write_to_writer(&mut bytes)?;
        Ok(bytes)
    }

    /// فك التسلسل والتحقق الصارم من الترويسة السحرية وجذر ميركل
    pub fn from_bytes(bytes: &[u8]) -> Result<Self, EpistemicError> {
        let mut cursor = std::io::Cursor::new(bytes);
        Self::read_from_reader(&mut cursor)
    }

    /// كتابة الحقول بالبايتات الصرفة Little-Endian
    pub fn write_to_writer<W: Write>(&self, w: &mut W) -> Result<(), EpistemicError> {
        // 1. الترويسة السحرية (8 بايت)
        w.write_all(MAGIC_HEADER)
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;

        // 2. الحقول الرقمية بالبايتات الصرفة (Little-Endian)
        w.write_all(&self.version.to_le_bytes())
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
        w.write_all(&self.epoch.to_le_bytes())
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
        w.write_all(&(self.sovereign_receipts.len() as u32).to_le_bytes())
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;

        // 3. جذر ميركل (32 بايت خام)
        w.write_all(&self.genome_merkle_root)
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;

        // 4. تسلسل الصكوك السيادية
        for r in &self.sovereign_receipts {
            Self::write_receipt(w, r)?;
        }

        Ok(())
    }

    /// قراءة الجينوم المعرفي والتحقق من سلامة البصمات
    pub fn read_from_reader<R: Read>(r: &mut R) -> Result<Self, EpistemicError> {
        let mut magic = [0u8; 8];
        r.read_exact(&mut magic)
            .map_err(|e| EpistemicError::FormalContradiction(format!("فشل قراءة الترويسة السحرية: {}", e)))?;

        if &magic != MAGIC_HEADER {
            return Err(EpistemicError::FormalContradiction(format!(
                "ترويسة سحرية غير مطابقة للجينوم المعرفي: المتوقع {:?} والمسجل {:?}",
                MAGIC_HEADER, magic
            )));
        }

        let mut v_buf = [0u8; 4];
        r.read_exact(&mut v_buf)
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
        let version = u32::from_le_bytes(v_buf);

        let mut ep_buf = [0u8; 8];
        r.read_exact(&mut ep_buf)
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
        let epoch = u64::from_le_bytes(ep_buf);

        let mut count_buf = [0u8; 4];
        r.read_exact(&mut count_buf)
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
        let count = u32::from_le_bytes(count_buf) as usize;

        let mut root = [0u8; 32];
        r.read_exact(&mut root)
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;

        let mut receipts = Vec::with_capacity(count);
        for _ in 0..count {
            receipts.push(Self::read_receipt(r)?);
        }

        // التحقق الصارم من عدم التلاعب بمقارنة جذر ميركل المعاد حسابه
        let computed_root = Self::compute_merkle_root(&receipts, epoch, version);
        if computed_root != root {
            return Err(EpistemicError::FormalContradiction(
                "رصد خرق أمني أو تلاعب في محتوى الجينوم المعرفي: جذر ميركل لا يطابق البايتات المسترجعة!".to_string(),
            ));
        }

        Ok(Self {
            version,
            epoch,
            genome_merkle_root: root,
            sovereign_receipts: receipts,
        })
    }

    // ---------------------------------------------------------------------
    // دوال المساعدة للترميز الثنائي الخام
    // ---------------------------------------------------------------------

    pub fn write_receipt<W: Write>(w: &mut W, r: &SovereignReceipt) -> Result<(), EpistemicError> {
        w.write_all(&r.receipt_id)
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;

        Self::write_string(w, &r.law_id)?;

        w.write_all(&r.canonical_id)
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;

        Self::write_expr(w, &r.ast)?;

        // status: u8
        let status_byte = match r.status {
            LawStatus::ActiveAxiom => 1u8,
            LawStatus::ConditionalLimit => 2u8,
            LawStatus::DemarcatedBoundary => 3u8,
            LawStatus::Overthrown => 4u8,
            LawStatus::QuarantinedEpoche => 5u8,
        };
        w.write_all(&[status_byte])
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;

        // validity_regime
        if let Some(regime) = &r.validity_regime {
            w.write_all(&[1u8])
                .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
            Self::write_string(w, regime)?;
        } else {
            w.write_all(&[0u8])
                .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
        }

        // parent_law_id
        if let Some(parent) = &r.parent_law_id {
            w.write_all(&[1u8])
                .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
            Self::write_string(w, parent)?;
        } else {
            w.write_all(&[0u8])
                .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
        }

        // domain: u8 + custom_id
        match r.domain {
            DomainTag::UniversalAbstract => w.write_all(&[0u8]),
            DomainTag::ClassicalMechanics => w.write_all(&[1u8]),
            DomainTag::Electromagnetism => w.write_all(&[2u8]),
            DomainTag::Thermodynamics => w.write_all(&[3u8]),
            DomainTag::Relativity => w.write_all(&[4u8]),
            DomainTag::QuantumMechanics => w.write_all(&[5u8]),
            DomainTag::StatisticalMechanics => w.write_all(&[6u8]),
            DomainTag::Cosmology => w.write_all(&[7u8]),
            DomainTag::Custom(c_id) => {
                w.write_all(&[8u8])
                    .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
                w.write_all(&c_id.to_le_bytes())
            }
        }
        .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;

        // dimension
        w.write_all(&(r.dimension.len() as u32).to_le_bytes())
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
        for i in 0..r.dimension.len() {
            Self::write_rational(w, &r.dimension.get_coord(i))?;
        }

        // cost: 4 x u64
        w.write_all(&r.cost.size.to_le_bytes())
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
        w.write_all(&r.cost.degree.to_le_bytes())
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
        w.write_all(&r.cost.bit_complexity.to_le_bytes())
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
        w.write_all(&r.cost.transcendental.to_le_bytes())
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;

        // proof_chain
        w.write_all(&(r.proof_chain.len() as u32).to_le_bytes())
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
        for proof in &r.proof_chain {
            w.write_all(proof)
                .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
        }

        // lock_receipts
        w.write_all(&(r.lock_receipts.len() as u32).to_le_bytes())
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
        for lock in &r.lock_receipts {
            w.write_all(&[lock.lock_id as u8])
                .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
            Self::write_string(w, &lock.name)?;
            w.write_all(&[if lock.passed { 1u8 } else { 0u8 }])
                .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
            Self::write_string(w, &lock.details)?;
            if let Some(metric) = &lock.violation_metric {
                w.write_all(&[1u8])
                    .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
                Self::write_rational(w, metric)?;
            } else {
                w.write_all(&[0u8])
                    .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
            }
        }

        // asymptotic_reduction
        if let Some(asymp) = &r.asymptotic_reduction {
            w.write_all(&[1u8])
                .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
            w.write_all(asymp)
                .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
        } else {
            w.write_all(&[0u8])
                .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
        }

        // sovereignty_epoch & timestamp
        w.write_all(&r.sovereignty_epoch.to_le_bytes())
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
        w.write_all(&r.issued_at_timestamp.to_le_bytes())
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;

        Ok(())
    }

    pub fn read_receipt<R: Read>(r: &mut R) -> Result<SovereignReceipt, EpistemicError> {
        let mut receipt_id = [0u8; 32];
        r.read_exact(&mut receipt_id)
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;

        let law_id = Self::read_string(r)?;

        let mut canonical_id = [0u8; 32];
        r.read_exact(&mut canonical_id)
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;

        let ast = Self::read_expr(r)?;

        let mut status_buf = [0u8; 1];
        r.read_exact(&mut status_buf)
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
        let status = match status_buf[0] {
            1 => LawStatus::ActiveAxiom,
            2 => LawStatus::ConditionalLimit,
            3 => LawStatus::DemarcatedBoundary,
            4 => LawStatus::Overthrown,
            _ => LawStatus::QuarantinedEpoche,
        };

        let mut regime_flag = [0u8; 1];
        r.read_exact(&mut regime_flag)
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
        let validity_regime = if regime_flag[0] == 1 {
            Some(Self::read_string(r)?)
        } else {
            None
        };

        let mut parent_flag = [0u8; 1];
        r.read_exact(&mut parent_flag)
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
        let parent_law_id = if parent_flag[0] == 1 {
            Some(Self::read_string(r)?)
        } else {
            None
        };

        let mut domain_buf = [0u8; 1];
        r.read_exact(&mut domain_buf)
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
        let domain = match domain_buf[0] {
            0 => DomainTag::UniversalAbstract,
            1 => DomainTag::ClassicalMechanics,
            2 => DomainTag::Electromagnetism,
            3 => DomainTag::Thermodynamics,
            4 => DomainTag::Relativity,
            5 => DomainTag::QuantumMechanics,
            6 => DomainTag::StatisticalMechanics,
            7 => DomainTag::Cosmology,
            8 => {
                let mut c_buf = [0u8; 4];
                r.read_exact(&mut c_buf)
                    .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
                DomainTag::Custom(u32::from_le_bytes(c_buf))
            }
            _ => DomainTag::UniversalAbstract,
        };

        let mut dim_len_buf = [0u8; 4];
        r.read_exact(&mut dim_len_buf)
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
        let dim_len = u32::from_le_bytes(dim_len_buf) as usize;
        let mut coords = Vec::with_capacity(dim_len);
        for _ in 0..dim_len {
            coords.push(Self::read_rational(r)?);
        }
        let dimension = DimensionVector::from_coords(coords);

        let mut cost_buf = [0u8; 32];
        r.read_exact(&mut cost_buf)
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
        let size = u64::from_le_bytes(cost_buf[0..8].try_into().unwrap());
        let degree = u64::from_le_bytes(cost_buf[8..16].try_into().unwrap());
        let bit_complexity = u64::from_le_bytes(cost_buf[16..24].try_into().unwrap());
        let transcendental = u64::from_le_bytes(cost_buf[24..32].try_into().unwrap());
        let cost = Cost {
            size,
            degree,
            bit_complexity,
            transcendental,
        };

        let mut proof_len_buf = [0u8; 4];
        r.read_exact(&mut proof_len_buf)
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
        let proof_len = u32::from_le_bytes(proof_len_buf) as usize;
        let mut proof_chain = Vec::with_capacity(proof_len);
        for _ in 0..proof_len {
            let mut p = [0u8; 32];
            r.read_exact(&mut p)
                .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
            proof_chain.push(p);
        }

        let mut lock_len_buf = [0u8; 4];
        r.read_exact(&mut lock_len_buf)
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
        let lock_len = u32::from_le_bytes(lock_len_buf) as usize;
        let mut lock_receipts = Vec::with_capacity(lock_len);
        for _ in 0..lock_len {
            let mut l_id_buf = [0u8; 1];
            r.read_exact(&mut l_id_buf)
                .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
            let lock_id = match l_id_buf[0] {
                1 => LockType::ResidualSieve,
                2 => LockType::DimensionalLattice,
                3 => LockType::DomainIsolationBridge,
                _ => LockType::OntologicalAnchor,
            };
            let name = Self::read_string(r)?;
            let mut pass_buf = [0u8; 1];
            r.read_exact(&mut pass_buf)
                .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
            let passed = pass_buf[0] == 1;
            let details = Self::read_string(r)?;
            let mut m_flag = [0u8; 1];
            r.read_exact(&mut m_flag)
                .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
            let violation_metric = if m_flag[0] == 1 {
                Some(Self::read_rational(r)?)
            } else {
                None
            };
            lock_receipts.push(LockReceipt {
                lock_id,
                name,
                passed,
                details,
                violation_metric,
            });
        }

        let mut asymp_flag = [0u8; 1];
        r.read_exact(&mut asymp_flag)
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
        let asymptotic_reduction = if asymp_flag[0] == 1 {
            let mut a_buf = [0u8; 32];
            r.read_exact(&mut a_buf)
                .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
            Some(a_buf)
        } else {
            None
        };

        let mut epoch_buf = [0u8; 8];
        r.read_exact(&mut epoch_buf)
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
        let sovereignty_epoch = u64::from_le_bytes(epoch_buf);

        let mut ts_buf = [0u8; 8];
        r.read_exact(&mut ts_buf)
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
        let issued_at_timestamp = u64::from_le_bytes(ts_buf);

        let receipt = SovereignReceipt {
            receipt_id,
            law_id,
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
        };

        if !receipt.verify_integrity() {
            return Err(EpistemicError::FormalContradiction(format!(
                "رصد تلاعب تشفيري أو فساد في صك السيادة للقانون '{}': البصمة المسترجعة لا تطابق الحقول!",
                receipt.law_id
            )));
        }

        Ok(receipt)
    }

    fn write_string<W: Write>(w: &mut W, s: &str) -> Result<(), EpistemicError> {
        let bytes = s.as_bytes();
        w.write_all(&(bytes.len() as u32).to_le_bytes())
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
        w.write_all(bytes)
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
        Ok(())
    }

    fn read_string<R: Read>(r: &mut R) -> Result<String, EpistemicError> {
        let mut len_buf = [0u8; 4];
        r.read_exact(&mut len_buf)
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
        let len = u32::from_le_bytes(len_buf) as usize;
        let mut str_bytes = vec![0u8; len];
        r.read_exact(&mut str_bytes)
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
        String::from_utf8(str_bytes)
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))
    }

    fn write_rational<W: Write>(w: &mut W, rat: &Rational) -> Result<(), EpistemicError> {
        let s = format!("{}/{}", rat.numer(), rat.denom());
        Self::write_string(w, &s)
    }

    fn read_rational<R: Read>(r: &mut R) -> Result<Rational, EpistemicError> {
        let s = Self::read_string(r)?;
        let parts: Vec<&str> = s.split('/').collect();
        if parts.len() != 2 {
            return Err(EpistemicError::FormalContradiction(format!("كسر غير صالح: {}", s)));
        }
        let numer: i64 = parts[0]
            .parse()
            .map_err(|_| EpistemicError::FormalContradiction(format!("بسط غير صالح: {}", parts[0])))?;
        let denom: i64 = parts[1]
            .parse()
            .map_err(|_| EpistemicError::FormalContradiction(format!("مقام غير صالح: {}", parts[1])))?;
        Rational::new(numer, denom)
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))
    }

    fn write_expr<W: Write>(w: &mut W, expr: &CanonicalExpr) -> Result<(), EpistemicError> {
        match expr {
            CanonicalExpr::Const(rat) => {
                w.write_all(&[1u8])
                    .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
                Self::write_rational(w, rat)?;
            }
            CanonicalExpr::Var(VariableId(id)) => {
                w.write_all(&[2u8])
                    .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
                w.write_all(&id.to_le_bytes())
                    .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
            }
            CanonicalExpr::Add(children) => {
                w.write_all(&[3u8])
                    .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
                w.write_all(&(children.len() as u32).to_le_bytes())
                    .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
                for child in children {
                    Self::write_expr(w, child)?;
                }
            }
            CanonicalExpr::Mul(children) => {
                w.write_all(&[4u8])
                    .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
                w.write_all(&(children.len() as u32).to_le_bytes())
                    .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
                for child in children {
                    Self::write_expr(w, child)?;
                }
            }
            CanonicalExpr::Div(lhs, rhs) => {
                w.write_all(&[5u8])
                    .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
                Self::write_expr(w, lhs)?;
                Self::write_expr(w, rhs)?;
            }
            CanonicalExpr::Pow(base, exp) => {
                w.write_all(&[6u8])
                    .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
                Self::write_expr(w, base)?;
                w.write_all(&exp.to_le_bytes())
                    .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
            }
            CanonicalExpr::Neg(inner) => {
                w.write_all(&[7u8])
                    .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
                Self::write_expr(w, inner)?;
            }
        }
        Ok(())
    }

    fn read_expr<R: Read>(r: &mut R) -> Result<CanonicalExpr, EpistemicError> {
        let mut tag = [0u8; 1];
        r.read_exact(&mut tag)
            .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;

        match tag[0] {
            1 => {
                let rat = Self::read_rational(r)?;
                Ok(CanonicalExpr::Const(rat))
            }
            2 => {
                let mut v_buf = [0u8; 4];
                r.read_exact(&mut v_buf)
                    .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
                let id = u32::from_le_bytes(v_buf);
                Ok(CanonicalExpr::Var(VariableId(id)))
            }
            3 => {
                let mut len_buf = [0u8; 4];
                r.read_exact(&mut len_buf)
                    .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
                let len = u32::from_le_bytes(len_buf) as usize;
                let mut children = Vec::with_capacity(len);
                for _ in 0..len {
                    children.push(Self::read_expr(r)?);
                }
                Ok(CanonicalExpr::Add(children))
            }
            4 => {
                let mut len_buf = [0u8; 4];
                r.read_exact(&mut len_buf)
                    .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
                let len = u32::from_le_bytes(len_buf) as usize;
                let mut children = Vec::with_capacity(len);
                for _ in 0..len {
                    children.push(Self::read_expr(r)?);
                }
                Ok(CanonicalExpr::Mul(children))
            }
            5 => {
                let lhs = Self::read_expr(r)?;
                let rhs = Self::read_expr(r)?;
                Ok(CanonicalExpr::Div(Box::new(lhs), Box::new(rhs)))
            }
            6 => {
                let base = Self::read_expr(r)?;
                let mut exp_buf = [0u8; 4];
                r.read_exact(&mut exp_buf)
                    .map_err(|e| EpistemicError::FormalContradiction(e.to_string()))?;
                let exp = i32::from_le_bytes(exp_buf);
                Ok(CanonicalExpr::Pow(Box::new(base), exp))
            }
            7 => {
                let inner = Self::read_expr(r)?;
                Ok(CanonicalExpr::Neg(Box::new(inner)))
            }
            _ => Err(EpistemicError::FormalContradiction(format!(
                "وسم تعبير كنسي غير معروف في الجينوم: {}",
                tag[0]
            ))),
        }
    }
}
