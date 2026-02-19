# fill_realistic_data.py
from datetime import datetime, date, timezone, timedelta
from app.database import get_session
from app.models import Tractors, Component, ComponentParts, TelemetryComponents, Software, Software2ComponentPart
from sqlalchemy.orm import Session
import random

def fill_realistic_data():
    # Получаем сессию
    session: Session = next(get_session())

    try:
        print("Заполняем базу данных реалистичными данными...")

        # --- 1. Добавляем 30 тракторов ---
        tractors_data = []
        models_pool = ["K-7", "K-525", "K-742МСТ"]
        
        # Создаем тракторы
        for i in range(1, 31):
            tractor = Tractors(
                model=models_pool[(i - 1) % 3],  # K-7, K-525, K-742МСТ по кругу
                vin=f"REALVIN{i:03d}",
                oh_hour=100 * i,
                last_activity=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30)),
                assembly_date=datetime.now(timezone.utc) - timedelta(days=random.randint(30, 730)),
                region="RU-MOS" if i <= 10 else "RU-SPE" if i <= 20 else "RU-KRA",
                consumer=f"Dealer {chr(64 + (i % 26 + 1))}",
                serv_center=f"Center {(i % 5) + 1}"
            )
            session.add(tractor)
            tractors_data.append(tractor)

        session.flush()  # Чтобы получить id тракторов
        print("✅ Добавлено 30 новых тракторов.")

        # --- 2. Добавляем компоненты ---
        components_data = [
            {"type": "engine", "model": "Engine-V1", "number_of_parts": 2, "producer_comp": "Producer A"},
            {"type": "transmission", "model": "Trans-X1", "number_of_parts": 2, "producer_comp": "Producer B"},
            {"type": "hydraulics", "model": "Hydra-Y1", "number_of_parts": 1, "producer_comp": "Producer C"},
            {"type": "brakes", "model": "Brake-Z1", "number_of_parts": 2, "producer_comp": "Producer D"},
            {"type": "suspension", "model": "Susp-X1", "number_of_parts": 2, "producer_comp": "Producer E"}
        ]

        components = []
        for c_data in components_data:
            comp = Component(**c_data)
            session.add(comp)
            components.append(comp)

        session.flush()
        print("✅ Добавлено 5 компонентов.")

        # --- 3. Добавляем ПО с учетом новых полей ---
        softwares_data = [
            # ПО для двигателя
            {"path": "engine_v1.bin", "name": "Engine-v1", "inner_name": "EngV1", 
             "release_date": datetime(2024, 1, 1), "description": "Initial engine SW", 
             "producer": "EngineSoft Inc", "is_actual": True, "status": "stable"},
            {"path": "engine_v2.bin", "name": "Engine-v2", "inner_name": "EngV2", 
             "release_date": datetime(2024, 5, 1), "description": "Major engine update", 
             "producer": "EngineSoft Inc", "is_actual": True, "status": "stable"},
            # ПО для трансмиссии
            {"path": "trans_v1.bin", "name": "Trans-v1", "inner_name": "TransV1", 
             "release_date": datetime(2024, 2, 1), "description": "Initial trans SW", 
             "producer": "TransSoft Co", "is_actual": True, "status": "stable"},
            {"path": "trans_v2.bin", "name": "Trans-v2", "inner_name": "TransV2", 
             "release_date": datetime(2024, 6, 1), "description": "Major trans update", 
             "producer": "TransSoft Co", "is_actual": True, "status": "stable"},
            # ПО для гидравлики
            {"path": "hydra_v1.bin", "name": "Hydra-v1", "inner_name": "HydraV1", 
             "release_date": datetime(2024, 3, 1), "description": "Initial hydra SW", 
             "producer": "HydraSystems", "is_actual": True, "status": "stable"},
            {"path": "hydra_v2.bin", "name": "Hydra-v2", "inner_name": "HydraV2", 
             "release_date": datetime(2024, 7, 1), "description": "Major hydra update", 
             "producer": "HydraSystems", "is_actual": True, "status": "stable"},
            {"path": "hydra_v3.bin", "name": "Hydra-v3", "inner_name": "HydraV3", 
             "release_date": datetime(2024, 9, 1), "description": "Major hydra update v3", 
             "producer": "HydraSystems", "is_actual": True, "status": "beta"},
            {"path": "hydra_v4.bin", "name": "Hydra-v4", "inner_name": "HydraV4", 
             "release_date": datetime(2024, 11, 1), "description": "Major hydra update v4", 
             "producer": "HydraSystems", "is_actual": True, "status": "beta"},
            # ПО для подвески
            {"path": "susp_v1.bin", "name": "Susp-v1", "inner_name": "SuspV1", 
             "release_date": datetime(2024, 4, 1), "description": "Initial suspension SW", 
             "producer": "SuspTech", "is_actual": True, "status": "stable"},
            {"path": "susp_v2.bin", "name": "Susp-v2", "inner_name": "SuspV2", 
             "release_date": datetime(2024, 8, 1), "description": "Major suspension update", 
             "producer": "SuspTech", "is_actual": True, "status": "stable"},
        ]

        softwares = []
        for s_data in softwares_data:
            sw = Software(**s_data)
            session.add(sw)
            softwares.append(sw)

        session.flush()
        print("✅ Добавлено 10 ПО.")

        # --- 4. Добавляем детали компонентов ---
        component_parts = []
        for comp in components:
            # Создаем основные детали для каждого компонента
            for part_num in range(comp.number_of_parts):
                part_type = "main" if part_num == 0 else f"aux_{part_num}"
                part = ComponentParts(component=comp.id, part_type=part_type)
                session.add(part)
                component_parts.append(part)

        session.flush()
        print(f"✅ Добавлено {len(component_parts)} деталей компонентов.")

        # --- 5. Создаём связи ПО <-> Детали компонентов ---
        sw_map = {sw.name: sw for sw in softwares}

        # Создаем связи для всех типов компонентов
        for comp in components:
            # Находим все детали для этого компонента
            comp_parts = [p for p in component_parts if p.component == comp.id]
            
            for part in comp_parts:
                # Выбираем соответствующее ПО для компонента
                if comp.type == "engine":
                    current_sw = sw_map.get("Engine-v1")
                    is_actual = True  # Это major обновление
                elif comp.type == "transmission":
                    current_sw = sw_map.get("Trans-v1")
                    is_actual = True
                elif comp.type == "hydraulics":
                    current_sw = sw_map.get("Hydra-v1")
                    is_actual = True
                elif comp.type == "suspension":
                    current_sw = sw_map.get("Susp-v1")
                    is_actual = True
                elif comp.type == "brakes":
                    # Для brakes нет ПО
                    continue
                else:
                    continue

                if current_sw:
                    link = Software2ComponentPart(
                        component_part_id=part.id,
                        software_id=current_sw.id,
                        is_actual=is_actual,  # Флаг Major обновления
                        status='s',
                        date_change_actual=date.today() if is_actual else None,
                        previous_sw_version=None,
                        not_recom=None
                    )
                    session.add(link)

        session.flush()
        print("✅ Добавлены связи ПО с деталями компонентов.")

        # --- 6. Создаём телеметрию для тракторов ---
        for i, tractor in enumerate(tractors_data):
            for comp in components:
                # Пропускаем brakes (нет ПО)
                if comp.type == "brakes":
                    continue

                # Определяем текущее и рекомендуемое ПО в зависимости от группы трактора
                if i < 10:  # Трактора 0-9 (REALVIN001 - REALVIN010) -> Требуют MAJOR обновления
                    if comp.type == "engine":
                        current_sw_name = "Engine-v1"
                        recommend_sw_name = "Engine-v2"
                    elif comp.type == "transmission":
                        current_sw_name = "Trans-v1"
                        recommend_sw_name = "Trans-v2"
                    elif comp.type == "hydraulics":
                        current_sw_name = "Hydra-v1"
                        recommend_sw_name = "Hydra-v2"
                    elif comp.type == "suspension":
                        current_sw_name = "Susp-v1"
                        recommend_sw_name = "Susp-v2"
                    else:
                        continue
                    
                    print(f"  - Трактор {tractor.vin} (#{i+1}) -> {comp.type}: {current_sw_name} -> {recommend_sw_name} (MAJOR)")

                elif i < 20:  # Трактора 10-19 (REALVIN011 - REALVIN020) -> Требуют MINOR обновления
                    if comp.type == "engine":
                        current_sw_name = "Engine-v2"
                        recommend_sw_name = "Engine-v2"  # minor - та же версия
                    elif comp.type == "transmission":
                        current_sw_name = "Trans-v2"
                        recommend_sw_name = "Trans-v2"
                    elif comp.type == "hydraulics":
                        current_sw_name = "Hydra-v2"
                        recommend_sw_name = "Hydra-v3"
                    elif comp.type == "suspension":
                        current_sw_name = "Susp-v2"
                        recommend_sw_name = "Susp-v2"
                    else:
                        continue
                    
                    print(f"  - Трактор {tractor.vin} (#{i+1}) -> {comp.type}: {current_sw_name} -> {recommend_sw_name} (MINOR)")

                else:  # Трактора 20-29 (REALVIN021 - REALVIN030) -> Уже обновлены
                    if comp.type == "engine":
                        current_sw_name = "Engine-v2"
                        recommend_sw_name = "Engine-v2"
                    elif comp.type == "transmission":
                        current_sw_name = "Trans-v2"
                        recommend_sw_name = "Trans-v2"
                    elif comp.type == "hydraulics":
                        current_sw_name = "Hydra-v3"
                        recommend_sw_name = "Hydra-v4"
                    elif comp.type == "suspension":
                        current_sw_name = "Susp-v2"
                        recommend_sw_name = "Susp-v2"
                    else:
                        continue
                    
                    print(f"  - Трактор {tractor.vin} (#{i+1}) -> {comp.type}: {current_sw_name} -> {recommend_sw_name} (UP-TO-DATE)")

                current_sw = sw_map.get(current_sw_name)
                recommend_sw = sw_map.get(recommend_sw_name)

                if not current_sw:
                    print(f"⚠️ ПО {current_sw_name} не найдено для трактора {tractor.vin}")
                    continue

                # Создаём запись телеметрии
                tc = TelemetryComponents(
                    tractor=tractor.id,
                    component=comp.id,
                    mounting_date=date.today() - timedelta(days=random.randint(30, 365)),
                    current_sw_version=current_sw.id,
                    recommend_sw_version=recommend_sw.id if recommend_sw else current_sw.id,
                    comp_ser_num=f"SERIAL_{tractor.id}_{comp.id}_{random.randint(1000, 9999)}",
                    time_rec=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30))
                )
                session.add(tc)

        # --- 7. Обновляем информацию о ПО для некоторых тракторов (новые поля) ---
        for i, tractor in enumerate(tractors_data[:5]):  # Только для первых 5 тракторов
            for sw in softwares[:3]:  # Только для первого ПО
                sw.tractor_id = tractor.id
                sw.tractor_model = tractor.model
                sw.tractor_vin = tractor.vin

        session.commit()
        
        print("\n" + "="*50)
        print("✅ РЕАЛИСТИЧНЫЕ ДАННЫЕ УСПЕШНО ДОБАВЛЕНЫ!")
        print("="*50)
        print("\nСтатистика:")
        print(f"- Тракторов: {len(tractors_data)}")
        print(f"- Компонентов: {len(components)}")
        print(f"- ПО: {len(softwares)}")
        print(f"- Деталей компонентов: {len(component_parts)}")
        print("\nГруппы тракторов:")
        print("- REALVIN001 - REALVIN010: Требуют MAJOR обновления")
        print("- REALVIN011 - REALVIN020: Требуют MINOR обновления")
        print("- REALVIN021 - REALVIN030: Обновлены (up-to-date)")
        print("="*50)

    except Exception as e:
        session.rollback()
        print(f"❌ Ошибка при заполнении базы данных: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    fill_realistic_data()