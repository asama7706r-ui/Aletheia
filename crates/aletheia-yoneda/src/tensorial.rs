/// توصيف الرتبة الهندسية والتنسورية لكائن رياضي أو فيزيائي
#[derive(Clone, Copy, Debug, PartialEq, Eq, Default)]
pub struct TensorSignature {
    /// رتبة التنافر (Contravariant Indices / Upper: p)
    pub contravariant: usize,
    /// رتبة التوافق (Covariant Indices / Lower: q)
    pub covariant: usize,
}

impl TensorSignature {
    pub fn scalar() -> Self {
        Self {
            contravariant: 0,
            covariant: 0,
        }
    }

    pub fn vector() -> Self {
        Self {
            contravariant: 1,
            covariant: 0,
        }
    }

    pub fn form_1() -> Self {
        Self {
            contravariant: 0,
            covariant: 1,
        }
    }

    pub fn rank_2_tensor() -> Self {
        Self {
            contravariant: 1,
            covariant: 1,
        }
    }

    #[inline]
    pub fn total_rank(&self) -> usize {
        self.contravariant + self.covariant
    }

    #[inline]
    pub fn is_scalar(&self) -> bool {
        self.total_rank() == 0
    }
}

/// نتيجة قياس عجز الرتبة التنسورية وانكماش أينشتاين
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct TensorialRankGap {
    pub p_gap: i32,
    pub q_gap: i32,
    pub required_rank: usize,
    pub is_scalar_invariant: bool,
}

/// محرك تتبع الرتب التنسورية وانكماش أينشتاين (Einstein Contraction Engine)
pub struct TensorialEngine;

impl TensorialEngine {
    /// قياس الفجوة التنسورية الصافية بين طرفين: Delta r = (p1 - p2, q1 - q2)
    pub fn compute_rank_gap(lhs: TensorSignature, rhs: TensorSignature) -> TensorialRankGap {
        let p_gap = (lhs.contravariant as i32) - (rhs.contravariant as i32);
        let q_gap = (lhs.covariant as i32) - (rhs.covariant as i32);

        let required_rank = (p_gap.abs() + q_gap.abs()) as usize;
        let is_scalar_invariant = required_rank == 0;

        TensorialRankGap {
            p_gap,
            q_gap,
            required_rank,
            is_scalar_invariant,
        }
    }

    /// التحقق مما إذا كان انكماش أينشتاين ممكناً لسد الفجوة التنسورية
    pub fn can_contract_to_scalar(gap: TensorialRankGap, candidate: TensorSignature) -> bool {
        if gap.is_scalar_invariant {
            candidate.is_scalar()
        } else {
            // يشترط أن تكون رتبة المرشح متوافقة ومتقابلة مع الفجوة لتحقيق الانكماش التام
            candidate.total_rank() == gap.required_rank
        }
    }
}
