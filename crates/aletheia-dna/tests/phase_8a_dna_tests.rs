use aletheia_algebra::Rational;
use aletheia_dna::{
    get_embedded_seed, AutonomousEvolutionEngine, DnaStorageEngine,
    InstantHydrationPipeline, OpCode, PackedDNAHeader, PackedENode, UniversalRecordPrefix,
    ENODE_SIZE, FLAG_IMMUTABLE_CONST,
    HEADER_SIZE, MAGIC_KDNA, MAGIC_RECD, RECORD_PREFIX_SIZE, RECORD_STATUS_ACTIVE,
    RECORD_TYPE_SOVEREIGN_AXIOM,
};
use aletheia_epistemic::{DomainTag, LockReceipt, LockType, SovereignDnaPayload, SovereignReceipt};
use aletheia_lattice::DimensionVector;
use aletheia_rewriting::Cost;
use std::fs;
use std::path::PathBuf;

/// مسار مؤقت آمن للاختبارات في مجلد scratch
fn get_test_scratch_dir() -> PathBuf {
    let dir = std::env::temp_dir().join("aletheia_dna_tests");
    let _ = fs::create_dir_all(&dir);
    dir
}

#[test]
fn test_packed_dna_header_64_bytes_alignment_and_checksum() {
    assert_eq!(HEADER_SIZE, 64);
    assert_eq!(std::mem::size_of::<PackedDNAHeader>(), 64);

    let mut header = PackedDNAHeader::new(3);
    assert_eq!(&header.magic, MAGIC_KDNA);
    assert_eq!(header.dimension_rank(), 3);
    assert!(!header.is_compacted());
    assert!(!header.is_seed_mode());

    // التحقق من صحة البصمة التشفيرية CRC32C
    let computed_chk = header.compute_checksum();
    assert_eq!(header.state_checksum, computed_chk);

    // التحقق من التسلسل وفك التسلسل
    let bytes = header.to_bytes();
    assert_eq!(bytes.len(), 64);
    let recovered = PackedDNAHeader::from_bytes(&bytes).expect("Valid header must deserialize");
    assert_eq!(recovered, header);

    // التحقق من ترقية رتبة الأبعاد (Canonical Zero-Padding update)
    header.set_dimension_rank(4);
    assert_eq!(header.dimension_rank(), 4);
    let bytes_rank4 = header.to_bytes();
    let recovered_rank4 = PackedDNAHeader::from_bytes(&bytes_rank4).unwrap();
    assert_eq!(recovered_rank4.dimension_rank(), 4);

    // كشف التلاعب (Tamper Detection)
    let mut corrupted = bytes;
    corrupted[10] ^= 0xFF; // قلب بايت في total_axioms
    let tamper_res = PackedDNAHeader::from_bytes(&corrupted);
    assert!(tamper_res.is_err(), "Corrupted header must be rejected by checksum mismatch");
}

#[test]
fn test_packed_enode_16_bytes_and_universal_record_32_bytes() {
    assert_eq!(ENODE_SIZE, 16);
    assert_eq!(std::mem::size_of::<PackedENode>(), 16);
    assert_eq!(RECORD_PREFIX_SIZE, 32);
    assert_eq!(std::mem::size_of::<UniversalRecordPrefix>(), 32);

    // 1. فحص العقدة المسطحة
    let const_node = PackedENode::new_constant(5, 42);
    assert_eq!(const_node.op_id, OpCode::RationalConst as u16);
    assert_eq!(const_node.arity, 0);
    assert_eq!(const_node.flags, FLAG_IMMUTABLE_CONST);
    assert_eq!(const_node.left_class_id, 5);
    assert_eq!(const_node.aux_data, 42);

    let node_bytes = const_node.to_bytes();
    assert_eq!(node_bytes.len(), 16);
    let recovered_node = PackedENode::from_bytes(&node_bytes).unwrap();
    assert_eq!(recovered_node, const_node);

    // 2. فحص بادئة السجل المعرفي
    let payload = b"SOVEREIGN_AXIOM_PAYLOAD_TEST";
    let crc = UniversalRecordPrefix::compute_crc(payload);
    let prefix = UniversalRecordPrefix::new_axiom(payload.len() as u32, 1, crc, 100);
    assert_eq!(&prefix.magic, MAGIC_RECD);
    assert_eq!(prefix.record_type, RECORD_TYPE_SOVEREIGN_AXIOM);
    assert_eq!(prefix.status, RECORD_STATUS_ACTIVE);
    assert_eq!(prefix.domain_id, 1);
    assert_eq!(prefix.extra_meta, 100);

    let prefix_bytes = prefix.to_bytes();
    assert_eq!(prefix_bytes.len(), 32);
    let recovered_prefix = UniversalRecordPrefix::from_bytes(&prefix_bytes).unwrap();
    assert_eq!(recovered_prefix, prefix);
}

#[test]
fn test_instant_hydration_pipeline_boot_sub_3ms_latency() {
    // الإقلاع من البذرة المدمجة في الـ RAM
    let pipeline = InstantHydrationPipeline::boot::<&str>(None, false)
        .expect("Boot from embedded seed must succeed");

    // التحقق من حتمية الإقلاع في زمن شبه معدوم (< 3 ms)
    println!("Embedded Seed Boot Latency: {} micros", pipeline.boot_latency_micros);
    assert!(
        pipeline.verify_sub_3ms_invariant(),
        "Boot latency must be strictly under 3000 microseconds, got {} us",
        pipeline.boot_latency_micros
    );

    assert!(!pipeline.is_evolutionary_mode);
    assert_eq!(pipeline.storage.header.dimension_rank(), 3);
    assert_eq!(pipeline.storage.header.total_classes, 2);
}

#[test]
fn test_dual_boot_protocol_and_embedded_seed_fallback() {
    let test_dir = get_test_scratch_dir();
    let missing_path = test_dir.join("non_existent_kernel.dna");
    let _ = fs::remove_file(&missing_path);

    // 1. الإقلاع بمسار غير موجود في وضع القراءة فقط => الرجوع التلقائي للبذرة المدمجة (Fallback)
    let fallback_pipeline = InstantHydrationPipeline::boot(Some(&missing_path), false)
        .expect("Missing file should fallback to embedded seed");
    assert!(!fallback_pipeline.is_evolutionary_mode);
    assert_eq!(fallback_pipeline.storage.header.total_enodes, 2);

    // 2. الإقلاع بمسار غير موجود في وضع التطور (Evolution Mode) => إنشاء وتفريغ البذرة في ملف محلي
    let evo_path = test_dir.join("evolution_test_kernel.dna");
    let _ = fs::remove_file(&evo_path);

    let evo_pipeline = InstantHydrationPipeline::boot(Some(&evo_path), true)
        .expect("Evolution boot should initialize local DNA file");
    assert!(evo_pipeline.is_evolutionary_mode);
    assert!(evo_path.exists());
    assert!(fs::metadata(&evo_path).unwrap().len() >= HEADER_SIZE as u64);

    // التأكد من إمكانية إعادة القراءة من الملف المحلي المنشأ
    let reloaded = DnaStorageEngine::open_read_only(&evo_path)
        .expect("Created local DNA file must be valid for reading");
    assert_eq!(reloaded.header.total_classes, 2);

    let _ = fs::remove_file(&evo_path);
}

#[test]
fn test_full_path_compression_invariant_and_o1_fast_equivalence() {
    // البذرة المدمجة تحتوي على فئتين: فئة 0 (للصفر)، وفئة 1 (للواحد) مع تسطيح مسار 100%
    let seed_slice = get_embedded_seed();
    let storage = DnaStorageEngine::from_static_slice(seed_slice)
        .expect("Static slice boot must succeed");

    // نفس الصنف => متكافئان دائماً
    assert!(storage.query_fast_equivalence(0, 0).unwrap());
    assert!(storage.query_fast_equivalence(1, 1).unwrap());

    // صنف 0 وصنف 1 لهما جذران مختلفان (0 != 1) => غير متكافئين
    assert!(!storage.query_fast_equivalence(0, 1).unwrap());
    assert!(!storage.query_fast_equivalence(1, 0).unwrap());

    // فئة خارج الحدود => false
    assert!(!storage.query_fast_equivalence(0, 999).unwrap());
}

#[test]
fn test_canonical_zero_padding_dimensional_extension() {
    let test_dir = get_test_scratch_dir();
    let dna_path = test_dir.join("dimension_test_kernel.dna");
    let _ = fs::remove_file(&dna_path);

    let storage = DnaStorageEngine::open_or_create(&dna_path, 3).unwrap();
    let mut engine = AutonomousEvolutionEngine::new(storage);

    assert_eq!(engine.storage.header.dimension_rank(), 3);

    // التمدد البعدي الفيزيائي من Q^3 إلى Q^4 (إضافة بعد الشحنة/التيار)
    let new_rank = engine.spawn_dimension("ElectricCurrent").unwrap();
    assert_eq!(new_rank, 4);
    assert_eq!(engine.storage.header.dimension_rank(), 4);

    // التمدد البعدي من Q^4 إلى Q^5 (إضافة بعد درجة الحرارة)
    let rank5 = engine.spawn_dimension("Temperature").unwrap();
    assert_eq!(rank5, 5);
    assert_eq!(engine.storage.header.dimension_rank(), 5);

    // إعادة فتح الملف والتأكد من استدامة التمدد البعدي
    let reopened = DnaStorageEngine::open_read_only(&dna_path).unwrap();
    assert_eq!(reopened.header.dimension_rank(), 5);

    let _ = fs::remove_file(&dna_path);
}

#[test]
fn test_windows_preallocation_arena_and_atomic_bridge_materialization() {
    let test_dir = get_test_scratch_dir();
    let dna_path = test_dir.join("bridge_arena_kernel.dna");
    let _ = fs::remove_file(&dna_path);

    let storage = DnaStorageEngine::open_or_create(&dna_path, 3).unwrap();
    let mut engine = AutonomousEvolutionEngine::new(storage);

    let initial_enodes = engine.storage.header.total_enodes;
    let initial_classes = engine.storage.header.total_classes;

    // زرع ثابت سرعة الضوء c = 299792458 / 1 مادياً بين الميكانيكا والنسبية
    let c_scale = Rational::new(299792458, 1).unwrap();
    let bridge_class = engine
        .materialize_bridge_constant(1, 4, c_scale.clone())
        .expect("Materializing bridge constant in pre-allocated arena must succeed");

    assert_eq!(bridge_class, initial_classes);
    assert_eq!(engine.storage.header.total_enodes, initial_enodes + 1);
    assert_eq!(engine.storage.header.total_classes, initial_classes + 1);

    // قراءة العقدة المزروعة مباشرة من الـ Arena
    let node = engine.storage.read_enode(initial_enodes).unwrap();
    assert_eq!(node.op_id, OpCode::RationalConst as u16);
    assert_eq!(node.flags, FLAG_IMMUTABLE_CONST);
    assert_eq!(node.left_class_id, bridge_class);
    assert_eq!(node.aux_data, 299792458);

    // فحص استعلام التكافؤ اللحظي للعقدة مع نفسها
    assert!(engine.storage.query_fast_equivalence(bridge_class, bridge_class).unwrap());

    let _ = fs::remove_file(&dna_path);
}

#[test]
fn test_sovereign_payload_ingestion_and_in_memory_floyd_warshall_routing() {
    let test_dir = get_test_scratch_dir();
    let dna_path = test_dir.join("ingest_route_kernel.dna");
    let _ = fs::remove_file(&dna_path);

    let storage = DnaStorageEngine::open_or_create(&dna_path, 3).unwrap();
    let mut engine = AutonomousEvolutionEngine::new(storage);

    // 1. تسجيل صكوك سيادية قادمة من المحور السابع
    let dummy_receipt = SovereignReceipt::issue_active(
        "maxwell_curl_e",
        [101u8; 32],
        aletheia_algebra::CanonicalExpr::Var(aletheia_algebra::VariableId(0)),
        DomainTag::Electromagnetism,
        DimensionVector::from_integers(&[1, 1, -2, -1]),
        Cost {
            size: 10,
            degree: 1,
            bit_complexity: 20,
            transcendental: 0,
        },
        vec![[1u8; 32]],
        vec![LockReceipt::new(
            LockType::ResidualSieve,
            "Residual Sieve",
            true,
            "Zero residual",
            None,
        )],
        None,
        1,
        5000,
    );

    let payload = SovereignDnaPayload::package(vec![dummy_receipt], 1)
        .expect("Payload packaging must succeed");

    let count = engine
        .ingest_sovereign_payload(&payload)
        .expect("Sovereign payload ingestion must succeed");
    assert_eq!(count, 1);
    assert_eq!(engine.storage.header.total_axioms, 1);

    // 2. زرع جسور فيزيائية مادياً في الـ DNA عبر الـ engine
    // جسر 1: من الميكانيكا (1) إلى الكهرومغناطيسية (2) بثابت اقتران 2/1
    engine
        .materialize_bridge_constant(1, 2, Rational::new(2, 1).unwrap())
        .expect("Bridge 1->2 must materialize");
    // جسر 2: من الكهرومغناطيسية (2) إلى ميكانيكا الكم (5) بثابت اقتران 3/1
    engine
        .materialize_bridge_constant(2, 5, Rational::new(3, 1).unwrap())
        .expect("Bridge 2->5 must materialize");

    engine.routing_matrix.recompute_all_known_pairs();
    let (path, k_cum) = engine
        .routing_matrix
        .query_route(1, 5)
        .expect("Direct route must exist in active engine");
    assert_eq!(path, &[1, 2, 5]);
    assert_eq!(k_cum, Rational::new(6, 1).unwrap());

    // 3. الاختبار الحاسم: إغلاق المحرك والتخزين بالكامل ومحاكاة إعادة الإقلاع (Full Reboot Cycle)
    drop(engine);

    // إعادة فتح الملف النظيف كـ DNA Storage جديد
    let reloaded_storage = DnaStorageEngine::open_or_create(&dna_path, 3)
        .expect("Reopening persisted DNA file must succeed");
    assert!(reloaded_storage.header.lineage_size > 0);
    assert_eq!(reloaded_storage.header.total_axioms, 1);
    assert_eq!(reloaded_storage.header.total_enodes, 2);

    // تشغيل محرك جديد: يجب أن يستدعي تلقائياً rebuild_in_memory_routing ويسترجع كافة الجسور
    let rebooted_engine = AutonomousEvolutionEngine::new(reloaded_storage);

    // التحقق من استرجاع الجسور والمسارات تلقائياً من الـ DNA دون أي تسجيل يدوي!
    let (reboot_path, reboot_k_cum) = rebooted_engine
        .routing_matrix
        .query_route(1, 5)
        .expect("Routing matrix must be automatically restored from DNA lineage on reboot!");
    assert_eq!(reboot_path, &[1, 2, 5]);
    assert_eq!(reboot_k_cum, Rational::new(6, 1).unwrap());

    // التحقق من الجسر المباشر 1 -> 2
    let (p12, k12) = rebooted_engine.routing_matrix.query_route(1, 2).unwrap();
    assert_eq!(p12, &[1, 2]);
    assert_eq!(k12, Rational::new(2, 1).unwrap());

    // التحقق من الجسر العكسي 5 -> 1 بثابت مقلوب 1/6
    let (p51, k51) = rebooted_engine.routing_matrix.query_route(5, 1).unwrap();
    assert_eq!(p51, &[5, 2, 1]);
    assert_eq!(k51, Rational::new(1, 6).unwrap());

    // 4. التحقق من تفكيك صك السيادة الكامل واسترجاعه سليماً من قطاع الـ Lineage
    let buf = rebooted_engine.storage.buffer();
    let lineage_start = rebooted_engine.storage.header.offset_lineage as usize;
    let prefix = UniversalRecordPrefix::from_bytes(
        &buf[lineage_start..lineage_start + RECORD_PREFIX_SIZE],
    )
    .expect("Axiom record prefix must be valid");
    assert_eq!(prefix.record_type, RECORD_TYPE_SOVEREIGN_AXIOM);

    let payload_start = lineage_start + RECORD_PREFIX_SIZE;
    let payload_end = payload_start + prefix.payload_len as usize;
    let receipt_bytes = &buf[payload_start..payload_end];

    let recovered_receipt = SovereignReceipt::from_bytes(receipt_bytes)
        .expect("Full SovereignReceipt must be faithfully reconstituted from DNA bytes");
    assert_eq!(recovered_receipt.law_id, "maxwell_curl_e");
    assert_eq!(recovered_receipt.domain, DomainTag::Electromagnetism);
    assert_eq!(recovered_receipt.dimension.len(), 4);
    assert!(recovered_receipt.verify_integrity());

    let _ = fs::remove_file(&dna_path);
}

#[test]
fn test_algebraic_independence_sieve_and_checked_dimension_spawn() {
    use aletheia_dna::error::DnaError;
    use aletheia_dna::spawner::verify_algebraic_independence;

    let test_dir = get_test_scratch_dir();
    let dna_path = test_dir.join("independence_sieve_test.dna");
    let _ = fs::remove_file(&dna_path);

    let storage = DnaStorageEngine::open_or_create(&dna_path, 3).unwrap();
    let mut engine = AutonomousEvolutionEngine::new(storage);

    // 1. الأساس القائم في فضاء Q^3: الكتلة (M)، الطول (L)، الزمن (T)
    let m = DimensionVector::from_integers(&[1, 0, 0]);
    let l = DimensionVector::from_integers(&[0, 1, 0]);
    let t = DimensionVector::from_integers(&[0, 0, 1]);
    let basis = vec![m, l, t];

    // 2. اختبار بعد مشتق (تابع خطياً): السرعة v = L / T = [0, 1, -1]
    let velocity = DimensionVector::from_integers(&[0, 1, -1]);
    assert!(!verify_algebraic_independence(&basis, &velocity));

    // اختبار القوة F = M L T^-2 = [1, 1, -2]
    let force = DimensionVector::from_integers(&[1, 1, -2]);
    assert!(!verify_algebraic_independence(&basis, &force));

    // محاولة الزرع في الـ DNA لبعد تابع يجب أن تفشل بخطأ غربال الاستقلال الجبري
    let dep_err = engine.spawn_dimension_checked("Velocity", &velocity, &basis);
    assert!(matches!(dep_err, Err(DnaError::AlgebraicDependenceError(_))));
    // الرتبة لم تتغير وظلت 3
    assert_eq!(engine.storage.header.dimension_rank(), 3);

    // 3. اختبار بعد مستقل أصيل: التيار الكهربائي I = [0, 0, 0, 1]
    let current = DimensionVector::from_integers(&[0, 0, 0, 1]);
    assert!(verify_algebraic_independence(&basis, &current));

    // زرع البعد المستقل في الـ DNA ينجح ويرقي الرتبة إلى 4
    let new_rank = engine
        .spawn_dimension_checked("ElectricCurrent", &current, &basis)
        .expect("Linearly independent dimension must be accepted by the sieve");
    assert_eq!(new_rank, 4);
    assert_eq!(engine.storage.header.dimension_rank(), 4);

    let _ = fs::remove_file(&dna_path);
}

#[test]
fn test_domain_materialization_with_descriptor_and_lineage_verification() {
    let test_dir = get_test_scratch_dir();
    let dna_path = test_dir.join("domain_materialize_test.dna");
    let _ = fs::remove_file(&dna_path);

    let storage = DnaStorageEngine::open_or_create(&dna_path, 3).unwrap();
    let mut engine = AutonomousEvolutionEngine::new(storage);

    // تدشين مجال مستقل "QuantumThermodynamics" (معرّف 0x0104، زمرة تناظر Lorentz 0x0002، وفضاء فرعي 0x0010)
    let domain_id = 0x0104;
    let group_id = 0x0002;
    let basis_id = 0x0010;
    let domain_name = "QuantumThermodynamics: Invariance SO(3) x U(1)";

    engine
        .materialize_domain_with_descriptor(domain_id, group_id, basis_id, domain_name)
        .expect("Materializing domain with descriptor must succeed");

    assert!(engine.storage.header.lineage_size > 0);

    // التحقق من كتابة السجل بدقة في الـ DNA
    let buf = engine.storage.buffer();
    let lineage_offset = engine.storage.header.offset_lineage as usize;
    let prefix = UniversalRecordPrefix::from_bytes(&buf[lineage_offset..lineage_offset + RECORD_PREFIX_SIZE])
        .expect("Domain record prefix must be valid");

    assert_eq!(prefix.record_type, aletheia_dna::record::RECORD_TYPE_DOMAIN_ENTRY);
    assert_eq!(prefix.status, aletheia_dna::record::RECORD_STATUS_ACTIVE);
    assert_eq!(prefix.domain_id, domain_id);
    assert_eq!(prefix.group_id, group_id);
    assert_eq!(prefix.basis_id, basis_id);
    assert_eq!(prefix.payload_len as usize, domain_name.len());

    let payload_start = lineage_offset + RECORD_PREFIX_SIZE;
    let payload_end = payload_start + prefix.payload_len as usize;
    let payload_str = std::str::from_utf8(&buf[payload_start..payload_end]).unwrap();
    assert_eq!(payload_str, domain_name);

    // اختبار استعلام مسار الجسر الفوري عبر query_bridge_path
    let (empty_path, zero_coupling) = engine.query_bridge_path(1, 99);
    assert!(empty_path.is_empty());
    assert!(zero_coupling.is_zero());

    let _ = fs::remove_file(&dna_path);
}

