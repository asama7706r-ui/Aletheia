use aletheia_algebra::{CanonicalExpr, Rational, VariableId};
use aletheia_lattice::{DimensionRegistry, DimensionVector};
use mathlex::ast::{BinaryOp, ExprKind, Expression, MathConstant, UnaryOp};
use num_rational::Ratio;
use std::collections::HashMap;

/// Cognitive symbol table mapping variable names to numerical VariableId identifiers
#[derive(Default, Clone, Debug)]
pub struct SymbolTable {
    names_to_ids: HashMap<String, VariableId>,
    ids_to_names: HashMap<VariableId, String>,
    next_id: u32,
}

impl SymbolTable {
    pub fn new() -> Self {
        Self {
            names_to_ids: HashMap::new(),
            ids_to_names: HashMap::new(),
            next_id: 1,
        }
    }

    pub fn get_or_register(&mut self, name: &str) -> VariableId {
        if let Some(&id) = self.names_to_ids.get(name) {
            id
        } else {
            let id = VariableId(self.next_id);
            self.next_id += 1;
            self.names_to_ids.insert(name.to_string(), id);
            self.ids_to_names.insert(id, name.to_string());
            id
        }
    }

    pub fn get_name(&self, id: VariableId) -> Option<&str> {
        self.ids_to_names.get(&id).map(|s| s.as_str())
    }

    pub fn len(&self) -> usize {
        self.names_to_ids.len()
    }

    pub fn is_empty(&self) -> bool {
        self.names_to_ids.is_empty()
    }
}

/// Normalizes LaTeX and mathematical notation prior to AST parsing.
/// - Handles physics macros (e.g. `\hbar` -> `hbar`, `ħ` -> `h`)
/// - Normalizes unicode operators (`·`, `×`, `÷`)
/// - Injects explicit multiplication where LaTeX juxtaposition needs clarity (e.g. `\frac{1}{2} m` -> `\frac{1}{2} \cdot m`)
pub fn preprocess_math_str(input: &str) -> String {
    let s = input.trim();
    let mut out = String::with_capacity(s.len() + 32);
    let chars: Vec<char> = s.chars().collect();
    let len = chars.len();
    let mut i = 0;

    while i < len {
        // Physics macro: \hbar
        if i + 5 <= len && s[i..].starts_with(r"\hbar") {
            out.push_str("hbar");
            i += 5;
            continue;
        }
        // Unicode ħ
        if chars[i] == 'ħ' {
            out.push_str("hbar");
            i += 1;
            continue;
        }
        // Unicode multiplication and division
        if chars[i] == '·' || chars[i] == '×' {
            out.push_str(" * ");
            i += 1;
            continue;
        }
        if chars[i] == '÷' {
            out.push_str(" / ");
            i += 1;
            continue;
        }

        // Auto-insert \cdot after closing brace if followed by an identifier or function
        // e.g. \frac{1}{2} m -> \frac{1}{2} \cdot m
        if chars[i] == '}' {
            out.push('}');
            let mut j = i + 1;
            while j < len && chars[j].is_whitespace() {
                j += 1;
            }
            if j < len {
                let next_ch = chars[j];
                if next_ch.is_alphabetic() || next_ch == '\\' || next_ch == '(' {
                    out.push_str(r" \cdot ");
                    i = j;
                    continue;
                }
            }
            i += 1;
            continue;
        }

        out.push(chars[i]);
        i += 1;
    }

    out
}

/// Parses LaTeX or plain-text mathematical notation into mathlex AST Expression.
pub fn parse_math_to_ast(input: &str) -> Result<Expression, String> {
    let clean = preprocess_math_str(input);
    if clean.is_empty() {
        return Err("Input mathematical expression is empty".to_string());
    }

    // 1. Try standard LaTeX parser
    if let Ok(expr) = mathlex::parse_latex(&clean) {
        return Ok(expr);
    }
    // 2. Try lenient LaTeX parser
    let lenient = mathlex::parse_latex_lenient(&clean);
    if let Some(expr) = lenient.expression {
        return Ok(expr);
    }
    // 3. Fallback to plain text parser
    mathlex::parse(&clean).map_err(|e| {
        format!(
            "Failed to parse mathematical expression '{}': {:?}",
            input, e
        )
    })
}

/// Converts a mathlex AST Expression into Aletheia's CanonicalExpr representation.
pub fn expr_to_canonical(
    expr: &Expression,
    symbols: &mut SymbolTable,
) -> Result<CanonicalExpr, String> {
    match &expr.kind {
        ExprKind::Integer(n) => Ok(CanonicalExpr::Const(Rational::from_i64(*n))),
        ExprKind::Float(f) => {
            let val = f.value();
            if let Some(ratio) = Ratio::from_float(val) {
                Rational::from_bigint(ratio.numer().clone(), ratio.denom().clone())
                    .map(CanonicalExpr::Const)
                    .map_err(|e| format!("{:?}", e))
            } else {
                Err(format!("Cannot convert float '{}' to exact rational", val))
            }
        }
        ExprKind::Rational {
            numerator,
            denominator,
        } => {
            let num = expr_to_canonical(numerator, symbols)?;
            let den = expr_to_canonical(denominator, symbols)?;
            if let (CanonicalExpr::Const(n), CanonicalExpr::Const(d)) = (&num, &den) {
                if let (Some(n_i), Some(d_i)) = (n.to_i64(), d.to_i64()) {
                    return Rational::new(n_i, d_i)
                        .map(CanonicalExpr::Const)
                        .map_err(|e| format!("{:?}", e));
                }
            }
            Ok(CanonicalExpr::Div(Box::new(num), Box::new(den)))
        }
        ExprKind::Variable(name) => {
            let id = symbols.get_or_register(name);
            Ok(CanonicalExpr::Var(id))
        }
        ExprKind::MarkedVector { name, .. } => {
            let id = symbols.get_or_register(name);
            Ok(CanonicalExpr::Var(id))
        }
        ExprKind::Constant(c) => {
            let name = match c {
                MathConstant::Pi => "pi",
                MathConstant::E => "e",
                MathConstant::I => "i",
                MathConstant::J => "j",
                MathConstant::K => "k",
                _ => return Err(format!("Unsupported mathematical constant {:?}", c)),
            };
            let id = symbols.get_or_register(name);
            Ok(CanonicalExpr::Var(id))
        }
        ExprKind::Unary { op, operand } => {
            let inner = expr_to_canonical(operand, symbols)?;
            match op {
                UnaryOp::Neg => Ok(CanonicalExpr::Neg(Box::new(inner))),
                UnaryOp::Pos => Ok(inner),
                _ => Err(format!("Unsupported unary operator {:?}", op)),
            }
        }
        ExprKind::Binary { op, left, right } => match op {
            BinaryOp::Add => {
                let l = expr_to_canonical(left, symbols)?;
                let r = expr_to_canonical(right, symbols)?;
                let mut terms = match l {
                    CanonicalExpr::Add(ts) => ts,
                    other => vec![other],
                };
                match r {
                    CanonicalExpr::Add(ts) => terms.extend(ts),
                    other => terms.push(other),
                }
                Ok(CanonicalExpr::Add(terms))
            }
            BinaryOp::Sub => {
                let l = expr_to_canonical(left, symbols)?;
                let r = expr_to_canonical(right, symbols)?;
                let neg_r = CanonicalExpr::Neg(Box::new(r));
                let mut terms = match l {
                    CanonicalExpr::Add(ts) => ts,
                    other => vec![other],
                };
                terms.push(neg_r);
                Ok(CanonicalExpr::Add(terms))
            }
            BinaryOp::Mul => {
                let l = expr_to_canonical(left, symbols)?;
                let r = expr_to_canonical(right, symbols)?;
                let mut factors = match l {
                    CanonicalExpr::Mul(fs) => fs,
                    other => vec![other],
                };
                match r {
                    CanonicalExpr::Mul(fs) => factors.extend(fs),
                    other => factors.push(other),
                }
                Ok(CanonicalExpr::Mul(factors))
            }
            BinaryOp::Div => {
                let l = expr_to_canonical(left, symbols)?;
                let r = expr_to_canonical(right, symbols)?;
                if let (CanonicalExpr::Const(n), CanonicalExpr::Const(d)) = (&l, &r) {
                    if !d.is_zero() {
                        let div = n.clone() / d.clone();
                        return Ok(CanonicalExpr::Const(div));
                    }
                }
                Ok(CanonicalExpr::Div(Box::new(l), Box::new(r)))
            }
            BinaryOp::Pow => {
                let base = expr_to_canonical(left, symbols)?;
                let exp = extract_integer_exponent(right)?;
                Ok(CanonicalExpr::Pow(Box::new(base), exp))
            }
            _ => Err(format!("Unsupported binary operator {:?}", op)),
        },
        ExprKind::Equation { .. } => Err(
            "Encountered unexpected equation inside single expression. Use parse_equation for two-sided equations."
                .to_string(),
        ),
        other => Err(format!(
            "Unsupported LaTeX expression AST construct: {:?}",
            other
        )),
    }
}

fn extract_integer_exponent(expr: &Expression) -> Result<i32, String> {
    match &expr.kind {
        ExprKind::Integer(n) => Ok(*n as i32),
        ExprKind::Unary {
            op: UnaryOp::Neg,
            operand,
        } => {
            if let ExprKind::Integer(n) = &operand.kind {
                Ok(-(*n as i32))
            } else {
                Err("Power exponent must be an integer".to_string())
            }
        }
        _ => Err("Power exponent must be an integer".to_string()),
    }
}

/// Parses a mathematical expression string (LaTeX or algebraic notation) into a CanonicalExpr.
pub fn parse_expr(input: &str, symbols: &mut SymbolTable) -> Result<CanonicalExpr, String> {
    let ast = parse_math_to_ast(input)?;
    expr_to_canonical(&ast, symbols)
}

/// Parses a two-sided equation (LHS = RHS) written in LaTeX or standard mathematical notation.
pub fn parse_equation(
    input: &str,
    symbols: &mut SymbolTable,
) -> Result<(CanonicalExpr, CanonicalExpr), String> {
    let clean = preprocess_math_str(input);
    if clean.is_empty() {
        return Err("Input equation is empty".to_string());
    }

    // 1. Try parsing directly as an AST Equation node
    if let Ok(ast) = parse_math_to_ast(&clean) {
        if let ExprKind::Equation { left, right } = &ast.kind {
            let lhs = expr_to_canonical(left, symbols)?;
            let rhs = expr_to_canonical(right, symbols)?;
            return Ok((lhs, rhs));
        }
    }

    // 2. Fallback: split on equality characters '=' or '≟' or '~' or '➔'
    let eq_delims = ['=', '≟', '~', '➔'];
    let mut split_pos = None;
    for (i, ch) in clean.chars().enumerate() {
        if eq_delims.contains(&ch) {
            split_pos = Some(i);
            break;
        }
    }

    if let Some(pos) = split_pos {
        let lhs_str = clean[..pos].trim();
        let rhs_str = clean[pos + 1..].trim();
        if lhs_str.is_empty() || rhs_str.is_empty() {
            return Err("Equation must contain expressions on both sides of '='".to_string());
        }
        let lhs = parse_expr(lhs_str, symbols)?;
        let rhs = parse_expr(rhs_str, symbols)?;
        return Ok((lhs, rhs));
    }

    Err("No equality sign '=' found in equation".to_string())
}

/// Parses a physical dimension string strictly by its dimensional invariants:
/// 1. Bracketed keyed coordinate vector: e.g. '[L: 2, M: 1, T: -2]'
/// 2. Direct numerical coordinate vector: e.g. '[2, 1, -2]' or '2, 1, -2'
/// 3. LaTeX / algebraic compound expression over base dimensions: e.g. '\frac{L^2 \cdot M}{T^2}', 'L^2 * M / T^2', 'L / T'
/// 4. Pure dimensionless scalar: '1', '[1]', 'dimensionless', 'scalar', or empty
pub fn parse_dimension_str(input: &str) -> Result<DimensionVector, String> {
    let registry = DimensionRegistry::new();
    parse_dimension_str_with_registry(input, &registry)
}

/// Parses a dimension string using the provided DimensionRegistry (supporting custom/spawned base dimensions)
pub fn parse_dimension_str_with_registry(
    input: &str,
    registry: &DimensionRegistry,
) -> Result<DimensionVector, String> {
    let s = input.trim();
    if s.is_empty()
        || s == "1"
        || s == "[1]"
        || s.eq_ignore_ascii_case("dimensionless")
        || s.eq_ignore_ascii_case("scalar")
    {
        return Ok(DimensionVector::dimensionless());
    }

    // 1. Bracketed keyed coordinate vector: e.g. [L: 2, M: 1, T: -2]
    if s.starts_with('[') && s.ends_with(']') && s.contains(':') {
        let inner = &s[1..s.len() - 1];
        let mut vec = DimensionVector::dimensionless();
        for item in inner.split(',') {
            let item = item.trim();
            if item.is_empty() {
                continue;
            }
            let parts: Vec<&str> = item.splitn(2, ':').collect();
            if parts.len() != 2 {
                return Err(format!(
                    "Invalid keyed dimension syntax '{}'. Expected 'SYMBOL: EXPONENT'",
                    item
                ));
            }
            let sym = parts[0].trim();
            let exp: i64 = parts[1]
                .trim()
                .parse()
                .map_err(|_| format!("Invalid exponent in keyed dimension '{}'", item))?;
            let dim_id = registry
                .find_by_symbol(sym)
                .or_else(|| registry.find_dimension(sym))
                .ok_or_else(|| {
                    format!(
                        "Unknown base dimension symbol '{}' in keyed dimension vector",
                        sym
                    )
                })?;
            vec.set_coord(dim_id.0, Rational::from_i64(exp));
        }
        return Ok(vec);
    }

    // 2. Numerical coordinate vector: [c0, c1, c2, ...] or comma-separated integers
    let stripped = s.trim_start_matches('[').trim_end_matches(']');
    if stripped.contains(',')
        || (stripped.split_whitespace().count() > 1
            && !stripped.contains('*')
            && !stripped.contains('/')
            && !stripped.contains('^')
            && !stripped.contains('\\'))
    {
        let parts: Vec<&str> = if stripped.contains(',') {
            stripped.split(',').collect()
        } else {
            stripped.split_whitespace().collect()
        };
        let mut ints = Vec::new();
        let mut is_numeric_list = true;
        for part in parts {
            let p = part.trim();
            if let Ok(val) = p.parse::<i64>() {
                ints.push(val);
            } else {
                is_numeric_list = false;
                break;
            }
        }
        if is_numeric_list && !ints.is_empty() {
            return Ok(DimensionVector::from_integers(&ints));
        }
    }

    // 3. Algebraic / LaTeX dimensional expression of base dimensions
    parse_dimensional_algebraic_expr_with_registry(s, registry)
}

/// Evaluates a LaTeX or algebraic dimensional expression (e.g. \frac{L^2 \cdot M}{T^2} or L^2 * M / T^2)
fn parse_dimensional_algebraic_expr_with_registry(
    input: &str,
    registry: &DimensionRegistry,
) -> Result<DimensionVector, String> {
    let mut symbols = SymbolTable::new();
    let ast = parse_expr(input, &mut symbols)?;
    eval_dim_ast_with_registry(&ast, &symbols, registry)
}

fn eval_dim_ast_with_registry(
    expr: &CanonicalExpr,
    symbols: &SymbolTable,
    registry: &DimensionRegistry,
) -> Result<DimensionVector, String> {
    match expr {
        CanonicalExpr::Const(r) => {
            if r.is_one() {
                Ok(DimensionVector::dimensionless())
            } else {
                Err(format!(
                    "Scalar constants in dimensional expressions must be 1 (found {})",
                    r
                ))
            }
        }
        CanonicalExpr::Var(id) => {
            let orig = symbols.get_name(*id).unwrap_or("");
            if orig.is_empty() {
                return Err("Empty dimension symbol in expression".to_string());
            }

            // Case-sensitive SI base symbol conventions
            if orig == "m" || orig == "M" {
                if orig == "M" {
                    // M: Mass [0, 1, 0]
                    return Ok(DimensionVector::unit_basis(
                        DimensionRegistry::MASS_IDX,
                        registry.dimension_count(),
                    ));
                } else {
                    // m: Length [1, 0, 0]
                    return Ok(DimensionVector::unit_basis(
                        DimensionRegistry::LENGTH_IDX,
                        registry.dimension_count(),
                    ));
                }
            }

            // 1. Direct symbol lookup in DimensionRegistry
            if let Some(dim_id) = registry.find_by_symbol(orig) {
                return registry.unit_basis(dim_id).map_err(|e| e.to_string());
            }

            // 2. Direct name lookup in DimensionRegistry
            if let Some(dim_id) = registry.find_dimension(orig) {
                return registry.unit_basis(dim_id).map_err(|e| e.to_string());
            }

            // 3. Dynamic orthogonal base indices: D0, D1, D7, ...
            let upper = orig.to_uppercase();
            if let Some(num_str) = upper.strip_prefix('D') {
                if let Ok(idx) = num_str.parse::<usize>() {
                    let total = (idx + 1).max(registry.dimension_count());
                    return Ok(DimensionVector::unit_basis(idx, total));
                }
            }

            Err(format!(
                "Unrecognized dimension symbol '{}'. Quantities must be specified strictly by their dimensions using base symbols (e.g. L, M, T, I, Θ, N, J, or D0..D9) or coordinate vectors (e.g. [2, 1, -2]).",
                orig
            ))
        }
        CanonicalExpr::Mul(factors) => {
            let mut sum = DimensionVector::dimensionless();
            for f in factors {
                sum = sum + eval_dim_ast_with_registry(f, symbols, registry)?;
            }
            Ok(sum)
        }
        CanonicalExpr::Div(num, den) => {
            let d_num = eval_dim_ast_with_registry(num, symbols, registry)?;
            let d_den = eval_dim_ast_with_registry(den, symbols, registry)?;
            Ok(d_num - d_den)
        }
        CanonicalExpr::Pow(base, p) => {
            let d_base = eval_dim_ast_with_registry(base, symbols, registry)?;
            Ok(scale_dimension_vector(&d_base, *p as i64))
        }
        CanonicalExpr::Neg(base) => {
            let d = eval_dim_ast_with_registry(base, symbols, registry)?;
            Ok(scale_dimension_vector(&d, -1))
        }
        CanonicalExpr::Add(terms) => {
            if terms.is_empty() {
                return Ok(DimensionVector::dimensionless());
            }
            let first = eval_dim_ast_with_registry(&terms[0], symbols, registry)?;
            for t in &terms[1..] {
                let d = eval_dim_ast_with_registry(t, symbols, registry)?;
                if d != first {
                    return Err(
                        "Additive terms in dimensional formula are not dimensionally homogeneous"
                            .to_string(),
                    );
                }
            }
            Ok(first)
        }
    }
}

fn scale_dimension_vector(dim: &DimensionVector, p: i64) -> DimensionVector {
    let coords = (0..dim.len())
        .map(|k| dim.get_coord(k) * Rational::from_i64(p))
        .collect::<Vec<_>>();
    DimensionVector::from_coords(coords)
}

pub fn split_respecting_brackets(input: &str) -> Vec<String> {
    split_respecting_brackets_by(input, &[',', ';'])
}

pub fn split_respecting_brackets_by(input: &str, delims: &[char]) -> Vec<String> {
    let mut result = Vec::new();
    let mut current = String::new();
    let mut depth: i32 = 0;

    for ch in input.chars() {
        match ch {
            '[' | '(' | '{' => {
                depth += 1;
                current.push(ch);
            }
            ']' | ')' | '}' => {
                depth = depth.saturating_sub(1);
                current.push(ch);
            }
            c if depth == 0 && delims.contains(&c) => {
                if !current.trim().is_empty() {
                    result.push(current.trim().to_string());
                }
                current.clear();
            }
            _ => {
                current.push(ch);
            }
        }
    }
    if !current.trim().is_empty() {
        result.push(current.trim().to_string());
    }
    result
}

/// Parses variable dimension bindings:
/// Format: "E: L^2 * M / T^2, m: M" or "F: [1, 1, -2], m: [0, 1, 0]"
pub fn parse_variable_bindings(
    input: &str,
    symbols: &mut SymbolTable,
) -> Result<HashMap<VariableId, DimensionVector>, String> {
    let mut map = HashMap::new();
    let items = split_respecting_brackets(input);

    for trimmed in items {
        if trimmed.is_empty() {
            continue;
        }
        let parts: Vec<&str> = trimmed.splitn(2, ':').collect();
        if parts.len() != 2 {
            return Err(format!(
                "Invalid variable binding syntax '{}'. Expected 'variable: dimension'",
                trimmed
            ));
        }
        let var_name = parts[0].trim();
        let dim_str = parts[1].trim();

        let var_id = symbols.get_or_register(var_name);
        let dim = parse_dimension_str(dim_str)?;
        map.insert(var_id, dim);
    }

    Ok(map)
}

/// Parses candidate physical bases:
/// Format: "c: L / T, G: L^3 / (M * T^2), hbar: L^2 * M / T"
/// or simply "L / T, [3, -1, -2]"
pub fn parse_candidate_bases(input: &str) -> Result<Vec<(String, DimensionVector)>, String> {
    let mut result = Vec::new();
    let items = split_respecting_brackets(input);

    for trimmed in items {
        if trimmed.is_empty() {
            continue;
        }

        if trimmed.contains(':') {
            let parts: Vec<&str> = trimmed.splitn(2, ':').collect();
            if parts.len() != 2 {
                return Err(format!(
                    "Invalid candidate base syntax '{}'. Expected 'name: dimension'",
                    trimmed
                ));
            }
            let name = parts[0].trim().to_string();
            let dim = parse_dimension_str(parts[1].trim())?;
            result.push((name, dim));
        } else {
            let dim = parse_dimension_str(&trimmed)?;
            let name = format!("{}", dim);
            result.push((name, dim));
        }
    }

    Ok(result)
}

/// Formats a canonical algebraic expression into a clean mathematical string
pub fn format_expr(expr: &CanonicalExpr, symbols: &SymbolTable) -> String {
    format_expr_precedence(expr, symbols, 0)
}

/// Formats a two-sided equation (LHS = RHS) into a mathematical string
pub fn format_equation(lhs: &CanonicalExpr, rhs: &CanonicalExpr, symbols: &SymbolTable) -> String {
    format!(
        "{} = {}",
        format_expr(lhs, symbols),
        format_expr(rhs, symbols)
    )
}

fn format_expr_precedence(expr: &CanonicalExpr, symbols: &SymbolTable, parent_prec: u8) -> String {
    match expr {
        CanonicalExpr::Const(r) => format!("{}", r),
        CanonicalExpr::Var(id) => symbols
            .get_name(*id)
            .map(|s| s.to_string())
            .unwrap_or_else(|| format!("x_{}", id.0)),
        CanonicalExpr::Neg(inner) => {
            let inner_str = format_expr_precedence(inner, symbols, 4);
            if parent_prec > 3 {
                format!("(-{})", inner_str)
            } else {
                format!("-{}", inner_str)
            }
        }
        CanonicalExpr::Pow(base, p) => {
            let base_str = format_expr_precedence(base, symbols, 4);
            let pow_str = format!("{}^{}", base_str, p);
            if parent_prec > 4 {
                format!("({})", pow_str)
            } else {
                pow_str
            }
        }
        CanonicalExpr::Mul(factors) => {
            if factors.is_empty() {
                return "1".to_string();
            }
            let parts: Vec<String> = factors
                .iter()
                .map(|f| format_expr_precedence(f, symbols, 2))
                .collect();
            let mul_str = parts.join(" * ");
            if parent_prec > 2 {
                format!("({})", mul_str)
            } else {
                mul_str
            }
        }
        CanonicalExpr::Div(num, den) => {
            let num_str = format_expr_precedence(num, symbols, 3);
            let den_str = format_expr_precedence(den, symbols, 3);
            let div_str = format!("{} / {}", num_str, den_str);
            if parent_prec > 2 {
                format!("({})", div_str)
            } else {
                div_str
            }
        }
        CanonicalExpr::Add(terms) => {
            if terms.is_empty() {
                return "0".to_string();
            }
            let mut res = String::new();
            for (i, t) in terms.iter().enumerate() {
                if i > 0 {
                    res.push_str(" + ");
                }
                res.push_str(&format_expr_precedence(t, symbols, 1));
            }
            if parent_prec > 1 {
                format!("({})", res)
            } else {
                res
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_expression_simple() {
        let mut symbols = SymbolTable::new();
        let expr = parse_expr("E", &mut symbols).unwrap();
        assert!(matches!(expr, CanonicalExpr::Var(_)));
        assert_eq!(symbols.get_name(VariableId(1)), Some("E"));
    }

    #[test]
    fn test_parse_equation_einstein_latex() {
        let mut symbols = SymbolTable::new();
        let (lhs, rhs) = parse_equation(r"E = m c^2", &mut symbols).unwrap();
        assert!(matches!(lhs, CanonicalExpr::Var(_)));
        assert!(matches!(rhs, CanonicalExpr::Mul(_)));
        assert_eq!(symbols.get_name(VariableId(1)), Some("E"));
        assert_eq!(symbols.get_name(VariableId(2)), Some("m"));
        assert_eq!(symbols.get_name(VariableId(3)), Some("c"));

        let formatted = format_equation(&lhs, &rhs, &symbols);
        assert!(formatted.contains("E ="));
        assert!(formatted.contains("m"));
        assert!(formatted.contains("c^2"));
    }

    #[test]
    fn test_parse_equation_newton_latex_fraction() {
        let mut symbols = SymbolTable::new();
        let (lhs, rhs) = parse_equation(r"F = G \frac{m_1 m_2}{r^2}", &mut symbols).unwrap();
        assert!(matches!(lhs, CanonicalExpr::Var(_)));
        assert!(matches!(rhs, CanonicalExpr::Mul(_)));

        let formatted = format_equation(&lhs, &rhs, &symbols);
        assert!(formatted.contains("F ="));
        assert!(formatted.contains("G"));
        assert!(formatted.contains("m_1"));
        assert!(formatted.contains("m_2"));
        assert!(formatted.contains("r^2"));
    }

    #[test]
    fn test_pure_dimension_recognition_latex_and_coords() {
        // 1. Direct coordinate vectors
        let dim_coords = parse_dimension_str("[2, 1, -2]").unwrap();
        assert_eq!(dim_coords.get_coord(0), Rational::from_i64(2));
        assert_eq!(dim_coords.get_coord(1), Rational::from_i64(1));
        assert_eq!(dim_coords.get_coord(2), Rational::from_i64(-2));

        // 2. Bracketed keyed coordinates
        let dim_keyed = parse_dimension_str("[L: 2, M: 1, T: -2]").unwrap();
        assert_eq!(dim_coords, dim_keyed);

        // 3. LaTeX fraction dimension
        let dim_latex = parse_dimension_str(r"\frac{L^2 \cdot M}{T^2}").unwrap();
        assert_eq!(dim_coords, dim_latex);

        // 4. Algebraic base dimension expression
        let dim_alg = parse_dimension_str("L^2 * M / T^2").unwrap();
        assert_eq!(dim_coords, dim_alg);

        // 5. Velocity
        let dim_v_alg = parse_dimension_str("L / T").unwrap();
        let dim_v_latex = parse_dimension_str(r"\frac{L}{T}").unwrap();
        let dim_v_vec = parse_dimension_str("[1, 0, -1]").unwrap();
        assert_eq!(dim_v_alg, dim_v_vec);
        assert_eq!(dim_v_latex, dim_v_vec);

        // 6. Non-dimensional / scalar
        assert!(parse_dimension_str("1").unwrap().is_dimensionless());
        assert!(parse_dimension_str("dimensionless").unwrap().is_dimensionless());

        // 7. Rejection of ad-hoc human names (only dimensions allowed!)
        assert!(parse_dimension_str("energy").is_err());
        assert!(parse_dimension_str("force").is_err());
        assert!(parse_dimension_str("viscosity").is_err());
    }

    #[test]
    fn test_custom_registered_dimension_recognition() {
        let mut reg = DimensionRegistry::new();
        let bit_id = reg
            .register_orthogonal_with_symbol("InformationBit", "B")
            .unwrap();
        assert_eq!(bit_id.0, 7);

        let parsed = parse_dimension_str_with_registry("B / T", &reg).unwrap();
        assert_eq!(parsed.get_coord(7), Rational::from_i64(1));
        assert_eq!(parsed.get_coord(2), Rational::from_i64(-1));

        let parsed_latex = parse_dimension_str_with_registry(r"\frac{B}{T}", &reg).unwrap();
        assert_eq!(parsed_latex, parsed);
    }

    #[test]
    fn test_parse_variable_bindings_and_candidates() {
        let mut symbols = SymbolTable::new();
        let bindings =
            parse_variable_bindings("E: L^2 * M / T^2, m: M", &mut symbols).unwrap();
        assert_eq!(bindings.len(), 2);

        let candidates =
            parse_candidate_bases("c: L / T, G: L^3 / (M * T^2), hbar: L^2 * M / T").unwrap();
        assert_eq!(candidates.len(), 3);
        assert_eq!(candidates[0].0, "c");
        assert_eq!(
            candidates[0].1,
            DimensionVector::from_integers(&[1, 0, -1])
        );
        assert_eq!(candidates[1].0, "G");
        assert_eq!(
            candidates[1].1,
            DimensionVector::from_integers(&[3, -1, -2])
        );
        assert_eq!(candidates[2].0, "hbar");
        assert_eq!(
            candidates[2].1,
            DimensionVector::from_integers(&[2, 1, -1])
        );
    }
}
