use crate::anti_unification::AntiUnifier;
use crate::error::DnaError;
use crate::mmap_engine::DnaStorageEngine;
use crate::record::{UniversalRecordPrefix, RECORD_PREFIX_SIZE};
use aletheia_rewriting::MacroRule;

/// محرك تخليد وختم القواعد الكبرى الناتجة عن التخطيط متعدد الخطوات في شريط الـ DNA (المحور 8)
pub struct MacroRuleSealer;

impl MacroRuleSealer {
    /// تعميم القاعدة الكبرى عبر التوحيد العكسي وختمها في ركيزة الـ DNA كحافة تكافؤ سيادية
    pub fn seal_macro_rule(
        storage: &mut DnaStorageEngine,
        macro_rule: &MacroRule,
        domain_id: u16,
    ) -> Result<u64, DnaError> {
        let lhs_dummy = macro_rule.lhs.to_canonical_dummy();
        let rhs_dummy = macro_rule.rhs.to_canonical_dummy();

        // 1. التوحيد العكسي لتعميم مسار البرهان واستخراج النظرية الفوقية
        let (generalized_expr, _, _) = AntiUnifier::anti_unify(&lhs_dummy, &rhs_dummy);

        // 2. إعداد الحمولة البايتية للسجل المعرفي
        let rule_name_bytes = macro_rule.name.as_bytes();
        let gen_str = format!("{:?}", generalized_expr);
        let gen_bytes = gen_str.as_bytes();

        let mut payload = Vec::with_capacity(rule_name_bytes.len() + gen_bytes.len() + 8);
        payload.extend_from_slice(&(rule_name_bytes.len() as u32).to_le_bytes());
        payload.extend_from_slice(rule_name_bytes);
        payload.extend_from_slice(&(gen_bytes.len() as u32).to_le_bytes());
        payload.extend_from_slice(gen_bytes);

        // 3. بناء بادئة السجل المعرفي لحافة تكافؤ سيادية
        let payload_crc = UniversalRecordPrefix::compute_crc(&payload);
        let prefix = UniversalRecordPrefix::new_congruence_edge(
            domain_id,
            payload.len() as u32,
            payload_crc,
        );

        // 4. كتابة السجل في ذيل قطاع السجلات التراكمي في الـ DNA
        let append_offset =
            storage.header.offset_lineage as usize + storage.header.lineage_size as usize;
        let record_len = RECORD_PREFIX_SIZE + payload.len();
        let next_capacity = append_offset + record_len;
        storage.ensure_capacity(next_capacity)?;

        {
            let buf = storage.buffer_mut()?;
            buf[append_offset..append_offset + RECORD_PREFIX_SIZE]
                .copy_from_slice(&prefix.to_bytes());
            buf[append_offset + RECORD_PREFIX_SIZE..next_capacity].copy_from_slice(&payload);
        }

        storage.header.lineage_size += record_len as u32;
        storage.header.total_axioms += 1;
        storage.flush()?;

        Ok(append_offset as u64)
    }
}
