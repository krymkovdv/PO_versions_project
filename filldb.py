# fill_realistic_data.py
from datetime import datetime, date, timezone, timedelta
from app.database import get_session
from app.models import Tractor, Component, Software, Software_Component_Link, Tractor_Software_And_Component_Link
from sqlalchemy.orm import Session
import random

def fill_realistic_data():
    session: Session = next(get_session())

    try:
        print("Заполняем базу данных реалистичными данными...")

        # --- 1. Добавляем 50 тракторов ---
        tractors_data = []
        models_pool = ["K-7", "K-525", "K-742МСТ", "K-5", "K-700", "K-744", "K-530T", "K-730M", "K-714"]
        regions = ["RU-MOS", "RU-SPE", "RU-KRA", "RU-ROS", "RU-TAT", "RU-BAS"]
        dealers = ["АгроТехСервис", "Кировец-Центр", "СельхозМаш", "АгроИнвест", 
                   "ТехноАгро", "РосАгроМаш", "АгроКомплект", "Механизатор",
                   "АгроСервисПлюс", "ТракторныйДом"]
        dealers_for_consumer = dealers.copy()
        dealers_for_dealer = dealers.copy()

        # Обычные тракторы
        for i in range(1, 51):
            model = random.choice(models_pool)
            tractor = Tractor(
                model=model,
                vin=f"VIN_{i:05d}",  # VIN_00001...VIN_00050
                oh_hour=random.randint(50, 5000),
                last_activity=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 60)),
                assembly_date=datetime.now(timezone.utc) - timedelta(days=random.randint(30, 1500)),
                region=random.choice(regions),
                consumer=random.choice(dealers_for_consumer),
                dealer=random.choice(dealers_for_dealer)
            )
            session.add(tractor)
            tractors_data.append(tractor)

        session.flush()
        print("✅ Добавлено 50 обычных тракторов.")

        # --- 1.1. Добавляем 8 СИСТЕМНЫХ тракторов с НЕОБЫЧНЫМ VIN ---
        system_models = ["K-7", "K-5", "K-700", "K-744", "K-525", "K-530T", "K-730M", "K-714"]
        for i, model in enumerate(system_models, start=1):
            tractor = Tractor(
                model=model,
                vin=f"VIN_system_{i}",  # VIN_system_1, VIN_system_2...
                oh_hour=random.randint(0, 100),
                last_activity=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 5)),
                assembly_date=datetime.now(timezone.utc) - timedelta(days=random.randint(30, 365)),
                region="RU-SYS",
                consumer="Системный трактор",
                dealer="СЦ-Системный"
            )
            session.add(tractor)
            tractors_data.append(tractor)

        session.flush()
        print(f"✅ Добавлено {len(system_models)} системных тракторов (VIN_system_*).")

        # --- 2. Компоненты ---
        components_data = [
            {"type": "DVS", "name": "ДВС Weichai WP12", "producer": "Weichai"},
            {"type": "KPP", "name": "КПП-728", "producer": "Кировец"},
            {"type": "HR", "name": "Гидрораспределитель Р-80", "producer": "Гидросила"},
            {"type": "RK", "name": "Рулевая колонка РК-7", "producer": "Кировец"},
            {"type": "DVS", "name": "ДВС Cummins X12", "producer": "Cummins"},
            {"type": "KPP", "name": "КПП-730", "producer": "Кировец"},
            {"type": "BK", "name": "БК-Агро v2", "producer": "АгроЭлектроника"},
            {"type": "HR", "name": "Гидронасос НШ-50", "producer": "Гидросила"},
            {"type": "RK", "name": "Рулевой механизм РМ-7", "producer": "Кировец"},
            {"type": "BK", "name": "БК-Агро v3", "producer": "АгроЭлектроника"},
        ]

        components = []
        for c_data in components_data:
            # Проверяем, существует ли уже такой компонент
            existing = session.query(Component).filter_by(name=c_data["name"]).first()
            if not existing:
                comp = Component(**c_data)
                session.add(comp)
                components.append(comp)
            else:
                components.append(existing)

        session.flush()
        print(f"✅ Добавлено/обновлено {len(components)} компонентов.")

        # --- 3. ПО ---
        softwares_data = [
            # Для ДВС Weichai
            {"path": "weichai/weichai_v1.0.bin", "path_instruction": "weichai/weichai_v1.0.pdf",
             "release_date": datetime(2023, 1, 15), "end_actuality": datetime(2024, 1, 1),
             "description": "Базовая прошивка ДВС Weichai", "producer": "Weichai", 
             "is_actual": False, "is_archive": True, "is_critical": False, 
             "status": "serial", "tractor_model": "K-7", "previous_sw_version": None},
             
            {"path": "weichai/weichai_v2.0.bin", "path_instruction": "weichai/weichai_v2.0.pdf",
             "release_date": datetime(2024, 1, 10), "end_actuality": None,
             "description": "Major обновление экологии Euro-5", "producer": "Weichai", 
             "is_actual": True, "is_archive": False, "is_critical": True, 
             "status": "serial", "tractor_model": "K-7", "previous_sw_version": 1},
             
            # Для ДВС Cummins
            {"path": "cummins/cummins_v1.0.bin", "path_instruction": "cummins/cummins_v1.0.pdf",
             "release_date": datetime(2023, 3, 20), "end_actuality": datetime(2024, 2, 1),
             "description": "Базовая прошивка ДВС Cummins", "producer": "Cummins", 
             "is_actual": False, "is_archive": True, "is_critical": False, 
             "status": "serial", "tractor_model": "K-525", "previous_sw_version": None},
             
            {"path": "cummins/cummins_v2.0.bin", "path_instruction": "cummins/cummins_v2.0.pdf",
             "release_date": datetime(2024, 2, 15), "end_actuality": None,
             "description": "Обновление ДВС Cummins", "producer": "Cummins", 
             "is_actual": True, "is_archive": False, "is_critical": False, 
             "status": "serial", "tractor_model": "K-525", "previous_sw_version": 3},
             
            # Для КПП-728
            {"path": "kpp/kpp728_v1.0.bin", "path_instruction": "kpp/kpp728_v1.0.pdf",
             "release_date": datetime(2023, 5, 1), "end_actuality": datetime(2024, 1, 1),
             "description": "Базовая прошивка КПП-728", "producer": "Кировец", 
             "is_actual": False, "is_archive": True, "is_critical": False, 
             "status": "serial", "tractor_model": "K-7", "previous_sw_version": None},
             
            {"path": "kpp/kpp728_v2.0.bin", "path_instruction": "kpp/kpp728_v2.0.pdf",
             "release_date": datetime(2024, 2, 1), "end_actuality": None,
             "description": "Major обновление КПП-728", "producer": "Кировец", 
             "is_actual": True, "is_archive": False, "is_critical": True, 
             "status": "serial", "tractor_model": "K-7", "previous_sw_version": 5},
             
            # Для КПП-730
            {"path": "kpp/kpp730_v1.0.bin", "path_instruction": "kpp/kpp730_v1.0.pdf",
             "release_date": datetime(2023, 6, 1), "end_actuality": None,
             "description": "Базовая прошивка КПП-730", "producer": "Кировец", 
             "is_actual": True, "is_archive": False, "is_critical": False, 
             "status": "in operation", "tractor_model": "K-742МСТ", "previous_sw_version": None},
             
            # Для гидравлики
            {"path": "hydro/hydro_v1.0.bin", "path_instruction": "hydro/hydro_v1.0.pdf",
             "release_date": datetime(2023, 3, 15), "end_actuality": datetime(2024, 3, 1),
             "description": "Базовая прошивка гидравлики", "producer": "Гидросила", 
             "is_actual": False, "is_archive": True, "is_critical": False, 
             "status": "serial", "tractor_model": "K-7", "previous_sw_version": None},
             
            {"path": "hydro/hydro_v2.0.bin", "path_instruction": "hydro/hydro_v2.0.pdf",
             "release_date": datetime(2024, 4, 1), "end_actuality": None,
             "description": "Major обновление гидравлики", "producer": "Гидросила", 
             "is_actual": True, "is_archive": False, "is_critical": True, 
             "status": "experienced", "tractor_model": "K-7", "previous_sw_version": 8},
             
            # Для рулевого управления
            {"path": "steer/steer_v1.0.bin", "path_instruction": "steer/steer_v1.0.pdf",
             "release_date": datetime(2023, 6, 1), "end_actuality": None,
             "description": "Базовая прошивка рулевого", "producer": "Кировец", 
             "is_actual": True, "is_archive": False, "is_critical": True, 
             "status": "serial", "tractor_model": "K-7", "previous_sw_version": None},
             
            # Для БК-Агро v2
            {"path": "bk/bk_v1.5.bin", "path_instruction": "bk/bk_v1.5.pdf",
             "release_date": datetime(2024, 1, 1), "end_actuality": datetime(2024, 4, 1),
             "description": "Minor обновление БК", "producer": "АгроЭлектроника", 
             "is_actual": False, "is_archive": True, "is_critical": False, 
             "status": "experienced", "tractor_model": "K-5", "previous_sw_version": None},
             
            {"path": "bk/bk_v2.0.bin", "path_instruction": "bk/bk_v2.0.pdf",
             "release_date": datetime(2024, 5, 1), "end_actuality": None,
             "description": "Major обновление БК", "producer": "АгроЭлектроника", 
             "is_actual": True, "is_archive": False, "is_critical": True, 
             "status": "serial", "tractor_model": "K-5", "previous_sw_version": 11},
        ]

        softwares = []
        sw_by_name = {}  # Для быстрого поиска ПО по описанию

        for s_data in softwares_data:
            # Проверяем существование ПО
            existing = session.query(Software).filter_by(path=s_data["path"]).first()
            if not existing:
                sw = Software(**s_data)
                session.add(sw)
                session.flush()  # Чтобы получить id
                softwares.append(sw)
                # Сохраняем в словарь для последующего использования
                if "Базовая прошивка ДВС Weichai" in s_data["description"]:
                    sw_by_name["Weichai-ECU-1.0"] = sw
                elif "Major обновление экологии Euro-5" in s_data["description"]:
                    sw_by_name["Weichai-ECU-2.0"] = sw
                elif "Базовая прошивка ДВС Cummins" in s_data["description"]:
                    sw_by_name["Cummins-ECU-1.0"] = sw
                elif "Обновление ДВС Cummins" in s_data["description"]:
                    sw_by_name["Cummins-ECU-2.0"] = sw
                elif "Базовая прошивка КПП-728" in s_data["description"]:
                    sw_by_name["KPP-728-1.0"] = sw
                elif "Major обновление КПП-728" in s_data["description"]:
                    sw_by_name["KPP-728-2.0"] = sw
                elif "Базовая прошивка КПП-730" in s_data["description"]:
                    sw_by_name["KPP-730-1.0"] = sw
                elif "Базовая прошивка гидравлики" in s_data["description"]:
                    sw_by_name["HydroCtrl-1.0"] = sw
                elif "Major обновление гидравлики" in s_data["description"]:
                    sw_by_name["HydroCtrl-2.0"] = sw
                elif "Базовая прошивка рулевого" in s_data["description"]:
                    sw_by_name["SteerCtrl-1.0"] = sw
                elif "Minor обновление БК" in s_data["description"]:
                    sw_by_name["BK-Agro-1.5"] = sw
                elif "Major обновление БК" in s_data["description"]:
                    sw_by_name["BK-Agro-2.0"] = sw
            else:
                softwares.append(existing)
                # Добавляем в словарь существующее ПО
                sw_by_name[existing.description[:20]] = existing

        session.flush()
        print(f"✅ Добавлено/обновлено {len(softwares)} ПО.")

        # Если словарь пуст, заполняем его из существующих записей
        if not sw_by_name:
            for sw in softwares:
                if "Weichai" in sw.path:
                    if "v1.0" in sw.path:
                        sw_by_name["Weichai-ECU-1.0"] = sw
                    elif "v2.0" in sw.path:
                        sw_by_name["Weichai-ECU-2.0"] = sw
                elif "cummins" in sw.path.lower():
                    if "v1.0" in sw.path:
                        sw_by_name["Cummins-ECU-1.0"] = sw
                    elif "v2.0" in sw.path:
                        sw_by_name["Cummins-ECU-2.0"] = sw
                elif "kpp728" in sw.path.lower():
                    if "v1.0" in sw.path:
                        sw_by_name["KPP-728-1.0"] = sw
                    elif "v2.0" in sw.path:
                        sw_by_name["KPP-728-2.0"] = sw
                elif "kpp730" in sw.path.lower():
                    sw_by_name["KPP-730-1.0"] = sw
                elif "hydro" in sw.path.lower():
                    if "v1.0" in sw.path:
                        sw_by_name["HydroCtrl-1.0"] = sw
                    elif "v2.0" in sw.path:
                        sw_by_name["HydroCtrl-2.0"] = sw
                elif "steer" in sw.path.lower():
                    sw_by_name["SteerCtrl-1.0"] = sw
                elif "bk" in sw.path.lower():
                    if "v1.5" in sw.path:
                        sw_by_name["BK-Agro-1.5"] = sw
                    elif "v2.0" in sw.path:
                        sw_by_name["BK-Agro-2.0"] = sw

        # --- 4. Связи ПО и Компонентов (Software_Component_Link) ---
        component_sw_mapping = {
            "ДВС Weichai WP12": [
                ("Weichai-ECU-1.0", "Weichai-ECU-2.0")
            ],
            "ДВС Cummins X12": [
                ("Cummins-ECU-1.0", "Cummins-ECU-2.0")
            ],
            "КПП-728": [
                ("KPP-728-1.0", "KPP-728-2.0")
            ],
            "КПП-730": [
                ("KPP-730-1.0", None)
            ],
            "Гидрораспределитель Р-80": [
                ("HydroCtrl-1.0", "HydroCtrl-2.0")
            ],
            "Гидронасос НШ-50": [
                ("HydroCtrl-1.0", "HydroCtrl-2.0")
            ],
            "Рулевая колонка РК-7": [
                ("SteerCtrl-1.0", None)
            ],
            "Рулевой механизм РМ-7": [
                ("SteerCtrl-1.0", None)
            ],
            "БК-Агро v2": [
                ("BK-Agro-1.5", "BK-Agro-2.0")
            ],
            "БК-Агро v3": [
                ("BK-Agro-2.0", None)
            ],
        }

        software_component_links = []
        
        for comp in components:
            sw_names_list = component_sw_mapping.get(comp.name, [])
            for sw_names in sw_names_list:
                current_sw_name, next_sw_name = sw_names
                
                current_sw = sw_by_name.get(current_sw_name)
                if not current_sw:
                    # Пытаемся найти по части имени
                    for key, sw in sw_by_name.items():
                        if current_sw_name.lower() in key.lower():
                            current_sw = sw
                            break
                
                if current_sw:
                    # Создаем связь для текущей версии ПО
                    link = Software_Component_Link(
                        component_id=comp.id,
                        software_id=current_sw.id
                    )
                    session.add(link)
                    software_component_links.append(link)
                    
                if next_sw_name and next_sw_name != current_sw_name:
                    next_sw = sw_by_name.get(next_sw_name)
                    if next_sw and next_sw.id != current_sw.id:
                        link = Software_Component_Link(
                            component_id=comp.id,
                            software_id=next_sw.id
                        )
                        session.add(link)
                        software_component_links.append(link)

        session.flush()
        print(f"✅ Добавлено {len(software_component_links)} связей ПО-Компоненты.")

        # --- 5. Связи Тракторов с ПО и Компонентами (Tractor_Software_And_Component_Link) ---
        tractor_links_count = 0
        
        # Для обычных тракторов (первые 50)
        for i, tractor in enumerate(tractors_data[:50]):
            # Для каждого компонента выбираем подходящее ПО
            for comp in components:
                # Определяем, какое ПО должно быть установлено
                sw_links_for_comp = [link for link in software_component_links if link.component_id == comp.id]
                
                if not sw_links_for_comp:
                    continue
                
                # Выбираем ПО в зависимости от группы трактора
                if i < 15:  # Первая группа - старая версия
                    sw_link = sw_links_for_comp[0]  # Первая связь (обычно старая версия)
                    is_recom = len(sw_links_for_comp) > 1  # Рекомендуется если есть новая версия
                elif i < 30:  # Вторая группа - смешанная
                    if len(sw_links_for_comp) > 1:
                        # 50% на 50% старая/новая
                        sw_link = random.choice(sw_links_for_comp)
                    else:
                        sw_link = sw_links_for_comp[0]
                    is_recom = len(sw_links_for_comp) > 1
                else:  # Третья группа - новая версия
                    if len(sw_links_for_comp) > 1:
                        sw_link = sw_links_for_comp[-1]  # Последняя связь (обычно новая версия)
                    else:
                        sw_link = sw_links_for_comp[0]
                    is_recom = True
                
                # Создаем связь трактора с ПО и компонентом
                tractor_link = Tractor_Software_And_Component_Link(
                    is_recom=is_recom,
                    tractor_id=tractor.id,
                    soft_comp_link_id=sw_link.id
                )
                session.add(tractor_link)
                tractor_links_count += 1

        # Для системных тракторов (индексы 50-57) - добавляем только несколько связей
        for i, tractor in enumerate(tractors_data[50:], start=50):
            # Добавляем только 2-3 компонента для каждого системного трактора
            for comp in random.sample(components, min(3, len(components))):
                sw_links_for_comp = [link for link in software_component_links if link.component_id == comp.id]
                if sw_links_for_comp:
                    sw_link = random.choice(sw_links_for_comp)
                    tractor_link = Tractor_Software_And_Component_Link(
                        is_recom=True,
                        tractor_id=tractor.id,
                        soft_comp_link_id=sw_link.id
                    )
                    session.add(tractor_link)
                    tractor_links_count += 1

        session.flush()
        print(f"✅ Добавлено {tractor_links_count} связей Трактор-ПО-Компоненты.")

        # --- 6. Вывод статистики для первых нескольких тракторов ---
        print("\n📊 Примеры созданных связей:")
        for i, tractor in enumerate(tractors_data[:5]):
            links = session.query(Tractor_Software_And_Component_Link).filter_by(tractor_id=tractor.id).all()
            print(f"\n  Трактор {tractor.vin} ({tractor.model}):")
            for link in links[:3]:  # Показываем первые 3 связи
                soft_comp_link = link.software_component_link
                component = soft_comp_link.component
                software = soft_comp_link.software
                print(f"    • {component.type}: {component.name} -> ПО: {software.path.split('/')[-1]} (рекоменд: {link.is_recom})")

        session.commit()
        
        print("\n" + "="*70)
        print("✅ РЕАЛИСТИЧНЫЕ ДАННЫЕ УСПЕШНО ДОБАВЛЕНЫ!")
        print("="*70)
        print(f"\n📊 Итоговая статистика:")
        print(f"   • Тракторов: {len(tractors_data)} (50 обычных + 8 системных)")
        print(f"   • Компонентов: {len(components)}")
        print(f"   • ПО: {len(softwares)}")
        print(f"   • Связей ПО-Компоненты: {len(software_component_links)}")
        print(f"   • Связей Трактор-ПО-Компоненты: {tractor_links_count}")
        
        print(f"\n🔧 Типы компонентов (согласно ограничениям БД):")
        print("   • DVS (Двигатели)")
        print("   • KPP (Коробки передач)")
        print("   • RK (Рулевое управление)")
        print("   • HR (Гидравлика)")
        print("   • BK (Бортовые компьютеры)")
        
        print(f"\n📈 Группы тракторов:")
        print("   • VIN_00001-00050: Обычные тракторы (с полным набором связей)")
        print("   • VIN_system_1-8: СИСТЕМНЫЕ (с ограниченным набором связей)")
        
        print(f"\n🔰 Системные тракторы:")
        for i, model in enumerate(system_models, start=1):
            print(f"   • VIN_system_{i} ({model})")
        
        print(f"\n🔍 Доступные фильтры для тестирования:")
        print("   • Модели тракторов: K-7, K-525, K-742МСТ, K-5, K-700, K-744, K-530T, K-730M, K-714")
        print("   • Типы компонентов: DVS, KPP, RK, HR, BK")
        print("   • VIN: VIN_00001...VIN_00050, VIN_system_1...VIN_system_8")
        print("   • Регион: RU-SYS — для фильтрации системных тракторов")
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