# fill_realistic_data.py
from datetime import datetime, date
from app.database import get_session
from app.models import Tractors, Component, ComponentParts, TelemetryComponents, Software, Software2ComponentPart
from sqlalchemy.orm import Session

def fill_realistic_data():
    # Получаем сессию
    session: Session = next(get_session())

    try:
        print("Заполняем базу данных реалистичными данными...")

        # --- 1. Добавляем 30 тракторов ---
        tractors_data = []
        models_pool = ["K-7", "K-525", "K-742МСТ"]
        for i in range(1, 31):
            tractor = Tractors(
                model=models_pool[(i - 1) % 3],  # K-7, K-525, K-742МСТ по кругу
                vin=f"REALVIN{i:03d}",
                oh_hour=100 * i,
                last_activity=datetime(2024, 11, 15) if i % 2 == 0 else datetime(2024, 12, 15),
                assembly_date=datetime(2024, 1, i % 12 + 1),
                region="RU-MOS" if i <= 10 else "RU-SPE" if i <= 20 else "RU-KRA",
                consumer=f"Dealer {chr(64 + (i % 26 + 1))}",
                serv_center=f"Center {(i % 5) + 1}"
            )
            session.add(tractor)
            tractors_data.append(tractor)

        session.commit()
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

        session.commit()
        print("✅ Добавлено 5 компонентов.")

        # --- 3. Добавляем детали компонентов ---
        component_parts = []
        for tractor in tractors_data[:15]:  # Пример: первые 15 тракторов
            for comp in components:
                part_main = ComponentParts(component=comp.id, part_type="main")
                part_aux = ComponentParts(component=comp.id, part_type="aux")
                session.add(part_main)
                session.add(part_aux)
                component_parts.append(part_main)
                component_parts.append(part_aux)

        session.commit()
        print("✅ Добавлено деталей компонентов.")

        # --- 4. Добавляем ПО ---
        softwares_data = [
            {"path": "engine_v1.bin", "name": "Engine-v1", "inner_name": "EngV1", "release_date": datetime(2024, 1, 1), "description": "Initial engine SW"},
            {"path": "engine_v2.bin", "name": "Engine-v2", "inner_name": "EngV2", "release_date": datetime(2024, 5, 1), "description": "Major engine update"},
            {"path": "trans_v1.bin", "name": "Trans-v1", "inner_name": "TransV1", "release_date": datetime(2024, 2, 1), "description": "Initial trans SW"},
            {"path": "trans_v2.bin", "name": "Trans-v2", "inner_name": "TransV2", "release_date": datetime(2024, 6, 1), "description": "Major trans update"},
            {"path": "hydra_v1.bin", "name": "Hydra-v1", "inner_name": "HydraV1", "release_date": datetime(2024, 3, 1), "description": "Initial hydra SW"},
            {"path": "hydra_v2.bin", "name": "Hydra-v2", "inner_name": "HydraV2", "release_date": datetime(2024, 7, 1), "description": "Major hydra update"},
            {"path": "hydra_v3.bin", "name": "Hydra-v3", "inner_name": "HydraV3", "release_date": datetime(2024, 9, 1), "description": "Major hydra update v3"},
            {"path": "hydra_v4.bin", "name": "Hydra-v4", "inner_name": "HydraV4", "release_date": datetime(2024, 11, 1), "description": "Major hydra update v4"},
            {"path": "susp_v1.bin", "name": "Susp-v1", "inner_name": "SuspV1", "release_date": datetime(2024, 4, 1), "description": "Initial suspension SW"},
            {"path": "susp_v2.bin", "name": "Susp-v2", "inner_name": "SuspV2", "release_date": datetime(2024, 8, 1), "description": "Major suspension update"},
        ]

        softwares = []
        for s_data in softwares:
            sw = Software(**s_data)
            session.add(sw)
            softwares.append(sw)

        session.commit()
        print("✅ Добавлено 10 ПО.")

        # --- 5. Создаём телеметрию и устанавливаем ПО ---
        # Предположим, что:
        # - Трактора 1-10 (REALVIN001 - 010) → требуют major (v1 -> v2)
        # - Трактора 11-20 (REALVIN011 - 020) → требуют minor (v2 -> v2.1, или v2 -> v3)
        # - Трактора 21-30 (REALVIN021 - 030) → обновлены (v2 или v3 установлено)

        sw_map = {sw.name: sw for sw in softwares}

        for i, tractor in enumerate(tractors_data):
            for j, comp in enumerate(components):
                # Найдём детали компонентов для этого компонента
                part_main = next((p for p in component_parts if p.component == comp.id and p.part_type == "main"), None)
                part_aux = next((p for p in component_parts if p.component == comp.id and p.part_type == "aux"), None)

                if not part_main or not part_aux:
                    print(f"⚠️ Детали для компонента {comp.model} не найдены для трактора {tractor.vin}")
                    continue

                # Определяем текущее и новое ПО
                sw_name_current = ""
                sw_name_recommend = ""

                if i < 10:  # Трактора 0-9 (REALVIN001 - REALVIN010) -> MAJOR обновления
                    if comp.type == "engine":
                        sw_name_current = "Engine-v1"
                        sw_name_recommend = "Engine-v2"
                    elif comp.type == "transmission":
                        sw_name_current = "Trans-v1"
                        sw_name_recommend = "Trans-v2"
                    elif comp.type == "hydraulics":
                        sw_name_current = "Hydra-v1"
                        sw_name_recommend = "Hydra-v2"
                    elif comp.type == "suspension":
                        sw_name_current = "Susp-v1"
                        sw_name_recommend = "Susp-v2"
                    else:
                        continue  # brakes не требуют ПО

                    print(f"  - Трактор {tractor.vin} (#{i+1}) -> {comp.type}: {sw_name_current} -> {sw_name_recommend} (MAJOR)")

                elif i < 20:  # Трактора 10-19 (REALVIN011 - REALVIN020) -> MINOR обновления
                    if comp.type == "engine":
                        sw_name_current = "Engine-v2"
                        sw_name_recommend = "Engine-v3"
                    elif comp.type == "transmission":
                        sw_name_current = "Trans-v2"
                        sw_name_recommend = "Trans-v3"  # предположим, что v3 — это minor от v2
                    elif comp.type == "hydraulics":
                        sw_name_current = "Hydra-v2"
                        sw_name_recommend = "Hydra-v3"
                    elif comp.type == "suspension":
                        sw_name_current = "Susp-v2"
                        sw_name_recommend = "Susp-v3"
                    else:
                        continue

                    print(f"  - Трактор {tractor.vin} (#{i+1}) -> {comp.type}: {sw_name_current} -> {sw_name_recommend} (MINOR)")

                else:  # Трактора 20-29 (REALVIN021 - REALVIN030) -> Обновлены
                    if comp.type == "engine":
                        sw_name_current = "Engine-v2"
                        sw_name_recommend = "Engine-v2"
                    elif comp.type == "transmission":
                        sw_name_current = "Trans-v2"
                        sw_name_recommend = "Trans-v2"
                    elif comp.type == "hydraulics":
                        sw_name_current = "Hydra-v3"
                        sw_name_recommend = "Hydra-v3"
                    elif comp.type == "suspension":
                        sw_name_current = "Susp-v2"
                        sw_name_recommend = "Susp-v2"
                    else:
                        continue

                    print(f"  - Трактор {tractor.vin} (#{i+1}) -> {comp.type}: {sw_name_current} -> {sw_name_recommend} (UP-TO-DATE)")

                current_sw = sw_map.get(sw_name_current)
                recommend_sw = sw_map.get(sw_name_recommend)

                if not current_sw:
                    print(f"⚠️ ПО {sw_name_current} не найдено для трактора {tractor.vin}")
                    continue

                # Создаём телеметрию
                tc = TelemetryComponents(
                    tractor=tractor.id,
                    component=comp.id,
                    mounting_date=date.today(),
                    current_sw_version=current_sw.id,
                    recommend_sw_version=recommend_sw.id if recommend_sw else current_sw.id
                )
                session.add(tc)

                # --- Создаём связи ПО <-> Детали компонентов ---
                # MAJOR обновления (трактора 1-10)
                if i < 10 and recommend_sw:
                    # Проверим, нет ли уже такой связи
                    existing_link_main = session.query(Software2ComponentPart).filter(
                        Software2ComponentPart.component_part_id == part_main.id,
                        Software2ComponentPart.software_id == recommend_sw.id
                    ).first()
                    existing_link_aux = session.query(Software2ComponentPart).filter(
                        Software2ComponentPart.component_part_id == part_aux.id,
                        Software2ComponentPart.software_id == recommend_sw.id
                    ).first()

                    if not existing_link_main:
                        link_main = Software2ComponentPart(
                            component_part_id=part_main.id,
                            software_id=recommend_sw.id,
                            is_major=True, # ✅ Это MAJOR обновление
                            status='s',
                            date_change_major=date.today(),
                            previous_sw_version=current_sw.id
                        )
                        session.add(link_main)
                        print(f"    - Создана связь MAJOR для {part_main.id} -> {recommend_sw.name}")

                    if not existing_link_aux:
                        link_aux = Software2ComponentPart(
                            component_part_id=part_aux.id,
                            software_id=recommend_sw.id,
                            is_major=True, # ✅ Это MAJOR обновление
                            status='s',
                            date_change_major=date.today(),
                            previous_sw_version=current_sw.id
                        )
                        session.add(link_aux)
                        print(f"    - Создана связь MAJOR для {part_aux.id} -> {recommend_sw.name}")

                # MINOR обновления (трактора 11-20)
                elif 10 <= i < 20 and recommend_sw:
                    existing_link_main = session.query(Software2ComponentPart).filter(
                        Software2ComponentPart.component_part_id == part_main.id,
                        Software2ComponentPart.software_id == recommend_sw.id
                    ).first()
                    existing_link_aux = session.query(Software2ComponentPart).filter(
                        Software2ComponentPart.component_part_id == part_aux.id,
                        Software2ComponentPart.software_id == recommend_sw.id
                    ).first()

                    if not existing_link_main:
                        link_main = Software2ComponentPart(
                            component_part_id=part_main.id,
                            software_id=recommend_sw.id,
                            is_major=False, # ✅ Это MINOR обновление
                            status='s',
                            date_change_major=None, # Для minor не обязательно
                            previous_sw_version=current_sw.id
                        )
                        session.add(link_main)
                        print(f"    - Создана связь MINOR для {part_main.id} -> {recommend_sw.name}")

                    if not existing_link_aux:
                        link_aux = Software2ComponentPart(
                            component_part_id=part_aux.id,
                            software_id=recommend_sw.id,
                            is_major=False, # ✅ Это MINOR обновление
                            status='s',
                            date_change_major=None, # Для minor не обязательно
                            previous_sw_version=current_sw.id
                        )
                        session.add(link_aux)
                        print(f"    - Создана связь MINOR для {part_aux.id} -> {recommend_sw.name}")

                # UP-TO-DATE (трактора 21-30) — можно создать связи с текущим ПО, но is_major=False
                elif i >= 20:
                    # Создаём связи с текущим ПО как "установленное", но не major
                    existing_link_main = session.query(Software2ComponentPart).filter(
                        Software2ComponentPart.component_part_id == part_main.id,
                        Software2ComponentPart.software_id == current_sw.id
                    ).first()
                    existing_link_aux = session.query(Software2ComponentPart).filter(
                        Software2ComponentPart.component_part_id == part_aux.id,
                        Software2ComponentPart.software_id == current_sw.id
                    ).first()

                    if not existing_link_main:
                        link_main = Software2ComponentPart(
                            component_part_id=part_main.id,
                            software_id=current_sw.id,
                            is_major=False,
                            status='s',
                            date_change_major=None,
                            previous_sw_version=None
                        )
                        session.add(link_main)
                        print(f"    - Создана связь UP-TO-DATE для {part_main.id} -> {current_sw.name}")

                    if not existing_link_aux:
                        link_aux = Software2ComponentPart(
                            component_part_id=part_aux.id,
                            software_id=current_sw.id,
                            is_major=False,
                            status='s',
                            date_change_major=None,
                            previous_sw_version=None
                        )
                        session.add(link_aux)
                        print(f"    - Создана связь UP-TO-DATE для {part_aux.id} -> {current_sw.name}")

        session.commit()
        print("\n--- Реалистичные данные успешно добавлены! ---")
        print("- Трактора REALVIN001 - REALVIN010: Требуют MAJOR обновления.")
        print("- Трактора REALVIN011 - REALVIN020: Требуют MINOR обновления.")
        print("- Трактора REALVIN021 - REALVIN030: Обновлены (up-to-date).")

    except Exception as e:
        session.rollback()
        print(f"❌ Ошибка при заполнении базы данных: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    fill_realistic_data()