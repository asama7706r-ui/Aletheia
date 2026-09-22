use crate::error::YonedaError;
use crate::shadow::LatentShadow;
use crate::spectral_audit::DiagnosticVector;
use aletheia_algebra::Rational;
use aletheia_lattice::DimensionVector;
use std::collections::HashMap;
use std::fs::File;
use std::io::{BufReader, BufWriter, Read, Write};
use std::path::Path;

/// الترويسة السحرية المعيارية الصارمة للملف الجانبي للحجر الصحي
pub const MAGIC_HEADER: &[u8; 8] = b"ALETH_Q1";

/// صفة السلطة المعرفية للفرضيات المحتجزة
pub const AUTHORITY_NON_SOVEREIGN: &str = "NON_SOVEREIGN";

/// سجل الحجر الصحي الحتمي للفرضيات الناشئة المعلقة
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct QuarantineRecord {
    /// تجزئة BLAKE3 للنموذج المعياري الصرف للفرضية
    pub record_id: [u8; 32],
    /// كائن الظل السالب المستخلص من عجز الأقفال
    pub shadow: LatentShadow,
    /// الصفة القطعية لمنع السيادة البرهانية قبل الترقية
    pub authority: String,
    /// عمر الفرضية بعدد دورات التشبع في الحجر
    pub saturation_age: usize,
    /// درجات الحرية الصافية المتبقية (كسر نسبي دقيق في Q)
    pub remaining_dof: Rational,
    /// مفاتيح الحواف الفائقة المرتبطة بالمجاهيل والعجوزات
    pub hyperedge_keys: Vec<[u8; 32]>,
    /// علم الخمول المرحلي للفرضيات الراكدة (دون إعدام)
    pub is_dormant: bool,
}

impl QuarantineRecord {
    pub fn new(shadow: LatentShadow) -> Self {
        let mut hasher = blake3::Hasher::new();
        hasher.update(&shadow.shadow_id);
        for origin in &shadow.origin_law_ids {
            hasher.update(origin.as_bytes());
        }
        let record_id = *hasher.finalize().as_bytes();
        let remaining_dof = shadow.dof.clone();
        Self {
            record_id,
            shadow,
            authority: AUTHORITY_NON_SOVEREIGN.to_string(),
            saturation_age: 0,
            remaining_dof,
            hyperedge_keys: Vec::new(),
            is_dormant: false,
        }
    }

    /// زيادة عمر الفرضية بدورة تشبع
    pub fn increment_age(&mut self) {
        self.saturation_age += 1;
    }

    /// تعيين حالة الخمول المرحلي
    pub fn set_dormant(&mut self, dormant: bool) {
        self.is_dormant = dormant;
    }
}

/// مستودع الذاكرة الحية المعزول للفرضيات المحتجزة (Active RAM LatentBuffer)
#[derive(Clone, Debug, Default)]
pub struct LatentBuffer {
    records: HashMap<[u8; 32], QuarantineRecord>,
}

impl LatentBuffer {
    pub fn new() -> Self {
        Self {
            records: HashMap::new(),
        }
    }

    #[inline]
    pub fn len(&self) -> usize {
        self.records.len()
    }

    #[inline]
    pub fn is_empty(&self) -> bool {
        self.records.is_empty()
    }

    /// إيداع فرضية في الذاكرة الحية
    pub fn admit(&mut self, record: QuarantineRecord) {
        self.records.insert(record.record_id, record);
    }

    pub fn get(&self, id: &[u8; 32]) -> Option<&QuarantineRecord> {
        self.records.get(id)
    }

    pub fn get_mut(&mut self, id: &[u8; 32]) -> Option<&mut QuarantineRecord> {
        self.records.get_mut(id)
    }

    pub fn remove(&mut self, id: &[u8; 32]) -> Option<QuarantineRecord> {
        self.records.remove(id)
    }

    /// تصفير الحجر الحي بالكامل عند التراجع الذري للـ E-Graph
    pub fn clear(&mut self) {
        self.records.clear();
    }

    pub fn records(&self) -> impl Iterator<Item = &QuarantineRecord> {
        self.records.values()
    }

    pub fn records_mut(&mut self) -> impl Iterator<Item = &mut QuarantineRecord> {
        self.records.values_mut()
    }

    /// حفظ كافة السجلات المحتجزة إلى الركيزة الجانبية quarantine.bin مع الترويسة السحرية ALETH_Q1
    pub fn save_to_file(&self, path: &Path) -> Result<(), YonedaError> {
        let file = File::create(path).map_err(|e| YonedaError::StorageError(e.to_string()))?;
        let mut writer = BufWriter::new(file);

        // 1. كتابة الترويسة السحرية
        writer
            .write_all(MAGIC_HEADER)
            .map_err(|e| YonedaError::StorageError(e.to_string()))?;

        // 2. كتابة عدد السجلات
        let count = self.records.len() as u32;
        writer
            .write_all(&count.to_le_bytes())
            .map_err(|e| YonedaError::StorageError(e.to_string()))?;

        // 3. كتابة السجلات
        for record in self.records.values() {
            Self::write_record(&mut writer, record)?;
        }

        writer
            .flush()
            .map_err(|e| YonedaError::StorageError(e.to_string()))?;
        Ok(())
    }

    /// استرجاع الفرضيات من الركيزة الجانبية quarantine.bin والتحقق الصارم من الترويسة
    pub fn load_from_file(&mut self, path: &Path) -> Result<(), YonedaError> {
        if !path.exists() {
            return Ok(());
        }

        let file = File::open(path).map_err(|e| YonedaError::StorageError(e.to_string()))?;
        let mut reader = BufReader::new(file);

        // 1. قراءة وفحص الترويسة السحرية
        let mut header = [0u8; 8];
        reader
            .read_exact(&mut header)
            .map_err(|e| YonedaError::StorageError(e.to_string()))?;

        if &header != MAGIC_HEADER {
            return Err(YonedaError::StorageError(
                "ملف غير صالح: الترويسة السحرية ALETH_Q1 غير مطابقة".into(),
            ));
        }

        // 2. قراءة عدد السجلات
        let mut count_buf = [0u8; 4];
        reader
            .read_exact(&mut count_buf)
            .map_err(|e| YonedaError::StorageError(e.to_string()))?;
        let count = u32::from_le_bytes(count_buf);

        // 3. قراءة السجلات
        for _ in 0..count {
            let record = Self::read_record(&mut reader)?;
            self.records.insert(record.record_id, record);
        }

        Ok(())
    }

    fn write_record<W: Write>(w: &mut W, r: &QuarantineRecord) -> Result<(), YonedaError> {
        w.write_all(&r.record_id)
            .map_err(|e| YonedaError::StorageError(e.to_string()))?;
        w.write_all(&(r.saturation_age as u64).to_le_bytes())
            .map_err(|e| YonedaError::StorageError(e.to_string()))?;
        w.write_all(&[if r.is_dormant { 1 } else { 0 }])
            .map_err(|e| YonedaError::StorageError(e.to_string()))?;

        // كتابة dof ككسر نسبي
        Self::write_rational(w, &r.remaining_dof)?;

        // كتابة متجه الأبعاد
        let coords = r.shadow.dim_deficit.coords();
        w.write_all(&(coords.len() as u32).to_le_bytes())
            .map_err(|e| YonedaError::StorageError(e.to_string()))?;
        for c in coords {
            Self::write_rational(w, c)?;
        }

        w.write_all(&(r.shadow.tensorial_rank as u32).to_le_bytes())
            .map_err(|e| YonedaError::StorageError(e.to_string()))?;
        w.write_all(&(r.shadow.macaulay_ceiling as u64).to_le_bytes())
            .map_err(|e| YonedaError::StorageError(e.to_string()))?;

        // كتابة الحواف الفائقة
        w.write_all(&(r.hyperedge_keys.len() as u32).to_le_bytes())
            .map_err(|e| YonedaError::StorageError(e.to_string()))?;
        for k in &r.hyperedge_keys {
            w.write_all(k)
                .map_err(|e| YonedaError::StorageError(e.to_string()))?;
        }

        // كتابة معرفات القوانين المصدرية
        w.write_all(&(r.shadow.origin_law_ids.len() as u32).to_le_bytes())
            .map_err(|e| YonedaError::StorageError(e.to_string()))?;
        for law_id in &r.shadow.origin_law_ids {
            let bytes = law_id.as_bytes();
            w.write_all(&(bytes.len() as u32).to_le_bytes())
                .map_err(|e| YonedaError::StorageError(e.to_string()))?;
            w.write_all(bytes)
                .map_err(|e| YonedaError::StorageError(e.to_string()))?;
        }

        Ok(())
    }

    fn read_record<R: Read>(r: &mut R) -> Result<QuarantineRecord, YonedaError> {
        let mut record_id = [0u8; 32];
        r.read_exact(&mut record_id)
            .map_err(|e| YonedaError::StorageError(e.to_string()))?;

        let mut age_buf = [0u8; 8];
        r.read_exact(&mut age_buf)
            .map_err(|e| YonedaError::StorageError(e.to_string()))?;
        let saturation_age = u64::from_le_bytes(age_buf) as usize;

        let mut dormant_buf = [0u8; 1];
        r.read_exact(&mut dormant_buf)
            .map_err(|e| YonedaError::StorageError(e.to_string()))?;
        let is_dormant = dormant_buf[0] != 0;

        let remaining_dof = Self::read_rational(r)?;

        let mut num_coords_buf = [0u8; 4];
        r.read_exact(&mut num_coords_buf)
            .map_err(|e| YonedaError::StorageError(e.to_string()))?;
        let num_coords = u32::from_le_bytes(num_coords_buf) as usize;

        let mut coords = Vec::with_capacity(num_coords);
        for _ in 0..num_coords {
            coords.push(Self::read_rational(r)?);
        }
        let dim_deficit = DimensionVector::from_coords(coords);

        let mut rank_buf = [0u8; 4];
        r.read_exact(&mut rank_buf)
            .map_err(|e| YonedaError::StorageError(e.to_string()))?;
        let tensorial_rank = u32::from_le_bytes(rank_buf) as usize;

        let mut ceiling_buf = [0u8; 8];
        r.read_exact(&mut ceiling_buf)
            .map_err(|e| YonedaError::StorageError(e.to_string()))?;
        let macaulay_ceiling = u64::from_le_bytes(ceiling_buf) as usize;

        let mut num_hedges_buf = [0u8; 4];
        r.read_exact(&mut num_hedges_buf)
            .map_err(|e| YonedaError::StorageError(e.to_string()))?;
        let num_hedges = u32::from_le_bytes(num_hedges_buf) as usize;

        let mut hyperedge_keys = Vec::with_capacity(num_hedges);
        for _ in 0..num_hedges {
            let mut k = [0u8; 32];
            r.read_exact(&mut k)
                .map_err(|e| YonedaError::StorageError(e.to_string()))?;
            hyperedge_keys.push(k);
        }

        let mut num_laws_buf = [0u8; 4];
        r.read_exact(&mut num_laws_buf)
            .map_err(|e| YonedaError::StorageError(e.to_string()))?;
        let num_laws = u32::from_le_bytes(num_laws_buf) as usize;

        let mut origin_law_ids = Vec::with_capacity(num_laws);
        for _ in 0..num_laws {
            let mut len_buf = [0u8; 4];
            r.read_exact(&mut len_buf)
                .map_err(|e| YonedaError::StorageError(e.to_string()))?;
            let len = u32::from_le_bytes(len_buf) as usize;
            let mut str_bytes = vec![0u8; len];
            r.read_exact(&mut str_bytes)
                .map_err(|e| YonedaError::StorageError(e.to_string()))?;
            let s = String::from_utf8(str_bytes)
                .map_err(|e| YonedaError::StorageError(e.to_string()))?;
            origin_law_ids.push(s);
        }

        let shadow = LatentShadow {
            shadow_id: record_id,
            origin_law_ids,
            dim_deficit,
            tensorial_rank,
            dof: remaining_dof.clone(),
            spectral_audit: DiagnosticVector::default(),
            coupling_carrier: None,
            target_classes: Vec::new(),
            macaulay_ceiling,
        };

        Ok(QuarantineRecord {
            record_id,
            shadow,
            authority: AUTHORITY_NON_SOVEREIGN.to_string(),
            saturation_age,
            remaining_dof,
            hyperedge_keys,
            is_dormant,
        })
    }

    fn write_rational<W: Write>(w: &mut W, rat: &Rational) -> Result<(), YonedaError> {
        let s = format!("{}/{}", rat.numer(), rat.denom());
        let bytes = s.as_bytes();
        w.write_all(&(bytes.len() as u32).to_le_bytes())
            .map_err(|e| YonedaError::StorageError(e.to_string()))?;
        w.write_all(bytes)
            .map_err(|e| YonedaError::StorageError(e.to_string()))?;
        Ok(())
    }

    fn read_rational<R: Read>(r: &mut R) -> Result<Rational, YonedaError> {
        let mut len_buf = [0u8; 4];
        r.read_exact(&mut len_buf)
            .map_err(|e| YonedaError::StorageError(e.to_string()))?;
        let len = u32::from_le_bytes(len_buf) as usize;
        let mut bytes = vec![0u8; len];
        r.read_exact(&mut bytes)
            .map_err(|e| YonedaError::StorageError(e.to_string()))?;
        let s = String::from_utf8(bytes).map_err(|e| YonedaError::StorageError(e.to_string()))?;
        let parts: Vec<&str> = s.split('/').collect();
        if parts.len() != 2 {
            return Err(YonedaError::StorageError("تنسيق كسر غير صالح".into()));
        }
        let numer = parts[0]
            .parse::<num_bigint::BigInt>()
            .map_err(|e| YonedaError::StorageError(e.to_string()))?;
        let denom = parts[1]
            .parse::<num_bigint::BigInt>()
            .map_err(|e| YonedaError::StorageError(e.to_string()))?;
        Rational::from_bigint(numer, denom).map_err(|e| YonedaError::StorageError(format!("{:?}", e)))
    }
}
