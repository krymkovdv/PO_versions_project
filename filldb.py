# fill_realistic_data.py
from datetime import datetime, date, timezone, timedelta
from app.database import get_session
from app.models import Tractors, Component, ComponentParts, TelemetryComponents, Software, Software2ComponentPart
from sqlalchemy.orm import Session
import random

def fill_realistic_data():
    session: Session = next(get_session())

    try:
        print("Заполняем базу данных реалистичными данными...")

        # --- 1. Добавляем 50 тракторов ---
        tractors_data = []
        models_pool = ["K-7", "K-525", "K-742МСТ"]
        regions = ["RU-MOS", "RU-SPE", "RU-KRA", "RU-ROS", "RU-TAT", "RU-BAS"]
        dealers = ["АгроТехСервис", "Кировец-Центр", "СельхозМаш", "АгроИнвест", 
                   "ТехноАгро", "РосАгроМаш", "АгроКомплект", "Механизатор",
                   "АгроСервисПлюс", "ТракторныйДом"]
        serv_centers = ["СЦ-Москва", "СЦ-СПб", "СЦ-Краснодар", "СЦ-Ростов", 
                        "СЦ-Казань", "СЦ-Уфа", "СЦ-Воронеж", "СЦ-Саратов"]

        for i in range(1, 51):
            model = models_pool[(i - 1) % 3]
            tractor = Tractors(
                model=model,
                vin=f"VIN_{i:05d}",  # Обычные: VIN_00001...VIN_00050
                oh_hour=random.randint(50, 5000),
                last_activity=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 60)),
                assembly_date=datetime.now(timezone.utc) - timedelta(days=random.randint(30, 1500)),
                region=random.choice(regions),
                consumer=random.choice(dealers),
                serv_center=random.choice(serv_centers)
            )
            session.add(tractor)
            tractors_data.append(tractor)

        session.flush()
        print("✅ Добавлено 50 тракторов.")

        # --- 1.1. Добавляем 8 СИСТЕМНЫХ тракторов с НЕОБЫЧНЫМ VIN ---
        system_models = ["K-7", "K-5", "K-700", "K-744", "K-525", "K-530T", "K-730M", "K-714"]
        for i, model in enumerate(system_models, start=1):
            tractor = Tractors(
                model=model,
                vin=f"VIN_system_{i}",  # 🔹 НЕОБЫЧНЫЙ формат: VIN_system_1, VIN_system_2...
                oh_hour=random.randint(0, 100),
                last_activity=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 5)),
                assembly_date=datetime.now(timezone.utc) - timedelta(days=random.randint(30, 365)),
                region="RU-SYS",
                consumer="Системный трактор",
                serv_center="СЦ-Системный"
            )
            session.add(tractor)
            tractors_data.append(tractor)

        session.flush()
        print(f"✅ Добавлено {len(system_models)} системных тракторов (VIN_system_*).")

        # --- 2. Компоненты: ОДИН на ТИП ---
        components_data = [
            {"type": "ДВС", "model": "ДВС Weichai WP12", "number_of_parts": 3, "producer_comp": "Weichai"},
            {"type": "КПП", "model": "КПП-728", "number_of_parts": 2, "producer_comp": "Кировец"},
            {"type": "Гидравлика", "model": "Гидрораспределитель Р-80", "number_of_parts": 2, "producer_comp": "Гидросила"},
            {"type": "Рулевое", "model": "Рулевая колонка РК-7", "number_of_parts": 2, "producer_comp": "Кировец"},
            {"type": "Тормоза", "model": "Тормоз дисковый ТД-400", "number_of_parts": 4, "producer_comp": "Knorr-Bremse"},
            {"type": "БК", "model": "БК-Агро v2", "number_of_parts": 1, "producer_comp": "АгроЭлектроника"},
            {"type": "Подвеска", "model": "Амортизатор А-500", "number_of_parts": 2, "producer_comp": "Sachs"},
        ]

        components = []
        for c_data in components_data:
            comp = Component(**c_data)
            session.add(comp)
            components.append(comp)

        session.flush()
        print(f"✅ Добавлено {len(components)} компонентов (по 1 на тип).")

        # --- 3. ПО ---
        softwares_data = [
            {"path": "weichai_v1.0.bin", "name": "Weichai-ECU-1.0", "inner_name": "WECU10", 
             "release_date": datetime(2023, 1, 15), "description": "Базовая прошивка ДВС Weichai", 
             "producer": "Weichai", "is_actual": False, "status": "s"},
            {"path": "weichai_v2.0.bin", "name": "Weichai-ECU-2.0", "inner_name": "WECU20", 
             "release_date": datetime(2024, 1, 10), "description": "Major обновление экологии Euro-5", 
             "producer": "Weichai", "is_actual": True, "status": "s"},
            {"path": "kpp728_v1.0.bin", "name": "KPP-728-1.0", "inner_name": "K72810", 
             "release_date": datetime(2023, 5, 1), "description": "Базовая прошивка КПП-728", 
             "producer": "Кировец", "is_actual": False, "status": "s"},
            {"path": "kpp728_v2.0.bin", "name": "KPP-728-2.0", "inner_name": "K72820", 
             "release_date": datetime(2024, 2, 1), "description": "Major обновление КПП-728", 
             "producer": "Кировец", "is_actual": True, "status": "s"},
            {"path": "hydro_v1.0.bin", "name": "HydroCtrl-1.0", "inner_name": "HC10", 
             "release_date": datetime(2023, 3, 15), "description": "Базовая прошивка гидравлики", 
             "producer": "Гидросила", "is_actual": False, "status": "s"},
            {"path": "hydro_v2.0.bin", "name": "HydroCtrl-2.0", "inner_name": "HC20", 
             "release_date": datetime(2024, 4, 1), "description": "Major обновление гидравлики", 
             "producer": "Гидросила", "is_actual": True, "status": "s"},
            {"path": "steer_v1.0.bin", "name": "SteerCtrl-1.0", "inner_name": "SC10", 
             "release_date": datetime(2023, 6, 1), "description": "Базовая прошивка рулевого", 
             "producer": "Кировец", "is_actual": True, "status": "s"},
            {"path": "brake_v1.0.bin", "name": "BrakeCtrl-1.0", "inner_name": "BC10", 
             "release_date": datetime(2023, 7, 1), "description": "Базовая прошивка тормозов", 
             "producer": "Knorr-Bremse", "is_actual": False, "status": "s"},
            {"path": "brake_v2.0.bin", "name": "BrakeCtrl-2.0", "inner_name": "BC20", 
             "release_date": datetime(2024, 3, 15), "description": "Major обновление тормозов", 
             "producer": "Knorr-Bremse", "is_actual": True, "status": "s"},
            {"path": "bk_v1.5.bin", "name": "BK-Agro-1.5", "inner_name": "BKA15", 
             "release_date": datetime(2024, 1, 1), "description": "Minor обновление БК", 
             "producer": "АгроЭлектроника", "is_actual": False, "status": "t"},
            {"path": "bk_v2.0.bin", "name": "BK-Agro-2.0", "inner_name": "BKA20", 
             "release_date": datetime(2024, 5, 1), "description": "Major обновление БК", 
             "producer": "АгроЭлектроника", "is_actual": True, "status": "s"},
            {"path": "susp_v1.0.bin", "name": "SuspCtrl-1.0", "inner_name": "SUSP10", 
             "release_date": datetime(2023, 9, 1), "description": "Базовая прошивка подвески", 
             "producer": "Sachs", "is_actual": True, "status": "o"},
        ]

        softwares = []
        for s_data in softwares_data:
            sw = Software(**s_data)
            session.add(sw)
            softwares.append(sw)

        session.flush()
        print(f"✅ Добавлено {len(softwares)} ПО.")

        # --- 4. Детали компонентов ---
        component_parts = []
        for comp in components:
            for part_num in range(comp.number_of_parts):
                part_types = {
                    "ДВС": ["ЭБУ", "ТНВД", "Форсунки"],
                    "КПП": ["Основной блок", "Доп. модуль"],
                    "Гидравлика": ["Клапан", "Датчик"],
                    "Рулевое": ["Колонка", "Цилиндр"],
                    "Тормоза": ["Диск", "Колодка", "Суппорт", "Датчик"],
                    "БК": ["Основной модуль"],
                    "Подвеска": ["Амортизатор", "Датчик положения"],
                }
                types = part_types.get(comp.type, [f"Часть_{part_num+1}"])
                part_type = types[part_num] if part_num < len(types) else f"Часть_{part_num+1}"
                part = ComponentParts(component=comp.id, part_type=part_type)
                session.add(part)
                component_parts.append(part)

        session.flush()
        print(f"✅ Добавлено {len(component_parts)} деталей компонентов.")

        # --- 5. Связи ПО <-> Детали ---
        sw_map = {sw.name: sw for sw in softwares}
        comp_sw_mapping = {
            "ДВС Weichai WP12": ("Weichai-ECU-1.0", "Weichai-ECU-2.0"),
            "КПП-728": ("KPP-728-1.0", "KPP-728-2.0"),
            "Гидрораспределитель Р-80": ("HydroCtrl-1.0", "HydroCtrl-2.0"),
            "Рулевая колонка РК-7": ("SteerCtrl-1.0", "SteerCtrl-1.0"),
            "Тормоз дисковый ТД-400": ("BrakeCtrl-1.0", "BrakeCtrl-2.0"),
            "БК-Агро v2": ("BK-Agro-1.5", "BK-Agro-2.0"),
            "Амортизатор А-500": ("SuspCtrl-1.0", "SuspCtrl-1.0"),
        }
        status_pool = ['s', 't', 'o']

        for comp in components:
            comp_parts = [p for p in component_parts if p.component == comp.id]
            sw_names = comp_sw_mapping.get(comp.model, (None, None))
            if sw_names[0]:
                current_sw = sw_map.get(sw_names[0])
                if current_sw:
                    for idx, part in enumerate(comp_parts):
                        status = status_pool[idx % len(status_pool)]
                        link = Software2ComponentPart(
                            component_part_id=part.id,
                            software_id=current_sw.id,
                            is_actual=sw_names[0] != sw_names[1],
                            status=status,
                            date_change_actual=date.today() if current_sw.is_actual else None,
                            previous_sw_version=None,
                            not_recom=None
                        )
                        session.add(link)

        session.flush()
        print("✅ Добавлены связи ПО с деталями компонентов.")

        # --- 6. Телеметрия: ТОЛЬКО для обычных тракторов (первые 50) ---
        telemetry_count = 0
        for i, tractor in enumerate(tractors_data[:50]):  # Исключаем системные (индексы 50-57)
            for comp in components:
                sw_names = comp_sw_mapping.get(comp.model, (None, None))
                if not sw_names[0]:
                    continue

                if i < 15:
                    current_sw_name = sw_names[0]
                    recommend_sw_name = sw_names[1] if sw_names[1] != sw_names[0] else sw_names[0]
                elif i < 30:
                    if "Weichai" in comp.model:
                        current_sw_name = "Weichai-ECU-1.2" if any("Weichai-ECU-1.2" in s.name for s in softwares) else sw_names[0]
                        recommend_sw_name = sw_names[1]
                    elif "Гидро" in comp.model:
                        current_sw_name = "HydroCtrl-1.3" if any("HydroCtrl-1.3" in s.name for s in softwares) else sw_names[0]
                        recommend_sw_name = sw_names[1]
                    elif "БК" in comp.model:
                        current_sw_name, recommend_sw_name = "BK-Agro-1.5", "BK-Agro-2.0"
                    else:
                        current_sw_name, recommend_sw_name = sw_names
                else:
                    current_sw_name = sw_names[1] if sw_names[1] else sw_names[0]
                    recommend_sw_name = current_sw_name

                current_sw = sw_map.get(current_sw_name)
                recommend_sw = sw_map.get(recommend_sw_name) if recommend_sw_name else current_sw

                if not current_sw:
                    continue

                tc = TelemetryComponents(
                    tractor=tractor.id,
                    component=comp.id,
                    mounting_date=date.today() - timedelta(days=random.randint(30, 730)),
                    current_sw_version=current_sw.id,
                    recommend_sw_version=recommend_sw.id if recommend_sw else current_sw.id,
                    comp_ser_num=f"SER_{tractor.id}_{comp.id}_{random.randint(10000, 99999)}",
                    time_rec=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30))
                )
                session.add(tc)
                telemetry_count += 1

                if i < 3:
                    print(f"  - {tractor.vin} ({tractor.model}) -> {comp.type}: {comp.model}")

        print(f"✅ Добавлено {telemetry_count} записей телеметрии.")

        # --- 7. Обновляем ПО для некоторых тракторов ---
        for i, tractor in enumerate(tractors_data[:10]):
            for sw in softwares[:5]:
                sw.tractor_id = tractor.id
                sw.tractor_model = tractor.model
                sw.tractor_vin = tractor.vin

        session.commit()
        
        print("\n" + "="*70)
        print("✅ РЕАЛИСТИЧНЫЕ ДАННЫЕ УСПЕШНО ДОБАВЛЕНЫ!")
        print("="*70)
        print(f"\n📊 Итоговая статистика:")
        print(f"   • Тракторов: {len(tractors_data)} (50 обычных + 8 системных)")
        print(f"   • Компонентов: {len(components)} (по 1 на тип)")
        print(f"   • ПО: {len(softwares)}")
        print(f"   • Деталей: {len(component_parts)}")
        print(f"   • Связей ПО-компоненты: {session.query(Software2ComponentPart).count()}")
        print(f"   • Записей телеметрии: {session.query(TelemetryComponents).count()}")
        
        print(f"\n🔧 Компоненты (по 1 на тип):")
        for comp in components:
            print(f"   • {comp.type}: {comp.model} ({comp.producer_comp})")
        
        print(f"\n📈 Группы тракторов:")
        print("   • VIN_00001-00050: Обычные тракторы (с телеметрией)")
        print("   • VIN_system_1-8: СИСТЕМНЫЕ (без телеметрии, необычный VIN)")
        
        print(f"\n🔰 Системные тракторы (нулевая телеметрия):")
        for i, model in enumerate(system_models, start=1):
            print(f"   • VIN_system_{i} ({model})")
        
        print(f"\n🔍 Доступные фильтры для тестирования:")
        print("   • trac_model: K-7, K-5, K-525, K-700, K-744, K-530T, K-730M, K-714, K-742МСТ")
        print("   • type_comp: ДВС, КПП, Гидравлика, Рулевое, Тормоза, БК, Подвеска")
        print("   • query: Поиск по VIN (VIN_00001...VIN_00050, VIN_system_1...VIN_system_8)")
        print("   • region: RU-SYS — для фильтрации системных тракторов")
        print("="*70)

    except Exception as e:
        session.rollback()
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    fill_realistic_data()