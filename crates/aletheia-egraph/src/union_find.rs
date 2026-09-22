use crate::id::EClassId;

/// شجرة الاتحاد والبحث العكسية القابلة للتراجع (Reversible Union-Find)
/// تعتمد Union-by-Rank لتوفير find خفيف وسريع O(log N) للقراءة دون تلويث مكدس التراجع
#[derive(Clone, Debug, Default)]
pub struct UnionFind {
    parents: Vec<EClassId>,
    ranks: Vec<u32>,
}

impl UnionFind {
    pub fn new() -> Self {
        Self {
            parents: Vec::new(),
            ranks: Vec::new(),
        }
    }

    /// إنشاء فئة تكافؤ جديدة تشير إلى نفسها برتبة 0
    pub fn make_set(&mut self) -> EClassId {
        let id = EClassId(self.parents.len() as u32);
        self.parents.push(id);
        self.ranks.push(0);
        id
    }

    /// عدد المجموعات الإجمالي المسجل
    #[inline]
    pub fn len(&self) -> usize {
        self.parents.len()
    }

    #[inline]
    pub fn is_empty(&self) -> bool {
        self.parents.is_empty()
    }

    /// استعلام الممثل الكنسي (Read-only Find):
    /// يلاحق المؤشرات بسرعة خفيفة دون أي تعديل أو ضغط مسار يلوث مكدس التراجع
    #[inline]
    pub fn find(&self, mut id: EClassId) -> EClassId {
        while (id.0 as usize) < self.parents.len() {
            let p = self.parents[id.0 as usize];
            if p == id {
                break;
            }
            id = p;
        }
        id
    }

    /// دمج مجموعتين برتبتهما (Union-by-Rank)
    /// يُرجع بيانات التعديل الدقيقة لعكسها في سجل التراجع: (child, parent, old_parent_rank)
    pub fn union(&mut self, root1: EClassId, root2: EClassId) -> Option<(EClassId, EClassId, u32)> {
        let r1 = self.find(root1);
        let r2 = self.find(root2);

        if r1 == r2 {
            return None;
        }

        let idx1 = r1.0 as usize;
        let idx2 = r2.0 as usize;

        let rank1 = self.ranks[idx1];
        let rank2 = self.ranks[idx2];

        if rank1 < rank2 {
            // جعل r1 تابعة لـ r2
            self.parents[idx1] = r2;
            Some((r1, r2, rank2))
        } else if rank1 > rank2 {
            // جعل r2 تابعة لـ r1
            self.parents[idx2] = r1;
            Some((r2, r1, rank1))
        } else {
            // تساوي الرتب: جعل r2 تابعة لـ r1 وزيادة رتبة r1 بمقدار 1
            self.parents[idx2] = r1;
            self.ranks[idx1] += 1;
            Some((r2, r1, rank1))
        }
    }

    /// التراجع العكسي الفوري لعملية دمج O(1)
    pub fn rollback_union(&mut self, child: EClassId, parent: EClassId, old_parent_rank: u32) {
        let child_idx = child.0 as usize;
        let parent_idx = parent.0 as usize;

        debug_assert_eq!(self.parents[child_idx], parent);
        self.parents[child_idx] = child;
        self.ranks[parent_idx] = old_parent_rank;
    }

    /// تقليص حجم الشجرة عند التراجع الكامل عن إنشاء فئات جديدة
    pub fn truncate(&mut self, len: usize) {
        self.parents.truncate(len);
        self.ranks.truncate(len);
    }
}
