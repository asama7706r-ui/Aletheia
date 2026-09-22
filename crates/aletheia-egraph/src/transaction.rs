use crate::egraph::TransactionalEGraph;
use std::ops::{Deref, DerefMut};

/// مدير سياق المعاملات الذري بنمط RAII الآمن
/// يضمن طهارة الذاكرة بنسبة 100% والتراجع التلقائي إذا لم يتم التثبيت صراحة (commit)
pub struct Transaction<'a> {
    egraph: &'a mut TransactionalEGraph,
    checkpoint_token: usize,
    committed: bool,
}

impl<'a> Transaction<'a> {
    /// فتح معاملة ذرية جديدة
    pub fn new(egraph: &'a mut TransactionalEGraph) -> Self {
        let checkpoint_token = egraph.checkpoint();
        Self {
            egraph,
            checkpoint_token,
            committed: false,
        }
    }

    /// نقطة التفتيش التي بدأت منها المعاملة
    #[inline]
    pub fn checkpoint_token(&self) -> usize {
        self.checkpoint_token
    }

    /// تثبيت المعاملة واعتماد كل التغييرات المنجزة
    pub fn commit(mut self) {
        self.egraph.commit(self.checkpoint_token);
        self.committed = true;
    }

    /// التراجع الصريح عن المعاملة فوراً
    pub fn rollback(mut self) {
        self.egraph.rollback(self.checkpoint_token);
        self.committed = true;
    }
}

impl<'a> Deref for Transaction<'a> {
    type Target = TransactionalEGraph;
    #[inline]
    fn deref(&self) -> &Self::Target {
        self.egraph
    }
}

impl<'a> DerefMut for Transaction<'a> {
    #[inline]
    fn deref_mut(&mut self) -> &mut Self::Target {
        self.egraph
    }
}

impl<'a> Drop for Transaction<'a> {
    fn drop(&mut self) {
        // إذا خرج الكائن من النطاق دون commit صريح (بسبب استثناء أو خطأ)، يُلغى كل شيء فورياً
        if !self.committed {
            self.egraph.rollback(self.checkpoint_token);
        }
    }
}

impl TransactionalEGraph {
    /// فتح معاملة ذرية جديدة محصنة بنمط RAII
    pub fn transaction(&mut self) -> Transaction<'_> {
        Transaction::new(self)
    }
}
