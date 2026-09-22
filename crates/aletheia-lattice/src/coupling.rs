use crate::vector::DimensionVector;
use aletheia_algebra::Rational;

/// حساب متجه فجوة الأبعاد (Dimensional Gap Vector)
/// عند رصد علاقة فيزيائية بين كميات: Y ~ X_1^a1 * X_2^a2 * ...
/// Delta_dim = d_Y - sum(a_i * d_X_i)
pub fn calculate_dimensional_gap(
    target_dim: &DimensionVector,
    factors: &[(&DimensionVector, &Rational)],
) -> DimensionVector {
    let mut factors_sum = DimensionVector::dimensionless();
    for (dim, exp) in factors {
        factors_sum += dim.scale(exp);
    }
    target_dim - &factors_sum
}

/// توليد وتحديد متجه أبعاد ثابت الاقتران الكوني (Coupling Constant Synthesis)
/// لسد الفجوة البُعدية وجعل المعادلة متجانسة بالكامل: d_k_bridge = Delta_dim
pub fn synthesize_coupling_constant(gap: &DimensionVector) -> DimensionVector {
    gap.clone()
}

/// اشتقاق أبعاد ثابت الجاذبية العام لنيوتن G تلقائياً
/// من قانون الجاذبية: F ~ m1 * m2 / r^2
pub fn synthesize_newton_g(
    force_dim: &DimensionVector,
    mass_dim: &DimensionVector,
    length_dim: &DimensionVector,
) -> DimensionVector {
    // الطرف الأيمن: mass^2 * length^(-2)
    let two = Rational::from_i64(2);
    let neg_two = Rational::from_i64(-2);
    let gap = calculate_dimensional_gap(
        force_dim,
        &[(mass_dim, &two), (length_dim, &neg_two)],
    );
    // [G] = -gap
    synthesize_coupling_constant(&gap)
}

/// اشتقاق أبعاد ثابت بلانك h تلقائياً
/// من علاقة بلانك-أينشتاين: E ~ nu (حيث nu هو التردد T^(-1))
pub fn synthesize_planck_h(
    energy_dim: &DimensionVector,
    time_dim: &DimensionVector,
) -> DimensionVector {
    // التردد nu = time^(-1)
    let neg_one = Rational::from_i64(-1);
    let gap = calculate_dimensional_gap(
        energy_dim,
        &[(time_dim, &neg_one)],
    );
    synthesize_coupling_constant(&gap)
}

/// اشتقاق أبعاد ثابت كولوم k_e تلقائياً
/// من قانون كولوم: F ~ q1 * q2 / r^2 (حيث الشحنة q = I * T)
pub fn synthesize_coulomb_ke(
    force_dim: &DimensionVector,
    current_dim: &DimensionVector,
    time_dim: &DimensionVector,
    length_dim: &DimensionVector,
) -> DimensionVector {
    // الشحنة q = current * time
    let charge_dim = current_dim + time_dim;
    let two = Rational::from_i64(2);
    let neg_two = Rational::from_i64(-2);
    let gap = calculate_dimensional_gap(
        force_dim,
        &[(&charge_dim, &two), (length_dim, &neg_two)],
    );
    synthesize_coupling_constant(&gap)
}
