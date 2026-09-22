use aletheia_algebra::{CanonicalExpr, Rational, VariableId};
use aletheia_lattice::DimensionVector;
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

/// Lexical tokens for mathematical parsing
#[derive(Debug, Clone, PartialEq)]
enum Token {
    Number(i64, i64), // numerator and denominator
    Ident(String),
    Plus,
    Minus,
    Star,
    Slash,
    Caret,
    LParen,
    RParen,
    Equal,
}

struct Lexer<'a> {
    input: &'a [char],
    pos: usize,
}

impl<'a> Lexer<'a> {
    fn new(chars: &'a [char]) -> Self {
        Self { input: chars, pos: 0 }
    }

    fn skip_whitespace(&mut self) {
        while self.pos < self.input.len() && self.input[self.pos].is_whitespace() {
            self.pos += 1;
        }
    }

    fn next_token(&mut self) -> Result<Option<Token>, String> {
        self.skip_whitespace();
        if self.pos >= self.input.len() {
            return Ok(None);
        }

        let ch = self.input[self.pos];

        if ch.is_ascii_digit() {
            let mut num_str = String::new();
            while self.pos < self.input.len() && self.input[self.pos].is_ascii_digit() {
                num_str.push(self.input[self.pos]);
                self.pos += 1;
            }
            let val = num_str.parse::<i64>().map_err(|e| e.to_string())?;
            return Ok(Some(Token::Number(val, 1)));
        }

        if ch.is_alphabetic() || ch == '_' || ch == 'ħ' || ch == 'Θ' || ch == 'θ' || ch == 'μ' || ch == 'ε' || ch == 'ν' {
            let mut ident = String::new();
            while self.pos < self.input.len() {
                let c = self.input[self.pos];
                if c.is_alphanumeric() || c == '_' || c == 'ħ' || c == 'Θ' || c == 'θ' || c == 'μ' || c == 'ε' || c == 'ν' {
                    ident.push(c);
                    self.pos += 1;
                } else {
                    break;
                }
            }
            return Ok(Some(Token::Ident(ident)));
        }

        self.pos += 1;
        match ch {
            '+' => Ok(Some(Token::Plus)),
            '-' => Ok(Some(Token::Minus)),
            '*' | '·' | '×' => Ok(Some(Token::Star)),
            '/' | '÷' => Ok(Some(Token::Slash)),
            '^' => Ok(Some(Token::Caret)),
            '(' | '[' => Ok(Some(Token::LParen)),
            ')' | ']' => Ok(Some(Token::RParen)),
            '=' | '≟' | '~' | '➔' => Ok(Some(Token::Equal)),
            _ => Err(format!("Unknown character during lexical analysis: '{}'", ch)),
        }
    }
}

/// Canonical algebraic expression parser
struct ExprParser<'a> {
    tokens: Vec<Token>,
    pos: usize,
    symbols: &'a mut SymbolTable,
}

impl<'a> ExprParser<'a> {
    fn new(tokens: Vec<Token>, symbols: &'a mut SymbolTable) -> Self {
        Self { tokens, pos: 0, symbols }
    }

    fn peek(&self) -> Option<&Token> {
        self.tokens.get(self.pos)
    }

    fn next(&mut self) -> Option<Token> {
        if self.pos < self.tokens.len() {
            let tok = self.tokens[self.pos].clone();
            self.pos += 1;
            Some(tok)
        } else {
            None
        }
    }

    fn parse_expression(&mut self) -> Result<CanonicalExpr, String> {
        let mut left = self.parse_term()?;

        while let Some(tok) = self.peek() {
            match tok {
                Token::Plus => {
                    self.next();
                    let right = self.parse_term()?;
                    left = match left {
                        CanonicalExpr::Add(mut terms) => {
                            terms.push(right);
                            CanonicalExpr::Add(terms)
                        }
                        other => CanonicalExpr::Add(vec![other, right]),
                    };
                }
                Token::Minus => {
                    self.next();
                    let right = self.parse_term()?;
                    let neg_right = CanonicalExpr::Neg(Box::new(right));
                    left = match left {
                        CanonicalExpr::Add(mut terms) => {
                            terms.push(neg_right);
                            CanonicalExpr::Add(terms)
                        }
                        other => CanonicalExpr::Add(vec![other, neg_right]),
                    };
                }
                _ => break,
            }
        }

        Ok(left)
    }

    fn parse_term(&mut self) -> Result<CanonicalExpr, String> {
        let mut left = self.parse_power()?;

        while let Some(tok) = self.peek() {
            match tok {
                Token::Star => {
                    self.next();
                    let right = self.parse_power()?;
                    left = match left {
                        CanonicalExpr::Mul(mut factors) => {
                            factors.push(right);
                            CanonicalExpr::Mul(factors)
                        }
                        other => CanonicalExpr::Mul(vec![other, right]),
                    };
                }
                Token::Slash => {
                    self.next();
                    let right = self.parse_power()?;
                    left = CanonicalExpr::Div(Box::new(left), Box::new(right));
                }
                Token::Ident(_) | Token::LParen => {
                    let right = self.parse_power()?;
                    left = match left {
                        CanonicalExpr::Mul(mut factors) => {
                            factors.push(right);
                            CanonicalExpr::Mul(factors)
                        }
                        other => CanonicalExpr::Mul(vec![other, right]),
                    };
                }
                _ => break,
            }
        }

        Ok(left)
    }

    fn parse_power(&mut self) -> Result<CanonicalExpr, String> {
        let base = self.parse_unary()?;

        if let Some(Token::Caret) = self.peek() {
            self.next();
            // Exponent may be negative
            let mut is_neg = false;
            if let Some(Token::Minus) = self.peek() {
                self.next();
                is_neg = true;
            }
            if let Some(Token::Number(exp, _)) = self.next() {
                let p = if is_neg { -exp } else { exp } as i32;
                return Ok(CanonicalExpr::Pow(Box::new(base), p));
            } else {
                return Err("Exponent after '^' must be an integer".to_string());
            }
        }

        Ok(base)
    }

    fn parse_unary(&mut self) -> Result<CanonicalExpr, String> {
        if let Some(Token::Minus) = self.peek() {
            self.next();
            let inner = self.parse_unary()?;
            return Ok(CanonicalExpr::Neg(Box::new(inner)));
        }
        self.parse_primary()
    }

    fn parse_primary(&mut self) -> Result<CanonicalExpr, String> {
        match self.next() {
            Some(Token::Number(n, d)) => {
                let r = Rational::new(n, d).map_err(|e| format!("{:?}", e))?;
                Ok(CanonicalExpr::Const(r))
            }
            Some(Token::Ident(name)) => {
                let id = self.symbols.get_or_register(&name);
                Ok(CanonicalExpr::Var(id))
            }
            Some(Token::LParen) => {
                let expr = self.parse_expression()?;
                match self.next() {
                    Some(Token::RParen) => Ok(expr),
                    other => Err(format!("Expected closing parenthesis ')' but found: {:?}", other)),
                }
            }
            other => Err(format!("Unexpected expression token: {:?}", other)),
        }
    }
}

/// Parse a canonical algebraic expression string
pub fn parse_expr(input: &str, symbols: &mut SymbolTable) -> Result<CanonicalExpr, String> {
    let chars: Vec<char> = input.chars().collect();
    let mut lexer = Lexer::new(&chars);
    let mut tokens = Vec::new();
    while let Some(tok) = lexer.next_token()? {
        tokens.push(tok);
    }
    if tokens.is_empty() {
        return Err("Input mathematical expression is empty".to_string());
    }
    let mut parser = ExprParser::new(tokens, symbols);
    parser.parse_expression()
}

/// Parse a two-sided equation (LHS = RHS)
pub fn parse_equation(input: &str, symbols: &mut SymbolTable) -> Result<(CanonicalExpr, CanonicalExpr), String> {
    let s = input.trim();
    let chars: Vec<char> = s.chars().collect();
    let mut lexer = Lexer::new(&chars);
    let mut tokens = Vec::new();
    while let Some(tok) = lexer.next_token()? {
        tokens.push(tok);
    }

    // Find equality symbol
    let eq_pos = tokens.iter().position(|t| matches!(t, Token::Equal));
    match eq_pos {
        Some(pos) => {
            let left_tokens = tokens[..pos].to_vec();
            let right_tokens = tokens[pos + 1..].to_vec();
            if left_tokens.is_empty() || right_tokens.is_empty() {
                return Err("Equation must contain expressions on both sides of '='".to_string());
            }
            let mut parser_l = ExprParser::new(left_tokens, symbols);
            let lhs = parser_l.parse_expression()?;
            let mut parser_r = ExprParser::new(right_tokens, symbols);
            let rhs = parser_r.parse_expression()?;
            Ok((lhs, rhs))
        }
        None => Err("No equality sign '=' found in equation".to_string()),
    }
}

/// Canonical table of standard physical quantities and their SI-7 integer exponents [L, M, T, I, Θ, N, J]
const STANDARD_PHYSICAL_DIMENSIONS: &[(&str, &[i64])] = &[
    // SI-7 Base Dimensions
    ("length", &[1, 0, 0]),
    ("distance", &[1, 0, 0]),
    ("radius", &[1, 0, 0]),
    ("mass", &[0, 1, 0]),
    ("time", &[0, 0, 1]),
    ("duration", &[0, 0, 1]),
    ("current", &[0, 0, 0, 1]),
    ("temperature", &[0, 0, 0, 0, 1]),
    ("substance", &[0, 0, 0, 0, 0, 1]),
    ("luminosity", &[0, 0, 0, 0, 0, 0, 1]),
    // Kinematics & Wave Dynamics
    ("velocity", &[1, 0, -1]),
    ("speed", &[1, 0, -1]),
    ("acceleration", &[1, 0, -2]),
    ("frequency", &[0, 0, -1]),
    ("wavenumber", &[-1, 0, 0]),
    // Dynamics & Mechanics
    ("force", &[1, 1, -2]),
    ("newton", &[1, 1, -2]),
    ("energy", &[2, 1, -2]),
    ("joule", &[2, 1, -2]),
    ("work", &[2, 1, -2]),
    ("power", &[2, 1, -3]),
    ("watt", &[2, 1, -3]),
    ("pressure", &[-1, 1, -2]),
    ("pascal", &[-1, 1, -2]),
    ("momentum", &[1, 1, -1]),
    ("angularmomentum", &[2, 1, -1]),
    ("action", &[2, 1, -1]),
    ("viscosity", &[-1, 1, -1]),
    ("frequency", &[0, 0, -1]),
    ("hertz", &[0, 0, -1]),
    ("gravitation", &[3, -1, -2]),
    ("gravity", &[3, -1, -2]),
    // Electromagnetism
    ("charge", &[0, 0, 1, 1]),
    ("coulomb", &[0, 0, 1, 1]),
    ("voltage", &[2, 1, -3, -1]),
    ("volt", &[2, 1, -3, -1]),
    ("potential", &[2, 1, -3, -1]),
    ("coulombke", &[3, 1, -4, -2]),
    // Pure Dimensionless Quantities
    ("dimensionless", &[]),
    ("scalar", &[]),
];

/// Parses a physical dimension string using a flexible, principled 3-tier hierarchy:
/// 1. Canonical physical quantity name (e.g. 'energy', 'force', 'viscosity', 'pressure')
/// 2. Direct numerical coordinate vector (e.g. '[2, 1, -2]' or '2, 1, -2')
/// 3. Compound algebraic unit / dimensional formula (e.g. 'L^2 * M * T^-2', 'N/m^2', 'kg*m/s^2', 'J*s')
pub fn parse_dimension_str(input: &str) -> Result<DimensionVector, String> {
    let s = input.trim();
    if s.is_empty() {
        return Ok(DimensionVector::dimensionless());
    }

    // 1. Table-driven lookup for canonical physical names
    let norm = s.to_lowercase().replace(['_', '-', ' '], "");
    if let Some(&(_, coords)) = STANDARD_PHYSICAL_DIMENSIONS
        .iter()
        .find(|&&(name, _)| name == norm.as_str())
    {
        return Ok(DimensionVector::from_integers(coords));
    }

    // 2. Numerical coordinate vector: [c0, c1, c2, ...]
    let stripped = s.trim_start_matches('[').trim_end_matches(']');
    if stripped.contains(',') || stripped.split_whitespace().count() > 1 {
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

    // 3. Algebraic dimensional expression evaluation: e.g. "L^2 * M / T^2", "N/m^2", "kg*m/s^2"
    parse_dimensional_algebraic_expr(s)
}

/// Evaluates an algebraic dimensional expression (e.g. L^2 * M * T^-2 or L^3 / (M * T^2))
fn parse_dimensional_algebraic_expr(input: &str) -> Result<DimensionVector, String> {
    let mut symbols = SymbolTable::new();
    let ast = parse_expr(input, &mut symbols)?;
    eval_dim_ast(&ast, &symbols)
}

fn eval_dim_ast(expr: &CanonicalExpr, symbols: &SymbolTable) -> Result<DimensionVector, String> {
    match expr {
        CanonicalExpr::Const(_) => Ok(DimensionVector::dimensionless()),
        CanonicalExpr::Var(id) => {
            let orig = symbols.get_name(*id).unwrap_or("");
            // Handle case-sensitive single-letter conventions
            if orig == "m" {
                // Lowercase 'm' in unit expressions is meter (Length [1, 0, 0])
                return Ok(DimensionVector::unit_basis(0, 7));
            }
            if orig == "M" {
                // Uppercase 'M' in dimensional analysis is Mass [0, 1, 0]
                return Ok(DimensionVector::unit_basis(1, 7));
            }

            let upper = orig.to_uppercase();
            match upper.as_str() {
                // Base SI Dimensions and Units
                "L" | "METER" | "METRE" | "LENGTH" => Ok(DimensionVector::unit_basis(0, 7)),
                "KG" | "KILOGRAM" | "MASS" => Ok(DimensionVector::unit_basis(1, 7)),
                "T" | "S" | "SEC" | "SECOND" | "TIME" => Ok(DimensionVector::unit_basis(2, 7)),
                "I" | "A" | "AMP" | "AMPERE" | "CURRENT" => Ok(DimensionVector::unit_basis(3, 7)),
                "THETA" | "Θ" | "K" | "KELVIN" | "TEMPERATURE" => Ok(DimensionVector::unit_basis(4, 7)),
                "MOL" | "MOLE" | "SUBSTANCE" => Ok(DimensionVector::unit_basis(5, 7)),
                "CD" | "CANDELA" | "LUMINOSITY" => Ok(DimensionVector::unit_basis(6, 7)),
                // Derived SI Units and Standards
                "N" | "NEWTON" | "FORCE" => Ok(DimensionVector::from_integers(&[1, 1, -2])),
                "J" | "JOULE" | "ENERGY" => Ok(DimensionVector::from_integers(&[2, 1, -2])),
                "PASCAL" | "PA" | "PRESSURE" => Ok(DimensionVector::from_integers(&[-1, 1, -2])),
                "WATT" | "W" | "POWER" => Ok(DimensionVector::from_integers(&[2, 1, -3])),
                "HERTZ" | "HZ" | "FREQUENCY" => Ok(DimensionVector::from_integers(&[0, 0, -1])),
                "COULOMB" | "C" | "CHARGE" => Ok(DimensionVector::from_integers(&[0, 0, 1, 1])),
                "VOLT" | "V" | "VOLTAGE" => Ok(DimensionVector::from_integers(&[2, 1, -3, -1])),
                other => {
                    if let Some(num_str) = other.strip_prefix('D') {
                        if let Ok(idx) = num_str.parse::<usize>() {
                            let total = (idx + 1).max(7);
                            return Ok(DimensionVector::unit_basis(idx, total));
                        }
                    }
                    Err(format!(
                        "Unknown dimensional base symbol or derived unit: '{}'. Expected base dimensions (L, M, T, I, Theta, Mol, Cd, D0..D9) or standard derived units (N, J, Pa, W, Hz, V, C).",
                        other
                    ))
                }
            }
        }
        CanonicalExpr::Mul(factors) => {
            let mut sum = DimensionVector::dimensionless();
            for f in factors {
                sum = sum + eval_dim_ast(f, symbols)?;
            }
            Ok(sum)
        }
        CanonicalExpr::Div(num, den) => {
            let d_num = eval_dim_ast(num, symbols)?;
            let d_den = eval_dim_ast(den, symbols)?;
            Ok(d_num - d_den)
        }
        CanonicalExpr::Pow(base, p) => {
            let d_base = eval_dim_ast(base, symbols)?;
            Ok(scale_dimension_vector(&d_base, *p as i64))
        }
        CanonicalExpr::Neg(base) => {
            let d = eval_dim_ast(base, symbols)?;
            Ok(scale_dimension_vector(&d, -1))
        }
        CanonicalExpr::Add(terms) => {
            if terms.is_empty() {
                return Ok(DimensionVector::dimensionless());
            }
            let first = eval_dim_ast(&terms[0], symbols)?;
            for t in &terms[1..] {
                let d = eval_dim_ast(t, symbols)?;
                if d != first {
                    return Err("Additive terms in dimensional formula are not dimensionally homogeneous".to_string());
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
            '[' | '(' => {
                depth += 1;
                current.push(ch);
            }
            ']' | ')' => {
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
/// Format: "E:energy, m:mass" or "F:force, m1:mass, m2:mass, r:length"
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
            return Err(format!("Invalid variable binding syntax '{}'. Expected 'variable:dimension'", trimmed));
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
/// Format: "c, G, hbar" or "c, custom:[1, 0, -1]"
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
                return Err(format!("Invalid candidate base syntax '{}'", trimmed));
            }
            let name = parts[0].trim().to_string();
            let dim = parse_dimension_str(parts[1].trim())?;
            result.push((name, dim));
            continue;
        }

        let norm = trimmed.to_lowercase().replace(['_', '-', ' '], "");
        match norm.as_str() {
            "c" | "velocity" | "speedoflight" => {
                result.push(("c (Speed of Light)".to_string(), DimensionVector::from_integers(&[1, 0, -1])));
            }
            "g" | "gravitation" | "gravitationalconstant" => {
                result.push(("G (Gravitational Constant)".to_string(), DimensionVector::from_integers(&[3, -1, -2])));
            }
            "hbar" | "ħ" => {
                result.push(("ħ (Reduced Planck Constant)".to_string(), DimensionVector::from_integers(&[2, 1, -1])));
            }
            "h" | "planck" => {
                result.push(("h (Planck Constant)".to_string(), DimensionVector::from_integers(&[2, 1, -1])));
            }
            "ke" | "coulomb" => {
                result.push(("k_e (Coulomb Constant)".to_string(), DimensionVector::from_integers(&[3, 1, -4, -2])));
            }
            "kb" | "boltzmann" => {
                result.push(("k_B (Boltzmann Constant)".to_string(), DimensionVector::from_integers(&[2, 1, -2, 0, -1])));
            }
            "mu0" => {
                result.push(("μ_0 (Vacuum Permeability)".to_string(), DimensionVector::from_integers(&[1, 1, -2, -2])));
            }
            "eps0" => {
                result.push(("ε_0 (Vacuum Permittivity)".to_string(), DimensionVector::from_integers(&[-3, -1, 4, 2])));
            }
            other => {
                return Err(format!("Unknown physical constant '{}'. Expected standard constants (c, G, hbar, ke, kB) or custom format 'name:dim_expr'", other));
            }
        }
    }

    Ok(result)
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
    fn test_parse_equation_einstein() {
        let mut symbols = SymbolTable::new();
        let (lhs, rhs) = parse_equation("E = m", &mut symbols).unwrap();
        assert!(matches!(lhs, CanonicalExpr::Var(_)));
        assert!(matches!(rhs, CanonicalExpr::Var(_)));
        assert_eq!(symbols.get_name(VariableId(1)), Some("E"));
        assert_eq!(symbols.get_name(VariableId(2)), Some("m"));
    }

    #[test]
    fn test_parse_equation_newton_gravity() {
        let mut symbols = SymbolTable::new();
        let (lhs, rhs) = parse_equation("F = (m1 * m2) / r^2", &mut symbols).unwrap();
        assert!(matches!(lhs, CanonicalExpr::Var(_)));
        assert!(matches!(rhs, CanonicalExpr::Div(_, _)));
    }

    #[test]
    fn test_parse_dimension_named_and_algebraic() {
        let dim_e1 = parse_dimension_str("energy").unwrap();
        let dim_e2 = parse_dimension_str("L^2 * M * T^-2").unwrap();
        let dim_e3 = parse_dimension_str("[2, 1, -2]").unwrap();
        assert_eq!(dim_e1, dim_e2);
        assert_eq!(dim_e1, dim_e3);

        let dim_v1 = parse_dimension_str("velocity").unwrap();
        let dim_v2 = parse_dimension_str("L / T").unwrap();
        assert_eq!(dim_v1, dim_v2);

        let dim_g1 = parse_dimension_str("gravity").unwrap();
        let dim_g2 = parse_dimension_str("L^3 / (M * T^2)").unwrap();
        assert_eq!(dim_g1, dim_g2);
    }

    #[test]
    fn test_parse_variable_bindings_and_candidates() {
        let mut symbols = SymbolTable::new();
        let bindings = parse_variable_bindings("E:energy, m:mass", &mut symbols).unwrap();
        assert_eq!(bindings.len(), 2);

        let candidates = parse_candidate_bases("c, G, hbar").unwrap();
        assert_eq!(candidates.len(), 3);
        assert_eq!(candidates[0].0, "c (Speed of Light)");
        assert_eq!(candidates[1].0, "G (Gravitational Constant)");
        assert_eq!(candidates[2].0, "ħ (Reduced Planck Constant)");
    }
}
