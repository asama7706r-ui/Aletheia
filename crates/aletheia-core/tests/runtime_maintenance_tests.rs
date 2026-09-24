use aletheia_algebra::Rational;
use aletheia_core::runtime::AletheiaRuntime;
use aletheia_lattice::DimensionVector;
use aletheia_yoneda::{GraphMutationEvent, LatentShadow, QuarantineRecord};

#[test]
fn test_runtime_maintenance_dormancy_and_tarjan_immunity() {
    let mut runtime = AletheiaRuntime::boot_or_create(None, 3).expect("Boot failed");

    // 1. إنشاء فرضية عادية غير متصلة بجسر
    let dim_stagnant = DimensionVector::from_integers(&[1, 0, 0]);
    let shadow_stagnant = LatentShadow::new(
        vec!["stagnant_law_1".to_string()],
        dim_stagnant.clone(),
        0,
        Rational::one(),
        Vec::new(),
    );
    let mut rec_stagnant = QuarantineRecord::new(shadow_stagnant);
    rec_stagnant.saturation_age = 5;
    let id_stagnant = rec_stagnant.record_id;
    runtime.admit_to_quarantine(rec_stagnant);

    // 2. إنشاء فرضية تمثل جسراً طوبولوجياً حرجاً بين مجالين
    let dim_bridge = DimensionVector::from_integers(&[0, 1, 0]);
    // نسجل جسراً سيادياً طوبولوجياً يربط بين المجال 1 والمجال 2
    let _ = runtime
        .materialize_bridge_with_dimension(
            1,
            2,
            dim_bridge.clone(),
            Rational::one(),
            Rational::one(),
        )
        .expect("Materialize bridge failed");

    let shadow_bridge = LatentShadow::new(
        vec!["bridge_law_a".to_string(), "bridge_law_b".to_string()],
        dim_bridge.clone(),
        0,
        Rational::one(),
        Vec::new(),
    );
    let mut rec_bridge = QuarantineRecord::new(shadow_bridge);
    rec_bridge.saturation_age = 5;
    let id_bridge = rec_bridge.record_id;
    runtime.admit_to_quarantine(rec_bridge);

    assert_eq!(runtime.quarantine.len(), 2);

    // 3. تشغيل دورة الصيانة بحد أقصى للشيخوخة = 5
    // تزداد أعمارهما لتصبح 6، فتتجاوز حد الشيخوخة 5
    let report = runtime.maintenance_cycle(Some(5));
    assert_eq!(report.total_quarantined, 2);
    // الفرضية العادية أصبحت خاملة لأنها ليست جسراً
    assert_eq!(report.newly_dormant, 1);
    // الفرضية المحصنة كجسر طوبولوجي ظلت نشطة واكتسبت حصانة تارجان
    assert!(report.protected_bridge_records >= 1);

    let rec_stagnant_after = runtime.quarantine.get(&id_stagnant).unwrap();
    let rec_bridge_after = runtime.quarantine.get(&id_bridge).unwrap();

    assert!(
        rec_stagnant_after.is_dormant,
        "الفرضية الراكدة يجب أن تكون خاملة"
    );
    assert!(
        !rec_bridge_after.is_dormant,
        "فرضية الجسر الطوبولوجي يجب أن تحتفظ بحصانتها وتظل نشطة"
    );

    // 4. اختبار البعث الحتمي عند حدوث تحول معرفي (توسع بعدي)
    // نطلق حدث توسع بعدي في البعد 2
    let event = GraphMutationEvent::DimensionalExpansion {
        added_dimension_index: 2,
    };
    let resurrected = runtime.trigger_resurrection_on_mutation(&event);

    assert!(!resurrected.is_empty());
    assert!(resurrected.contains(&id_stagnant));

    let rec_stagnant_resurrected = runtime.quarantine.get(&id_stagnant).unwrap();
    assert!(
        !rec_stagnant_resurrected.is_dormant,
        "سقط ختم الخمول وعادت الفرضية للحياة بعد التوسع البعدي"
    );
}
