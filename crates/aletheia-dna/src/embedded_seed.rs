use crate::header::{FLAG_LITTLE_ENDIAN, FLAG_SEED_MODE, HEADER_SIZE, PackedDNAHeader};
use crate::packed_enode::{ENODE_SIZE, PackedENode};
use crate::record::UniversalRecordPrefix;
use std::sync::OnceLock;

/// توليد كبسولة البذرة الجينية المعرفية المدمجة
/// تحتوي على المعرفة التأسيسية الصرفة: الصفر، الواحد، والأبعاد الميكانيكية الأساسية الثلاثة [M, L, T]
pub fn generate_canonical_seed() -> Vec<u8> {
    let mut buffer = Vec::new();

    // 1. حساب الإزاحات
    let offset_enodes = HEADER_SIZE as u64;
    // عقدتان أساسيتان: الثابت 0، والثابت 1
    let enodes_count = 2u32;
    let offset_uf = offset_enodes + (enodes_count as u64 * ENODE_SIZE as u64);
    // صنفان تكافؤيان: فئة الصفر (0) وفئة الواحد (1)
    let classes_count = 2u32;
    let offset_lineage = offset_uf + (classes_count as u64 * 4);

    // 5. سجل البديهية التأسيسية الأولى (0 != 1) لحساب الحجم مسبقاً
    let payload = b"AXIOM_IDENTITY: ZERO_ONE_DISTINCT";
    let payload_crc = UniversalRecordPrefix::compute_crc(payload);
    let prefix = UniversalRecordPrefix::new_axiom(payload.len() as u32, 0, payload_crc, 1);
    let lineage_size = (crate::record::RECORD_PREFIX_SIZE + payload.len()) as u32;

    // 2. ترويسة البذرة
    let mut header = PackedDNAHeader {
        magic: *b"KDNA",
        version: 0x0100,
        flags: FLAG_LITTLE_ENDIAN | FLAG_SEED_MODE | (3 << 8), // 3 أبعاد أولية
        total_axioms: 1,
        total_enodes: enodes_count,
        total_classes: classes_count,
        lineage_size,
        offset_enodes,
        offset_uf,
        offset_lineage,
        state_checksum: 0,
        merkle_root_id: 0xCAFE_BABE_0000_0001,
    };
    header.state_checksum = header.compute_checksum();

    buffer.extend_from_slice(&header.to_bytes());

    // 3. كتابة العقد الأساسية في الـ Arena (عقدة 0: ثابت 0، عقدة 1: ثابت 1)
    let node_zero = PackedENode::new_constant(0, 0);
    let node_one = PackedENode::new_constant(1, 1);
    buffer.extend_from_slice(&node_zero.to_bytes());
    buffer.extend_from_slice(&node_one.to_bytes());

    // 4. كتابة جدول الـ Union-Find بضغط مسار كامل 100% (parent[0] = 0, parent[1] = 1)
    buffer.extend_from_slice(&0u32.to_le_bytes());
    buffer.extend_from_slice(&1u32.to_le_bytes());

    // 5. كتابة سجل البديهية التأسيسية الأولى (0 != 1)
    buffer.extend_from_slice(&prefix.to_bytes());
    buffer.extend_from_slice(payload);

    buffer
}

static SEED_STORAGE: OnceLock<Vec<u8>> = OnceLock::new();

/// استرجاع مرجع ثابت للبذرة الجينية المدمجة في الـ RAM
pub fn get_embedded_seed() -> &'static [u8] {
    SEED_STORAGE.get_or_init(generate_canonical_seed).as_slice()
}
