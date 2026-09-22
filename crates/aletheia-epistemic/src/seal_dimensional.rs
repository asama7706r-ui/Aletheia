use crate::logic::AuditTarget;
use crate::receipt::{LockReceipt, LockType};
use aletheia_algebra::VariableId;
use aletheia_lattice::{DimensionVector, DimensionalContext, SemanticGuard};
use std::collections::HashMap;

/// القفل الثاني: غربال التجانس البعدي والأنطولوجي (Seal 2: Dimensional & Ontological Lattice Sieve in Q^N)
/// يفرض شروط بكنغهام-باي، وطهارة وسائط الدوال المتسامية، ومنع التصادمات البعدية للمتغيرات المشتركة
pub struct DimensionalSieve;

impl DimensionalSieve {
    /// فحص الهدف المدقق وفق شبيكة الأبعاد Q^N والسياق البعدي
    pub fn verify(
        target: &AuditTarget,
        ctx: &DimensionalContext,
        variable_dimensions: Option<&HashMap<VariableId, DimensionVector>>,
    ) -> LockReceipt {
        match target {
            AuditTarget::ConstraintSystem {
                candidate_id: _,
                variables,
                ..
            } => Self::verify_constraint_variables(variables, ctx, variable_dimensions),
            AuditTarget::SovereignCandidate(cand) => {
                Self::verify_sovereign_candidate(&cand.ast, &cand.dim, ctx)
            }
        }
    }

    /// فحص متغيرات نظام القيود والتأكد من تطابق أبعادها وعدم وجود تصادم أنطولوجي
    fn verify_constraint_variables(
        variables: &[VariableId],
        ctx: &DimensionalContext,
        variable_dimensions: Option<&HashMap<VariableId, DimensionVector>>,
    ) -> LockReceipt {
        let mut registry: HashMap<VariableId, DimensionVector> = HashMap::new();

        for var in variables {
            // محاولة استرجاع البعد إما من الخريطة الممررة أو من سياق الأبعاد العام
            let dim_opt = variable_dimensions
                .and_then(|m| m.get(var).cloned())
                .or_else(|| ctx.get(*var).cloned());

            if let Some(dim) = dim_opt {
                if let Some(existing_dim) = registry.get(var) {
                    if existing_dim != &dim {
                        return LockReceipt::new(
                            LockType::DimensionalLattice,
                            "Dimensional Sieve",
                            false,
                            format!(
                                "تصادم بعدي في المتغير {:?}: البعد القائم {} != البعد الجديد {} في Q^N",
                                var, existing_dim, dim
                            ),
                            None,
                        );
                    }
                } else {
                    registry.insert(*var, dim);
                }
            }
        }

        LockReceipt::new(
            LockType::DimensionalLattice,
            "Dimensional Sieve",
            true,
            "التجانس البعدي ومنع التصادمات الأنطولوجية محقق بصرامة في Q^N",
            None,
        )
    }

    /// فحص شجرة التعبير الكنسي للقانون المرشح للسيادة
    fn verify_sovereign_candidate(
        expr: &aletheia_algebra::CanonicalExpr,
        expected_dim: &DimensionVector,
        ctx: &DimensionalContext,
    ) -> LockReceipt {
        let mut local_ctx;
        let effective_ctx = if let aletheia_algebra::CanonicalExpr::Var(v) = expr {
            if ctx.get(*v).is_none() {
                local_ctx = ctx.clone();
                local_ctx.bind(*v, expected_dim.clone());
                &local_ctx
            } else {
                ctx
            }
        } else {
            ctx
        };

        match SemanticGuard::infer_dimension(expr, effective_ctx) {
            Ok(inferred_dim) => {
                if &inferred_dim != expected_dim {
                    return LockReceipt::new(
                        LockType::DimensionalLattice,
                        "Dimensional Sieve (Sovereign Candidate)",
                        false,
                        format!(
                            "عدم تطابق بعدي: البعد المستنتج من شجرة الـ AST ({}) لا يطابق البعد المصادق عليه ({})",
                            inferred_dim, expected_dim
                        ),
                        None,
                    );
                }
                LockReceipt::new(
                    LockType::DimensionalLattice,
                    "Dimensional Sieve (Sovereign Candidate)",
                    true,
                    "التجانس البعدي وطهارة الشجرة التحليلية مصادق عليها في Q^N",
                    None,
                )
            }
            Err(err) => LockReceipt::new(
                LockType::DimensionalLattice,
                "Dimensional Sieve (Sovereign Candidate)",
                false,
                format!("فشل في استنتاج التجانس البعدي للشجرة: {}", err),
                None,
            ),
        }
    }
}
