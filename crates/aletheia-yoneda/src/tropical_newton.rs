use crate::error::YonedaError;
use aletheia_algebra::{Polynomial, Rational, VariableId};

/// نقطة في المستوى الاستوائي لمضلع نيوتن بإحداثيات كسرية دقيقة في Q
/// مناعة كاملة ضد الانجراف العائم: لا وجود لأي f32 أو f64 إطلاقاً
#[derive(Clone, Debug, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub struct NewtonPoint {
    pub x: Rational,
    pub y: Rational,
}

impl NewtonPoint {
    #[inline]
    pub fn new(x: Rational, y: Rational) -> Self {
        Self { x, y }
    }

    #[inline]
    pub fn from_integers(x: i64, y: i64) -> Self {
        Self {
            x: Rational::from_i64(x),
            y: Rational::from_i64(y),
        }
    }
}

/// ضلع في مضلع نيوتن مع ميله الدقيق في Q
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct NewtonEdge {
    pub p1: NewtonPoint,
    pub p2: NewtonPoint,
    /// ميل الضلع: Delta y / Delta x
    pub slope: Rational,
    /// أس التوازن البويزي (Puiseux balancing exponent): - Delta x / Delta y
    pub puiseux_exponent: Option<Rational>,
}

/// مضلع نيوتن الاستوائي (Tropical Newton Polygon)
/// يحسب الغلاف المحدب والأضلاع الحاكمة للسلوك التقاربي دون أي أخطاء تقريبية
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct NewtonPolygon {
    /// النقاط الأصلية المدخلة
    pub points: Vec<NewtonPoint>,
    /// رؤوس الغلاف المحدب مرتبة عكس عقارب الساعة
    pub hull_vertices: Vec<NewtonPoint>,
    /// رؤوس الغلاف السفلي (Lower Hull) الحاكمة للمجال التقاربي عند الصفر x -> 0
    pub lower_hull: Vec<NewtonPoint>,
    /// رؤوس الغلاف العلوي (Upper Hull) الحاكمة للمجال التقاربي عند اللانهاية x -> inf
    pub upper_hull: Vec<NewtonPoint>,
    /// أضلاع الغلاف المحدب وميولها
    pub edges: Vec<NewtonEdge>,
}

impl NewtonPolygon {
    /// بناء مضلع نيوتن من مجموعة نقاط كسرية في Q^2
    pub fn from_points(mut points: Vec<NewtonPoint>) -> Result<Self, YonedaError> {
        if points.is_empty() {
            return Err(YonedaError::TropicalNewtonError(
                "لا يمكن بناء مضلع نيوتن من مجموعة نقاط فارغة".into(),
            ));
        }

        // فرز كنسي وإزالة التكرارات
        points.sort();
        points.dedup();

        let (lower_hull, upper_hull, hull_vertices) = Self::compute_convex_hull(&points);
        let edges = Self::compute_edges(&hull_vertices);

        Ok(Self {
            points,
            hull_vertices,
            lower_hull,
            upper_hull,
            edges,
        })
    }

    /// استخراج مضلع نيوتن مباشرة من كثير حدود بمتغيرين (x, y) من حزمة aletheia-algebra
    pub fn from_polynomial(
        poly: &Polynomial,
        var_x: VariableId,
        var_y: VariableId,
    ) -> Result<Self, YonedaError> {
        if poly.is_zero() {
            return Err(YonedaError::TropicalNewtonError(
                "كثير الحدود الصفري ليس له مضلع نيوتن معرف".into(),
            ));
        }

        let mut points = Vec::new();
        for term in poly.terms() {
            let mut deg_x = 0u32;
            let mut deg_y = 0u32;
            for &(var, pow) in term.monomial.factors() {
                if var == var_x {
                    deg_x += pow;
                } else if var == var_y {
                    deg_y += pow;
                }
            }
            points.push(NewtonPoint::from_integers(deg_x as i64, deg_y as i64));
        }

        Self::from_points(points)
    }

    /// حساب الضرب الاتجاهي ثنائي الأبعاد (2D Cross Product) الصرف في Q
    /// يحدد اتجاه الدوران (Orientation Test) بين ثلاث نقاط
    /// موجب: دوران عكس عقارب الساعة (Left Turn)
    /// سالب: دوران مع عقارب الساعة (Right Turn)
    /// صفر: نقاط على استقامة واحدة (Collinear)
    #[inline]
    pub fn cross_product(p1: &NewtonPoint, p2: &NewtonPoint, p3: &NewtonPoint) -> Rational {
        let dx1 = &p2.x - &p1.x;
        let dy1 = &p2.y - &p1.y;
        let dx2 = &p3.x - &p1.x;
        let dy2 = &p3.y - &p1.y;
        (dx1 * dy2) - (dy1 * dx2)
    }

    /// خوارزمية السلسلة الرتيبة لأندرو (Andrew's Monotone Chain) لحساب الغلاف المحدب في O(n log n)
    /// تعمل بدقة مطلقة فوق حقل الأعداد النسبية Q ودون أي تحويل لفاصلة عائمة
    fn compute_convex_hull(
        sorted_points: &[NewtonPoint],
    ) -> (Vec<NewtonPoint>, Vec<NewtonPoint>, Vec<NewtonPoint>) {
        let n = sorted_points.len();
        if n <= 2 {
            return (
                sorted_points.to_vec(),
                sorted_points.to_vec(),
                sorted_points.to_vec(),
            );
        }

        // 1. حساب الغلاف السفلي (Lower Hull)
        let mut lower: Vec<NewtonPoint> = Vec::with_capacity(n);
        for p in sorted_points {
            while lower.len() >= 2 {
                let p1 = &lower[lower.len() - 2];
                let p2 = &lower[lower.len() - 1];
                // إذا كان الدوران مع عقارب الساعة أو على استقامة واحدة، احذف النقطة السابقة
                if Self::cross_product(p1, p2, p) <= Rational::zero() {
                    lower.pop();
                } else {
                    break;
                }
            }
            lower.push(p.clone());
        }

        // 2. حساب الغلاف العلوي (Upper Hull)
        let mut upper: Vec<NewtonPoint> = Vec::with_capacity(n);
        for p in sorted_points.iter().rev() {
            while upper.len() >= 2 {
                let p1 = &upper[upper.len() - 2];
                let p2 = &upper[upper.len() - 1];
                if Self::cross_product(p1, p2, p) <= Rational::zero() {
                    upper.pop();
                } else {
                    break;
                }
            }
            upper.push(p.clone());
        }

        // دمج الغلافين لتكوين المضلع الكامل عكس عقارب الساعة
        let mut full_hull = lower.clone();
        full_hull.pop(); // حذف النقطة الأخيرة لمنع التكرار مع بداية الغلاف العلوي
        for p in &upper[..upper.len() - 1] {
            full_hull.push(p.clone());
        }

        (lower, upper, full_hull)
    }

    /// حساب أضلاع الغلاف المحدب وميولها
    fn compute_edges(vertices: &[NewtonPoint]) -> Vec<NewtonEdge> {
        let n = vertices.len();
        if n < 2 {
            return Vec::new();
        }

        let mut edges = Vec::with_capacity(n);
        for i in 0..n {
            let p1 = &vertices[i];
            let p2 = &vertices[(i + 1) % n];

            let dx = &p2.x - &p1.x;
            let dy = &p2.y - &p1.y;

            let slope = if dx.is_zero() {
                // ضلع رأسي
                Rational::zero()
            } else {
                &dy / &dx
            };

            let puiseux_exponent = if dy.is_zero() {
                None
            } else {
                Some(-(&dx / &dy))
            };

            edges.push(NewtonEdge {
                p1: p1.clone(),
                p2: p2.clone(),
                slope,
                puiseux_exponent,
            });
        }
        edges
    }

    /// استخراج أضلاع الغلاف السفلي وميولها الحاكمة للسلوك التقاربي عند الصفر x -> 0
    pub fn lower_hull_slopes(&self) -> Vec<Rational> {
        let mut slopes = Vec::new();
        for i in 0..self.lower_hull.len().saturating_sub(1) {
            let p1 = &self.lower_hull[i];
            let p2 = &self.lower_hull[i + 1];
            let dx = &p2.x - &p1.x;
            let dy = &p2.y - &p1.y;
            if !dx.is_zero() {
                slopes.push(dy / dx);
            }
        }
        slopes
    }

    /// استخراج الأسس التقاربية المقترحة لنشر بويزو (Puiseux Asymptotic Exponents)
    pub fn candidate_puiseux_exponents(&self) -> Vec<Rational> {
        let mut exponents = Vec::new();
        for i in 0..self.lower_hull.len().saturating_sub(1) {
            let p1 = &self.lower_hull[i];
            let p2 = &self.lower_hull[i + 1];
            let dx = &p2.x - &p1.x;
            let dy = &p2.y - &p1.y;
            if !dy.is_zero() {
                exponents.push(-(&dx / &dy));
            }
        }
        exponents
    }
}
