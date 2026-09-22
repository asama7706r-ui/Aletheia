use crate::error::DnaError;

/// الحجم الثابت للعقدة المسطحة في مصفوفة الـ Arena (16 بايت بالضبط)
pub const ENODE_SIZE: usize = 16;

/// راية الثابت الفيزيائي/الرياضي الأصيل غير القابل للتعديل
pub const FLAG_IMMUTABLE_CONST: u8 = 0x04;
/// راية المعامل التبادلي (Commutative)
pub const FLAG_COMMUTATIVE: u8 = 0x01;
/// راية المعامل التجميعي (Associative)
pub const FLAG_ASSOCIATIVE: u8 = 0x02;

/// معرّفات العمليات الرياضية الجبرية الصامتة (Deterministic OpCodes)
#[repr(u16)]
#[derive(Copy, Clone, Debug, PartialEq, Eq)]
pub enum OpCode {
    Add = 0x0001,
    Mul = 0x0002,
    Pow = 0x0003,
    Neg = 0x0004,
    Diff = 0x0005,
    Integral = 0x0006,
    SymbolVar = 0x0007,
    RationalConst = 0x0008,
}

impl OpCode {
    pub fn from_u16(val: u16) -> Option<Self> {
        match val {
            0x0001 => Some(Self::Add),
            0x0002 => Some(Self::Mul),
            0x0003 => Some(Self::Pow),
            0x0004 => Some(Self::Neg),
            0x0005 => Some(Self::Diff),
            0x0006 => Some(Self::Integral),
            0x0007 => Some(Self::SymbolVar),
            0x0008 => Some(Self::RationalConst),
            _ => None,
        }
    }
}

/// بنية العقدة المسطحة المصمتة في مصفوفة الـ ENode Arena (16 Bytes Packed Struct)
/// مصممة بـ #[repr(C)] الصارم مع محاذاة طبيعية لضمان أقصى سرعة وأمان في الذاكرة
#[repr(C)]
#[derive(Copy, Clone, Debug, PartialEq, Eq)]
pub struct PackedENode {
    /// 0x00 - 0x01: معرّف المعامل الرياضي الحتمي (OpCode)
    pub op_id: u16,
    /// 0x02: عدد الفروع الفرعية (0 للثوابت/المتغيرات، 1 للأحادية، 2 للثنائية)
    pub arity: u8,
    /// 0x03: رايات الخصائص الجبرية (التبديلية، التجميعية، أو ثابت أصيل)
    pub flags: u8,
    /// 0x04 - 0x07: معرّف فئة التكافؤ للفرع الأول (left_class_id)
    pub left_class_id: u32,
    /// 0x08 - 0x0B: معرّف فئة التكافؤ للفرع الثاني (right_class_id)
    pub right_class_id: u32,
    /// 0x0C - 0x0F: فهرس الثابت في جدول الكسور أو معرّف الرمز المتغير (aux_data)
    pub aux_data: u32,
}

impl PackedENode {
    /// إنشاء عقدة ثابت كسري نسبي أصيل
    pub fn new_constant(class_id: u32, rational_index: u32) -> Self {
        Self {
            op_id: OpCode::RationalConst as u16,
            arity: 0,
            flags: FLAG_IMMUTABLE_CONST,
            left_class_id: class_id,
            right_class_id: 0,
            aux_data: rational_index,
        }
    }

    /// إنشاء عقدة متغير رمزي
    pub fn new_variable(class_id: u32, var_id: u32) -> Self {
        Self {
            op_id: OpCode::SymbolVar as u16,
            arity: 0,
            flags: 0,
            left_class_id: class_id,
            right_class_id: 0,
            aux_data: var_id,
        }
    }

    /// إنشاء عقدة عملية ثنائية (مثل الجمع أو الضرب)
    pub fn new_binary(op: OpCode, flags: u8, left_class: u32, right_class: u32) -> Self {
        Self {
            op_id: op as u16,
            arity: 2,
            flags,
            left_class_id: left_class,
            right_class_id: right_class,
            aux_data: 0,
        }
    }

    /// تسلسل العقدة إلى 16 بايت Little-Endian صرفة
    pub fn to_bytes(&self) -> [u8; ENODE_SIZE] {
        let mut bytes = [0u8; ENODE_SIZE];
        bytes[0..2].copy_from_slice(&self.op_id.to_le_bytes());
        bytes[2] = self.arity;
        bytes[3] = self.flags;
        bytes[4..8].copy_from_slice(&self.left_class_id.to_le_bytes());
        bytes[8..12].copy_from_slice(&self.right_class_id.to_le_bytes());
        bytes[12..16].copy_from_slice(&self.aux_data.to_le_bytes());
        bytes
    }

    /// فك تسلسل العقدة من 16 بايت
    pub fn from_bytes(bytes: &[u8]) -> Result<Self, DnaError> {
        if bytes.len() < ENODE_SIZE {
            return Err(DnaError::BufferUnderflow(bytes.len(), ENODE_SIZE));
        }

        let op_id = u16::from_le_bytes(bytes[0..2].try_into().unwrap());
        let arity = bytes[2];
        let flags = bytes[3];
        let left_class_id = u32::from_le_bytes(bytes[4..8].try_into().unwrap());
        let right_class_id = u32::from_le_bytes(bytes[8..12].try_into().unwrap());
        let aux_data = u32::from_le_bytes(bytes[12..16].try_into().unwrap());

        Ok(Self {
            op_id,
            arity,
            flags,
            left_class_id,
            right_class_id,
            aux_data,
        })
    }
}
