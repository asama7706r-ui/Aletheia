use crate::pattern::{Pattern, Subst};
use aletheia_egraph::{EClassId, ENode, TransactionalEGraph};
use smallvec::SmallVec;
use std::collections::HashSet;

/// مكرر القفز الهرمي (Leapfrog Iterator)
/// يتيح التحرك اللحظي O(log N) عبر البحث الثنائي (Seek) لتجاوز آلاف العناصر دون فحصها
pub struct LeapfrogSliceIterator<'a> {
    slice: &'a [EClassId],
    idx: usize,
}

impl<'a> LeapfrogSliceIterator<'a> {
    pub fn new(slice: &'a [EClassId]) -> Self {
        Self { slice, idx: 0 }
    }

    #[inline]
    pub fn at_end(&self) -> bool {
        self.idx >= self.slice.len()
    }

    #[inline]
    pub fn key(&self) -> EClassId {
        self.slice[self.idx]
    }

    #[inline]
    pub fn next(&mut self) {
        self.idx += 1;
    }

    /// قفز فوري إلى أول عنصر أكبر من أو يساوي target بواسطة البحث الثنائي
    pub fn seek(&mut self, target: EClassId) {
        if self.at_end() {
            return;
        }
        let remaining = &self.slice[self.idx..];
        match remaining.binary_search(&target) {
            Ok(found_idx) => {
                self.idx += found_idx;
            }
            Err(insert_idx) => {
                self.idx += insert_idx;
            }
        }
    }
}

/// خوارزمية Leapfrog Triejoin لتقاطع قوائم متعددة بأدنى تعقيد نظري (Worst-Case Optimal / AGM Bound)
/// تنتج التطابقات مباشرة عبر تدفق خطي دون استهلاك أي ذاكرة مؤقتة للجداول الوسيطة
pub fn leapfrog_intersect(lists: &[&[EClassId]]) -> Vec<EClassId> {
    if lists.is_empty() {
        return Vec::new();
    }
    for l in lists {
        if l.is_empty() {
            return Vec::new();
        }
    }

    let mut iters: Vec<LeapfrogSliceIterator> =
        lists.iter().map(|l| LeapfrogSliceIterator::new(l)).collect();
    let mut results = Vec::new();
    let k = iters.len();

    let mut p = 0;
    let mut max_key = iters.iter().map(|it| it.key()).max().unwrap();
    let mut match_count = 0;

    while !iters[p].at_end() {
        let cur_key = iters[p].key();
        if cur_key < max_key {
            iters[p].seek(max_key);
            if iters[p].at_end() {
                break;
            }
            let new_key = iters[p].key();
            if new_key > max_key {
                max_key = new_key;
                match_count = 1;
            } else if new_key == max_key {
                match_count += 1;
            }
        } else if cur_key == max_key {
            match_count += 1;
        }

        if match_count == k {
            results.push(max_key);
            match_count = 0;
            iters[p].next();
            if iters[p].at_end() {
                break;
            }
            max_key = iters[p].key();
        }

        p = (p + 1) % k;
    }

    results
}

/// نوع العملية التجميعية في الـ E-Graph
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ENodeKind {
    Add,
    Mul,
}

/// نتيجة تطابق ناجحة لنمط: جذر فئة التكافؤ، جدول التعويضات، وسياق المعاملات المتبقية لـ N-ary
#[derive(Clone, Debug)]
pub struct MatchResult {
    pub root: EClassId,
    pub subst: Subst,
    /// إذا كانت المطابقة لاختزال زوج فرعي داخل عقدة متعددة المعاملات (N-Ary Arity Reduction)،
    /// يحمل هذا الحقل نوع العملية والمعاملات المتبقية لإعادة بناء السياق (Context Reconstruction)
    pub n_ary_context: Option<(ENodeKind, SmallVec<[EClassId; 2]>)>,
}

/// فهرس العلاقات العلائقي في الـ E-Graph للبحث السريع وتفعيل تقاطع Leapfrog
pub struct RelationalTrieIndex {
    pub add_roots: Vec<EClassId>,
    pub mul_roots: Vec<EClassId>,
    pub div_roots: Vec<EClassId>,
    pub pow_roots: Vec<EClassId>,
    pub neg_roots: Vec<EClassId>,
    pub const_roots: Vec<EClassId>,
    pub var_roots: Vec<EClassId>,
}

impl RelationalTrieIndex {
    pub fn build(egraph: &TransactionalEGraph) -> Self {
        let mut add_roots = Vec::new();
        let mut mul_roots = Vec::new();
        let mut div_roots = Vec::new();
        let mut pow_roots = Vec::new();
        let mut neg_roots = Vec::new();
        let mut const_roots = Vec::new();
        let mut var_roots = Vec::new();

        for (&cid, class) in &egraph.classes {
            let canon = egraph.find(cid);
            for node in &class.nodes {
                match node {
                    ENode::Add(_) => add_roots.push(canon),
                    ENode::Mul(_) => mul_roots.push(canon),
                    ENode::Div(_) => div_roots.push(canon),
                    ENode::Pow(_, _) => pow_roots.push(canon),
                    ENode::Neg(_) => neg_roots.push(canon),
                    ENode::Const(_) => const_roots.push(canon),
                    ENode::Var(_) => var_roots.push(canon),
                    _ => {}
                }
            }
        }

        let sort_dedup = |v: &mut Vec<EClassId>| {
            v.sort_unstable();
            v.dedup();
        };

        sort_dedup(&mut add_roots);
        sort_dedup(&mut mul_roots);
        sort_dedup(&mut div_roots);
        sort_dedup(&mut pow_roots);
        sort_dedup(&mut neg_roots);
        sort_dedup(&mut const_roots);
        sort_dedup(&mut var_roots);

        Self {
            add_roots,
            mul_roots,
            div_roots,
            pow_roots,
            neg_roots,
            const_roots,
            var_roots,
        }
    }

    pub fn op_roots(&self, pattern: &Pattern) -> Option<&[EClassId]> {
        match pattern {
            Pattern::Add(_) => Some(&self.add_roots),
            Pattern::Mul(_) => Some(&self.mul_roots),
            Pattern::Div(_, _) => Some(&self.div_roots),
            Pattern::Pow(_, _) => Some(&self.pow_roots),
            Pattern::Neg(_) => Some(&self.neg_roots),
            Pattern::Const(_) => Some(&self.const_roots),
            Pattern::LiteralVar(_) => Some(&self.var_roots),
            Pattern::Wildcard(_) => None,
        }
    }
}

/// محرك المطابقة العلائقية المجمعة (Compiled Relational E-Matching Engine)
pub struct RelationalMatcher;

impl RelationalMatcher {
    /// مطابقة نمط Pattern عبر الـ E-Graph بالاعتماد الفعلي على خوارزمية Leapfrog Triejoin
    /// لتقاطع الفئات النشطة dirty_classes مع فهارس العلاقات العلائقية
    pub fn find_matches(
        egraph: &TransactionalEGraph,
        pattern: &Pattern,
        dirty_classes: Option<&HashSet<EClassId>>,
    ) -> Vec<MatchResult> {
        let mut matches = Vec::new();
        let index = RelationalTrieIndex::build(egraph);

        // تقاطع الفئات النشطة dirty_classes مع فئات المؤثرات باستخدام leapfrog_intersect
        let candidate_roots: Vec<EClassId> = match (dirty_classes, index.op_roots(pattern)) {
            (Some(dirty), Some(op_roots)) => {
                let mut sorted_dirty: Vec<EClassId> = dirty.iter().copied().collect();
                sorted_dirty.sort_unstable();
                sorted_dirty.dedup();
                leapfrog_intersect(&[&sorted_dirty, op_roots])
            }
            (Some(dirty), None) => {
                let mut sorted_dirty: Vec<EClassId> = dirty.iter().copied().collect();
                sorted_dirty.sort_unstable();
                sorted_dirty.dedup();
                sorted_dirty
            }
            (None, Some(op_roots)) => op_roots.to_vec(),
            (None, None) => {
                let mut all: Vec<EClassId> = egraph.class_ids().collect();
                all.sort_unstable();
                all.dedup();
                all
            }
        };

        for root_id in candidate_roots {
            let canon_root = egraph.find(root_id);
            let mut subst = Subst::new();
            Self::match_in_class(egraph, canon_root, pattern, &mut subst, &mut matches);
        }

        matches
    }

    /// فحص مطابقة نمط داخل فئة تكافؤ محددة
    pub fn match_in_class(
        egraph: &TransactionalEGraph,
        class_id: EClassId,
        pattern: &Pattern,
        subst: &mut Subst,
        results: &mut Vec<MatchResult>,
    ) {
        let canon_id = egraph.find(class_id);

        match pattern {
            // المتغير الحر يطابق أي فئة بشرط اتساق قيود التساوي المتكررة (Equijoins)
            Pattern::Wildcard(var_id) => {
                let mut new_subst = subst.clone();
                if new_subst.insert(*var_id, canon_id, egraph) {
                    results.push(MatchResult {
                        root: canon_id,
                        subst: new_subst,
                        n_ary_context: None,
                    });
                }
            }

            Pattern::LiteralVar(target_var) => {
                if let Some(class) = egraph.classes.get(&canon_id) {
                    for node in &class.nodes {
                        if let ENode::Var(v) = node {
                            if v == target_var {
                                results.push(MatchResult {
                                    root: canon_id,
                                    subst: subst.clone(),
                                    n_ary_context: None,
                                });
                                break;
                            }
                        }
                    }
                }
            }

            Pattern::Const(target_const) => {
                if let Some(class) = egraph.classes.get(&canon_id) {
                    for node in &class.nodes {
                        if let ENode::Const(c) = node {
                            if c == target_const {
                                results.push(MatchResult {
                                    root: canon_id,
                                    subst: subst.clone(),
                                    n_ary_context: None,
                                });
                                break;
                            }
                        }
                    }
                }
            }

            Pattern::Neg(inner_pattern) => {
                if let Some(class) = egraph.classes.get(&canon_id) {
                    for node in &class.nodes {
                        if let ENode::Neg(inner_id) = node {
                            let canon_child = egraph.find(*inner_id);
                            let mut child_matches = Vec::new();
                            Self::match_in_class(
                                egraph,
                                canon_child,
                                inner_pattern,
                                subst,
                                &mut child_matches,
                            );
                            for m in child_matches {
                                results.push(MatchResult {
                                    root: canon_id,
                                    subst: m.subst,
                                    n_ary_context: None,
                                });
                            }
                        }
                    }
                }
            }

            // الجمع التبادلي: معالجة التباديل والعمليات متعددة المعاملات
            Pattern::Add(op_patterns) => {
                if let Some(class) = egraph.classes.get(&canon_id) {
                    for node in &class.nodes {
                        if let ENode::Add(ops) = node {
                            Self::match_commutative_ops(
                                egraph,
                                canon_id,
                                ops,
                                op_patterns,
                                ENodeKind::Add,
                                subst,
                                results,
                            );
                        }
                    }
                }
            }

            // الضرب التبادلي: معالجة التباديل والعمليات متعددة المعاملات
            Pattern::Mul(op_patterns) => {
                if let Some(class) = egraph.classes.get(&canon_id) {
                    for node in &class.nodes {
                        if let ENode::Mul(ops) = node {
                            Self::match_commutative_ops(
                                egraph,
                                canon_id,
                                ops,
                                op_patterns,
                                ENodeKind::Mul,
                                subst,
                                results,
                            );
                        }
                    }
                }
            }

            Pattern::Div(num_pattern, den_pattern) => {
                if let Some(class) = egraph.classes.get(&canon_id) {
                    for node in &class.nodes {
                        if let ENode::Div(ops) = node {
                            let canon_num = egraph.find(ops[0]);
                            let canon_den = egraph.find(ops[1]);

                            let mut num_matches = Vec::new();
                            Self::match_in_class(
                                egraph,
                                canon_num,
                                num_pattern,
                                subst,
                                &mut num_matches,
                            );

                            for nm in num_matches {
                                let mut den_matches = Vec::new();
                                let mut subst_copy = nm.subst.clone();
                                Self::match_in_class(
                                    egraph,
                                    canon_den,
                                    den_pattern,
                                    &mut subst_copy,
                                    &mut den_matches,
                                );
                                for dm in den_matches {
                                    results.push(MatchResult {
                                        root: canon_id,
                                        subst: dm.subst,
                                        n_ary_context: None,
                                    });
                                }
                            }
                        }
                    }
                }
            }

            Pattern::Pow(base_pattern, target_exp) => {
                if let Some(class) = egraph.classes.get(&canon_id) {
                    for node in &class.nodes {
                        if let ENode::Pow(base_id, exp) = node {
                            if exp == target_exp {
                                let canon_base = egraph.find(*base_id);
                                let mut base_matches = Vec::new();
                                Self::match_in_class(
                                    egraph,
                                    canon_base,
                                    base_pattern,
                                    subst,
                                    &mut base_matches,
                                );
                                for bm in base_matches {
                                    results.push(MatchResult {
                                        root: canon_id,
                                        subst: bm.subst,
                                        n_ary_context: None,
                                    });
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    /// مطابقة العمليات التبادلية (Commutative Matching Engine):
    /// 1. فحص التباديل الكاملة للعمليات الثنائية لمنع الفشل عند انعكاس الترتيب الكنسي في الذاكرة
    /// 2. دعم اختزال العمليات متعددة المعاملات N-Ary بمطابقة النمط الثنائي على أي زوج فرعي مع حفظ باقي السياق
    fn match_commutative_ops(
        egraph: &TransactionalEGraph,
        root_id: EClassId,
        ops: &[EClassId],
        patterns: &[Pattern],
        kind: ENodeKind,
        subst: &Subst,
        results: &mut Vec<MatchResult>,
    ) {
        if patterns.len() == 2 && ops.len() == 2 {
            // فحص الترتيبين التبادليين للعملية الثنائية: (ops[0], ops[1]) و (ops[1], ops[0])
            Self::match_pair(
                egraph,
                root_id,
                (ops[0], ops[1]),
                patterns,
                None,
                subst,
                results,
            );

            if egraph.find(ops[0]) != egraph.find(ops[1]) {
                Self::match_pair(
                    egraph,
                    root_id,
                    (ops[1], ops[0]),
                    patterns,
                    None,
                    subst,
                    results,
                );
            }
        } else if patterns.len() == 2 && ops.len() > 2 {
            // اختزال العمليات متعددة المعاملات (N-Ary Arity Reduction):
            // مطابقة النمط الثنائي على كل زوج فرعي (i, j) داخل العقدة العريضة
            // مع حفظ المعاملات المتبقية لإعادة بناء السياق (Context Reconstruction)
            for i in 0..ops.len() {
                for j in (i + 1)..ops.len() {
                    let mut remaining = SmallVec::with_capacity(ops.len() - 2);
                    for (idx, &op) in ops.iter().enumerate() {
                        if idx != i && idx != j {
                            remaining.push(op);
                        }
                    }
                    let context = Some((kind, remaining.clone()));

                    Self::match_pair(
                        egraph,
                        root_id,
                        (ops[i], ops[j]),
                        patterns,
                        context.clone(),
                        subst,
                        results,
                    );

                    if egraph.find(ops[i]) != egraph.find(ops[j]) {
                        Self::match_pair(
                            egraph,
                            root_id,
                            (ops[j], ops[i]),
                            patterns,
                            context,
                            subst,
                            results,
                        );
                    }
                }
            }
        } else if patterns.len() == ops.len() {
            // للأطوال المتساوية
            Self::match_children_sequence(egraph, root_id, ops, patterns, subst, results);
        }
    }

    /// مطابقة زوج من المعاملات مع نمطين ثنائيين
    fn match_pair(
        egraph: &TransactionalEGraph,
        root_id: EClassId,
        pair: (EClassId, EClassId),
        patterns: &[Pattern],
        context: Option<(ENodeKind, SmallVec<[EClassId; 2]>)>,
        subst: &Subst,
        results: &mut Vec<MatchResult>,
    ) {
        let (op0, op1) = pair;
        let mut s0_matches = Vec::new();
        let mut subst_copy = subst.clone();
        Self::match_in_class(
            egraph,
            egraph.find(op0),
            &patterns[0],
            &mut subst_copy,
            &mut s0_matches,
        );

        for m0 in s0_matches {
            let mut s1_matches = Vec::new();
            let mut s0_subst = m0.subst;
            Self::match_in_class(
                egraph,
                egraph.find(op1),
                &patterns[1],
                &mut s0_subst,
                &mut s1_matches,
            );

            for m1 in s1_matches {
                results.push(MatchResult {
                    root: root_id,
                    subst: m1.subst,
                    n_ary_context: context.clone(),
                });
            }
        }
    }

    /// مطابقة متسلسلة لأبناء عقدة مركبة
    fn match_children_sequence(
        egraph: &TransactionalEGraph,
        root_id: EClassId,
        children: &[EClassId],
        patterns: &[Pattern],
        initial_subst: &Subst,
        results: &mut Vec<MatchResult>,
    ) {
        let mut current_substs = vec![initial_subst.clone()];

        for (i, p) in patterns.iter().enumerate() {
            let child_id = egraph.find(children[i]);
            let mut next_substs = Vec::new();

            for s in &current_substs {
                let mut child_matches = Vec::new();
                let mut subst_copy = s.clone();
                Self::match_in_class(egraph, child_id, p, &mut subst_copy, &mut child_matches);
                for cm in child_matches {
                    next_substs.push(cm.subst);
                }
            }

            current_substs = next_substs;
            if current_substs.is_empty() {
                return;
            }
        }

        for s in current_substs {
            results.push(MatchResult {
                root: root_id,
                subst: s,
                n_ary_context: None,
            });
        }
    }
}
