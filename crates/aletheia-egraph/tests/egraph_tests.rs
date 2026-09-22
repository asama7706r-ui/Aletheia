use aletheia_algebra::{CanonicalExpr, VariableId};
use aletheia_egraph::*;
use aletheia_lattice::{DimensionRegistry, DimensionalContext, LatticeError};

#[test]
fn test_hashcons_and_commutative_sorting() {
    let mut egraph = TransactionalEGraph::new();
    let ctx = DimensionalContext::mathematical();

    let x0 = VariableId(0);
    let x1 = VariableId(1);

    // 1. التعبير الأول: x0 + x1
    let expr1 = CanonicalExpr::Add(vec![CanonicalExpr::Var(x0), CanonicalExpr::Var(x1)]);
    let id1 = egraph.add_expr(&expr1, &ctx).unwrap();

    // 2. التعبير الثاني بالترتيب المعكوس: x1 + x0
    let expr2 = CanonicalExpr::Add(vec![CanonicalExpr::Var(x1), CanonicalExpr::Var(x0)]);
    let id2 = egraph.add_expr(&expr2, &ctx).unwrap();

    // الفرز الكنسي للعمليات التبادلية يضمن تطابق الفئتين فورياً في جدول الـ Hash-Cons
    assert_eq!(id1, id2);

    // 3. المشاركة الهيكلية القصوى (Maximum Structural Sharing): (x0 + x1) * (x1 + x0)
    let expr_prod = CanonicalExpr::Mul(vec![expr1, expr2]);
    let id_prod = egraph.add_expr(&expr_prod, &ctx).unwrap();
    assert_ne!(id_prod, id1);

    // التحقق من أن عقدي الضرب يشيران لنفس فئة الجمع
    let prod_class = egraph.classes.get(&egraph.find(id_prod)).unwrap();
    assert_eq!(prod_class.nodes.len(), 1);
    match &prod_class.nodes[0] {
        ENode::Mul(ops) => {
            assert_eq!(ops.len(), 2);
            assert_eq!(ops[0], id1);
            assert_eq!(ops[1], id1);
        }
        _ => panic!("Expected Mul node"),
    }
}

#[test]
fn test_atomic_rollback() {
    let mut egraph = TransactionalEGraph::new();
    let ctx = DimensionalContext::mathematical();

    let x0 = VariableId(0);
    let id_x0 = egraph
        .add_expr(&CanonicalExpr::Var(x0), &ctx)
        .unwrap();

    // أخذ نقطة تفتيش
    let initial_classes = egraph.class_count();
    let initial_nodes = egraph.node_count();
    let checkpoint = egraph.checkpoint();

    // طرح فرضيات مضاربية وإضافة عقد جديدة
    let x1 = VariableId(1);
    let id_x1 = egraph
        .add_expr(&CanonicalExpr::Var(x1), &ctx)
        .unwrap();
    assert_ne!(id_x0, id_x1);

    egraph.union(id_x0, id_x1).unwrap();
    egraph.rebuild().unwrap();

    // بعد الدمج، أصبحا متكافئين
    assert_eq!(egraph.find(id_x0), egraph.find(id_x1));
    assert!(egraph.class_count() > initial_classes);

    // التراجع الذري اللحظي التام (Bit-Exact Rollback)
    egraph.rollback(checkpoint);

    // التحقق من عودة الذاكرة لنفس الحالة الأولى 100%
    assert_eq!(egraph.class_count(), initial_classes);
    assert_eq!(egraph.node_count(), initial_nodes);
    assert_eq!(egraph.find(id_x0), id_x0);
    assert!(!egraph.classes.contains_key(&id_x1));
}

#[test]
fn test_raii_transaction_auto_rollback() {
    let mut egraph = TransactionalEGraph::new();
    let ctx = DimensionalContext::mathematical();

    let x0 = VariableId(0);
    let id_x0 = egraph.add_expr(&CanonicalExpr::Var(x0), &ctx).unwrap();
    let initial_classes = egraph.class_count();

    // فتح معاملة ذرية تنهار عند نهاية النطاق دون commit
    {
        let mut tx = egraph.transaction();
        let x1 = VariableId(1);
        let id_x1 = tx.add_expr(&CanonicalExpr::Var(x1), &ctx).unwrap();
        tx.union(id_x0, id_x1).unwrap();
        tx.rebuild().unwrap();
        assert_eq!(tx.find(id_x0), tx.find(id_x1));
        // نخرج دون استدعاء tx.commit()
    }

    // تم التراجع التلقائي بنسبة 100%
    assert_eq!(egraph.class_count(), initial_classes);
    assert_eq!(egraph.find(id_x0), id_x0);
}

#[test]
fn test_raii_transaction_commit() {
    let mut egraph = TransactionalEGraph::new();
    let ctx = DimensionalContext::mathematical();

    let x0 = VariableId(0);
    let id_x0 = egraph.add_expr(&CanonicalExpr::Var(x0), &ctx).unwrap();

    // فتح معاملة وتثبيتها صراحة
    let x1 = VariableId(1);
    let mut tx = egraph.transaction();
    let id_x1 = tx.add_expr(&CanonicalExpr::Var(x1), &ctx).unwrap();
    tx.union(id_x0, id_x1).unwrap();
    tx.rebuild().unwrap();
    tx.commit();

    // بقاء التغييرات واعتمادها كحقيقة كنسية
    assert_eq!(egraph.find(id_x0), egraph.find(id_x1));
    assert_eq!(egraph.class_count(), 2);
}

#[test]
fn test_congruence_closure_rebuild() {
    let mut egraph = TransactionalEGraph::new();
    let ctx = DimensionalContext::mathematical();

    let x0 = VariableId(0);
    let x1 = VariableId(1);

    // a = x0, b = x1
    let id_a = egraph.add_expr(&CanonicalExpr::Var(x0), &ctx).unwrap();
    let id_b = egraph.add_expr(&CanonicalExpr::Var(x1), &ctx).unwrap();

    // f(a) = a^2
    let expr_fa = CanonicalExpr::Pow(Box::new(CanonicalExpr::Var(x0)), 2);
    let id_fa = egraph.add_expr(&expr_fa, &ctx).unwrap();

    // f(b) = b^2
    let expr_fb = CanonicalExpr::Pow(Box::new(CanonicalExpr::Var(x1)), 2);
    let id_fb = egraph.add_expr(&expr_fb, &ctx).unwrap();

    assert_ne!(egraph.find(id_fa), egraph.find(id_fb));

    // دمج a ~ b وتشغيل دورة إغلاق التطابق (rebuild)
    egraph.union(id_a, id_b).unwrap();
    let propagated = egraph.rebuild().unwrap();

    // بديهية إغلاق التطابق تفرض: a ~ b => f(a) ~ f(b)
    assert!(propagated > 0);
    assert_eq!(egraph.find(id_fa), egraph.find(id_fb));
}

#[test]
fn test_lattice_dimensional_contradiction_rollback() {
    let reg = DimensionRegistry::new();
    let mut ctx = DimensionalContext::new();

    let x0 = VariableId(0); // مسافة r [L]
    let x1 = VariableId(1); // زمن t [T]

    ctx.bind(x0, reg.length());
    ctx.bind(x1, reg.time());

    let mut egraph = TransactionalEGraph::new();
    let id_r = egraph.add_expr(&CanonicalExpr::Var(x0), &ctx).unwrap();
    let id_t = egraph.add_expr(&CanonicalExpr::Var(x1), &ctx).unwrap();

    let checkpoint = egraph.checkpoint();

    // محاولة دمج فرضية شاذة: المسافة تكافئ الزمن r ~ t
    let union_res = egraph.union(id_r, id_t);

    // يجب أن تفشل فورياً برفض دمج الأبعاد المتعارضة
    assert!(matches!(
        union_res,
        Err(EGraphError::Lattice(LatticeError::ContradictoryMerge(_)))
    ));

    // التراجع الفوري لإبقاء الذاكرة نقية
    egraph.rollback(checkpoint);
    assert_eq!(egraph.find(id_r), id_r);
    assert_eq!(egraph.find(id_t), id_t);
}

#[test]
fn test_division_denominator_congruence_closure() {
    let mut egraph = TransactionalEGraph::new();
    let ctx = DimensionalContext::mathematical();

    let a = VariableId(0);
    let b = VariableId(1);
    let b_prime = VariableId(2);

    // a / b
    let expr_div1 = CanonicalExpr::Div(
        Box::new(CanonicalExpr::Var(a)),
        Box::new(CanonicalExpr::Var(b)),
    );
    let id_div1 = egraph.add_expr(&expr_div1, &ctx).unwrap();

    // a / b'
    let expr_div2 = CanonicalExpr::Div(
        Box::new(CanonicalExpr::Var(a)),
        Box::new(CanonicalExpr::Var(b_prime)),
    );
    let id_div2 = egraph.add_expr(&expr_div2, &ctx).unwrap();

    let id_b = egraph.add_expr(&CanonicalExpr::Var(b), &ctx).unwrap();
    let id_b_prime = egraph.add_expr(&CanonicalExpr::Var(b_prime), &ctx).unwrap();

    assert_ne!(egraph.find(id_div1), egraph.find(id_div2));

    // دمج المقامين: b ~ b'
    egraph.union(id_b, id_b_prime).unwrap();
    let propagated = egraph.rebuild().unwrap();

    // التحقق من أن المقام مسجل في قائمة الآباء parents وأن rebuild وحد a/b مع a/b' تلقائياً
    assert!(propagated > 0);
    assert_eq!(egraph.find(id_div1), egraph.find(id_div2));
}

#[test]
fn test_subexpression_lattice_data_protection() {
    let reg = DimensionRegistry::new();
    let mut ctx = DimensionalContext::new();

    let x = VariableId(0); // مسافة x [L]
    let y = VariableId(1); // مسافة y [L]
    let t = VariableId(2); // زمن t [T]

    ctx.bind(x, reg.length());
    ctx.bind(y, reg.length());
    ctx.bind(t, reg.time());

    let mut egraph = TransactionalEGraph::new();

    // تعبير مركب: (x + y) / t  [سرعة: L T^-1]
    let expr = CanonicalExpr::Div(
        Box::new(CanonicalExpr::Add(vec![
            CanonicalExpr::Var(x),
            CanonicalExpr::Var(y),
        ])),
        Box::new(CanonicalExpr::Var(t)),
    );

    let id_div = egraph.add_expr(&expr, &ctx).unwrap();

    // استخراج فئات التكافؤ للمتغيرات الفرعية
    let id_x = egraph.add_expr(&CanonicalExpr::Var(x), &ctx).unwrap();
    let id_y = egraph.add_expr(&CanonicalExpr::Var(y), &ctx).unwrap();
    let id_t = egraph.add_expr(&CanonicalExpr::Var(t), &ctx).unwrap();

    // التحقق من أن المتغيرات الفرعية تمتلك LatticeData بأبعادها الصحيحة
    let x_class = egraph.classes.get(&egraph.find(id_x)).unwrap();
    assert_eq!(x_class.data.as_ref().unwrap().dim, reg.length());

    let y_class = egraph.classes.get(&egraph.find(id_y)).unwrap();
    assert_eq!(y_class.data.as_ref().unwrap().dim, reg.length());

    let t_class = egraph.classes.get(&egraph.find(id_t)).unwrap();
    assert_eq!(t_class.data.as_ref().unwrap().dim, reg.time());

    // التعبير الكلي له بُعد السرعة [L * T^-1]
    let div_class = egraph.classes.get(&egraph.find(id_div)).unwrap();
    let expected_speed_dim = reg.length() - reg.time();
    assert_eq!(div_class.data.as_ref().unwrap().dim, expected_speed_dim);

    // محاولة دمج غير شرعية بين فرعين فرعيين متعارضين بُعدياً: x ~ t
    let union_res = egraph.union(id_x, id_t);
    assert!(matches!(
        union_res,
        Err(EGraphError::Lattice(LatticeError::ContradictoryMerge(_)))
    ));
}
