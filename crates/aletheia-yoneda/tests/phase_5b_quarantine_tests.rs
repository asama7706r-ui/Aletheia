use aletheia_algebra::{Rational, VariableId};
use aletheia_lattice::DimensionVector;
use aletheia_yoneda::*;
use std::fs;

fn create_dummy_record(id_byte: u8, dim: DimensionVector) -> QuarantineRecord {
    let mut shadow_id = [0u8; 32];
    shadow_id[0] = id_byte;
    let shadow = LatentShadow {
        shadow_id,
        origin_law_ids: vec![format!("law_{}", id_byte)],
        dim_deficit: dim,
        tensorial_rank: 0,
        dof: Rational::one(),
        spectral_audit: DiagnosticVector::default(),
        coupling_carrier: None,
        target_classes: Vec::new(),
        macaulay_ceiling: 5,
    };
    QuarantineRecord::new(shadow)
}

#[test]
fn test_quarantine_buffer_isolation_and_magic_header() {
    let mut buffer = LatentBuffer::new();
    let dim = DimensionVector::from_integers(&[1, 2, -2]);
    let record = create_dummy_record(1, dim);
    let record_id = record.record_id;

    buffer.admit(record);
    assert_eq!(buffer.len(), 1);
    assert!(buffer.get(&record_id).is_some());

    // حفظ في مسار ملف مؤقت
    let temp_dir = std::env::temp_dir();
    let file_path = temp_dir.join("test_aletheia_quarantine.bin");

    buffer.save_to_file(&file_path).unwrap();

    // التحقق الصارم من أول 8 بايتات: يجب أن تطابق ALETH_Q1
    let raw_bytes = fs::read(&file_path).unwrap();
    assert!(raw_bytes.len() >= 8);
    assert_eq!(&raw_bytes[0..8], MAGIC_HEADER);

    // استرجاع السجلات من الملف والتحقق من سلامة dof والصفة غير السيادية
    let mut loaded_buffer = LatentBuffer::new();
    loaded_buffer.load_from_file(&file_path).unwrap();
    assert_eq!(loaded_buffer.len(), 1);

    let loaded_record = loaded_buffer.get(&record_id).unwrap();
    assert_eq!(loaded_record.authority, AUTHORITY_NON_SOVEREIGN);
    assert_eq!(loaded_record.remaining_dof, Rational::one());
    assert!(!loaded_record.is_dormant);

    // التحقق من فحص الترويسة المزورة
    let bad_file_path = temp_dir.join("test_bad_quarantine.bin");
    fs::write(&bad_file_path, b"BAD_HEAD_DATA").unwrap();
    let mut bad_buffer = LatentBuffer::new();
    assert!(bad_buffer.load_from_file(&bad_file_path).is_err());

    // تنظيف
    let _ = fs::remove_file(file_path);
    let _ = fs::remove_file(bad_file_path);
}

#[test]
fn test_correlation_hypergraph_indexing() {
    let mut hypergraph = CorrelationHypergraph::new();

    let x = VariableId(10);
    let y = VariableId(20);

    let dim_energy = DimensionVector::from_integers(&[1, 2, -2]);
    let dim_mass = DimensionVector::from_integers(&[1, 0, 0]);

    // الفرضية A: مجهول x وعجز طاقة [M L^2 T^-2]
    let rec_a = create_dummy_record(1, dim_energy.clone());
    let id_a = rec_a.record_id;
    hypergraph.insert_record(rec_a);
    hypergraph.link_shared_unknown(id_a, x);

    // الفرضية B: مجهول x وعجز كتلة [M]
    let rec_b = create_dummy_record(2, dim_mass);
    let id_b = rec_b.record_id;
    hypergraph.insert_record(rec_b);
    hypergraph.link_shared_unknown(id_b, x);

    // الفرضية C: مجهول y وعجز طاقة [M L^2 T^-2]
    let rec_c = create_dummy_record(3, dim_energy.clone());
    let id_c = rec_c.record_id;
    hypergraph.insert_record(rec_c);
    hypergraph.link_shared_unknown(id_c, y);

    // 1. فحص حافة المجهول المشترك x (تضم A و B)
    let hedge_x_id = HyperedgeKind::SharedUnknown(x).compute_id();
    let hedge_x = hypergraph.hyperedges.get(&hedge_x_id).unwrap();
    assert_eq!(hedge_x.members.len(), 2);
    assert!(hedge_x.members.contains(&id_a));
    assert!(hedge_x.members.contains(&id_b));

    // 2. فحص حافة العجز البعدي المتطابق للطاقة (تضم A و C)
    let hedge_dim_id = HyperedgeKind::HomologousDeficit(Box::new(dim_energy)).compute_id();
    let hedge_dim = hypergraph.hyperedges.get(&hedge_dim_id).unwrap();
    assert_eq!(hedge_dim.members.len(), 2);
    assert!(hedge_dim.members.contains(&id_a));
    assert!(hedge_dim.members.contains(&id_c));

    // 3. التحقق من استخراج مرشحي الدمج
    let candidates = hypergraph.consolidation_candidates();
    assert!(candidates.len() >= 2);
}

#[test]
fn test_neutrino_consolidation_rank_jump() {
    let mut hypergraph = CorrelationHypergraph::new();

    // محاكاة ظاهرة تحلل بيتا:
    // فرضية 1 (تحلل بيتا): عجز سرعة v = [L T^-1]
    let dim1 = DimensionVector::from_integers(&[0, 1, -1]);
    let rec1 = create_dummy_record(1, dim1);
    let id1 = rec1.record_id;
    hypergraph.insert_record(rec1);

    // فرضية 2 (ارتداد النواة): عجز سرعة v = [L T^-1]
    let dim2 = DimensionVector::from_integers(&[0, 1, -1]);
    let rec2 = create_dummy_record(2, dim2);
    let id2 = rec2.record_id;
    hypergraph.insert_record(rec2);

    let noether_key = "LeptonConservation";
    hypergraph.link_noether_invariant(id1, noether_key);
    hypergraph.link_noether_invariant(id2, noether_key);

    let hedge_id = HyperedgeKind::NoetherInvariant(noether_key.to_string()).compute_id();

    // القواعد المرشحة لحل العجز المشترك: قاعدة السرعة v = [L T^-1]
    let candidate_v = DimensionVector::from_integers(&[0, 1, -1]);

    // تشغيل دورة دمج النيوترينو
    let result = NeutrinoConsolidator::consolidate_hyperedge(
        &mut hypergraph,
        &hedge_id,
        &[candidate_v],
    ).unwrap();

    // قفزة الرتبة تؤدي إلى dof -> 0 وتحرير الفرضيتين معاً
    assert!(result.is_resolved);
    assert_eq!(result.remaining_dof, Rational::zero());
    assert_eq!(result.freed_records.len(), 2);
    assert!(result.freed_records.contains(&id1));
    assert!(result.freed_records.contains(&id2));

    // التحقق من تحديث السجلات داخل المخطط
    assert_eq!(hypergraph.records.get(&id1).unwrap().remaining_dof, Rational::zero());
    assert_eq!(hypergraph.records.get(&id2).unwrap().remaining_dof, Rational::zero());
}

#[test]
fn test_tarjan_bridge_immunity() {
    // بناء رسم بياني معرفي:
    // المجموعة الأولى (0, 1, 2) كـ مثلث متصل
    // المجموعة الثانية (3, 4, 5) كـ مثلث متصل
    // الحافة بين 2 و 3 هي الجسر الوحيد الرابط بين المجموعتين
    let mut graph = KnowledgeGraph::new(6);

    // مثلث 1
    graph.add_edge(0, 1);
    graph.add_edge(1, 2);
    graph.add_edge(2, 0);

    // الجسر الرابط بين المجالين
    let bridge_edge = graph.add_edge(2, 3);

    // مثلث 2
    graph.add_edge(3, 4);
    graph.add_edge(4, 5);
    graph.add_edge(5, 3);

    let bridges = TarjanBridgeDetector::find_all_bridges(&graph);
    assert_eq!(bridges.len(), 1);
    assert!(bridges.contains(&bridge_edge));

    // التحقق من منح حصانة الجسر
    assert!(TarjanBridgeDetector::has_bridge_immunity(&graph, bridge_edge));
    // الحواف الداخلية للمثلث لا تملك حصانة لأن لها مسارات بديلة
    assert!(!TarjanBridgeDetector::has_bridge_immunity(&graph, 0));
}

#[test]
fn test_transient_dormancy_and_resurrection_on_paradigm_shift() {
    let mut buffer = LatentBuffer::new();
    let mut hypergraph = CorrelationHypergraph::new();

    let dim = DimensionVector::from_integers(&[1, 0, 0]);

    // فرضية راكدة عادية
    let mut rec_stagnant = create_dummy_record(1, dim.clone());
    rec_stagnant.saturation_age = 15; // تجاوزت الحد الأقصى 10
    let id_stagnant = rec_stagnant.record_id;
    buffer.admit(rec_stagnant);

    // فرضية جسر محصنة طوبولوجياً
    let mut rec_bridge = create_dummy_record(2, dim);
    rec_bridge.saturation_age = 20;
    let id_bridge = rec_bridge.record_id;
    buffer.admit(rec_bridge);

    // تطبيق الخمول مع حماية الجسر
    let protected = vec![id_bridge];
    let newly_dormant = DormancyManager::apply_transient_dormancy(&mut buffer, 10, &protected);
    assert_eq!(newly_dormant, 1);

    // الفرضية العادية أصبحت خاملة، والفرضية المحصنة ظلت نشطة
    assert!(buffer.get(&id_stagnant).unwrap().is_dormant);
    assert!(!buffer.get(&id_bridge).unwrap().is_dormant);

    // حدث تحول معرفي: توسع بعدي في الشبكة
    let event = GraphMutationEvent::DimensionalExpansion { added_dimension_index: 2 };
    let resurrected = DormancyManager::resurrect_on_mutation(&mut buffer, &mut hypergraph, &event);

    assert_eq!(resurrected.len(), 1);
    assert_eq!(resurrected[0], id_stagnant);
    // سقط ختم الخمول وعادت للنشاط
    assert!(!buffer.get(&id_stagnant).unwrap().is_dormant);
}
