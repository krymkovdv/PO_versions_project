# fill_realistic_data.py (исправленная версия с AUTOPILOT)
from datetime import datetime, timezone, timedelta
from app.database import get_session
from app.models import (
    Tractor, Component, Software, 
    Software_Component_Link, Tractor_Software_And_Component_Link,
    SupportMessage, MessageReadStatus, UserDB
)
from sqlalchemy.orm import Session
import random


def fill_realistic_data():
    session: Session = next(get_session())

    try:
        print("="*70)
        print("🚜 ЗАПОЛНЕНИЕ БАЗЫ ДАННЫХ РЕАЛИСТИЧНЫМИ ДАННЫМИ")
        print("="*70)

        # --- 0. ПОЛУЧАЕМ ПОЛЬЗОВАТЕЛЕЙ ДЛЯ ТЕСТИРОВАНИЯ ОБРАТНОЙ СВЯЗИ ---
        users = session.query(UserDB).all()
        moderators = [u for u in users if u.role == "moderator"]
        dealers = [u for u in users if u.role == "dealer"]
        engineers = [u for u in users if u.role == "engineer"]

        print(f"\n👥 Найдено пользователей в системе:")
        print(f"   • Модераторов: {len(moderators)}")
        print(f"   • Дилеров: {len(dealers)}")
        print(f"   • Инженеров: {len(engineers)}")

        # Если пользователей нет, создаем тестовых
        if not users:
            print("\n⚠️ В базе нет пользователей. Создаем тестовых...")
            
            test_users = [
                {"username": "moderator1", "password_hash": "hashed_pass1", "role": "moderator"},
                {"username": "moderator2", "password_hash": "hashed_pass2", "role": "moderator"},
                {"username": "dealer1", "password_hash": "hashed_pass3", "role": "dealer"},
                {"username": "dealer2", "password_hash": "hashed_pass4", "role": "dealer"},
                {"username": "engineer1", "password_hash": "hashed_pass5", "role": "engineer"},
                {"username": "engineer2", "password_hash": "hashed_pass6", "role": "engineer"},
            ]
            
            for u_data in test_users:
                user = UserDB(**u_data)
                session.add(user)
            
            session.flush()
            
            # Обновляем списки
            users = session.query(UserDB).all()
            moderators = [u for u in users if u.role == "moderator"]
            dealers = [u for u in users if u.role == "dealer"]
            engineers = [u for u in users if u.role == "engineer"]
            
            print(f"✅ Создано {len(users)} тестовых пользователей")

        dealers_names = [d.username for d in dealers] if dealers else ["АгроТехСервис", "Кировец-Центр", "СельхозМаш"]

        # --- 1. Добавляем 50 тракторов ---
        tractors_data = []
        models_pool = ["K-7", "K-525", "K-742МСТ", "K-5", "K-700", "K-744", "K-530T", "K-730M", "K-714"]
        regions = ["RU-MOS", "RU-SPE", "RU-KRA", "RU-ROS", "RU-TAT", "RU-BAS", "RU-SYS"]

        # Обычные тракторы
        for i in range(1, 51):
            model = random.choice(models_pool)
            tractor = Tractor(
                model=model,
                vin=f"VIN_{i:05d}",
                oh_hour=random.randint(50, 5000),
                last_activity=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 60)),
                assembly_date=datetime.now(timezone.utc) - timedelta(days=random.randint(30, 1500)),
                region=random.choice(regions[:-1]),
                consumer=random.choice(dealers_names) if dealers_names else "Тестовый потребитель",
                dealer=random.choice(dealers_names) if dealers_names else "Тестовый дилер"
            )
            session.add(tractor)
            tractors_data.append(tractor)

        session.flush()
        print(f"\n✅ Добавлено 50 обычных тракторов.")

        # --- 1.1. Добавляем 8 СИСТЕМНЫХ тракторов ---
        system_models = ["K-7", "K-5", "K-700", "K-744", "K-525", "K-530T", "K-730M", "K-714"]
        for i, model in enumerate(system_models, start=1):
            tractor = Tractor(
                model=model,
                vin=f"VIN_system_{i}",
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
        print(f"✅ Добавлено {len(system_models)} системных тракторов. Всего: {len(tractors_data)}")

        # --- 2. Компоненты (ДОБАВЛЕН AUTOPILOT) ---
        components_data = [
            # DVS (двигатели)
            {"type": "DVS", "name": "ДВС Weichai WP12", "producer": "Weichai"},
            {"type": "DVS", "name": "ДВС Cummins X12", "producer": "Cummins"},
            {"type": "DVS", "name": "ДВС ЯМЗ-238", "producer": "ЯМЗ"},
            
            # KPP (коробки передач)
            {"type": "KPP", "name": "КПП-728", "producer": "Кировец"},
            {"type": "KPP", "name": "КПП-730", "producer": "Кировец"},
            {"type": "KPP", "name": "КПП-740", "producer": "Кировец"},
            
            # RK (рулевое управление)
            {"type": "RK", "name": "Рулевая колонка РК-7", "producer": "Кировец"},
            {"type": "RK", "name": "Рулевой механизм РМ-7", "producer": "Кировец"},
            
            # HR (гидравлика)
            {"type": "HR", "name": "Гидрораспределитель Р-80", "producer": "Гидросила"},
            {"type": "HR", "name": "Гидронасос НШ-50", "producer": "Гидросила"},
            {"type": "HR", "name": "Гидронасос НШ-32", "producer": "Гидросила"},
            
            # BK (бортовые компьютеры)
            {"type": "BK", "name": "БК-Агро v2", "producer": "АгроЭлектроника"},
            {"type": "BK", "name": "БК-Агро v3", "producer": "АгроЭлектроника"},
            {"type": "BK", "name": "БК-Агро v4", "producer": "АгроЭлектроника"},
            
            # AUTOPILOT (НОВЫЙ ТИП КОМПОНЕНТОВ)
            {"type": "AUTOPILOT", "name": "Автопилот АгроПилот v1", "producer": "Cognitive Technologies"},
            {"type": "AUTOPILOT", "name": "Автопилот АгроПилот v2", "producer": "Cognitive Technologies"},
            {"type": "AUTOPILOT", "name": "Автопилот GeoPilot", "producer": "ГеоСкан"},
            {"type": "AUTOPILOT", "name": "Автопилот RTK-Pilot", "producer": "RTK Systems"},
        ]

        components = []
        for c_data in components_data:
            existing = session.query(Component).filter_by(name=c_data["name"]).first()
            if not existing:
                comp = Component(**c_data)
                session.add(comp)
                components.append(comp)
            else:
                components.append(existing)

        session.flush()
        print(f"✅ Добавлено/обновлено {len(components)} компонентов (включая {len([c for c in components if c.type == 'AUTOPILOT'])} автопилотов).")

        # --- 3. ПО (С ОБЯЗАТЕЛЬНЫМ ПОЛЕМ name) ---
        softwares_data = [
            # Для ДВС Weichai
            {"name": "Weichai WP12 ECU v1.0", "path": "weichai/weichai_v1.0.bin", "path_instruction": "weichai/weichai_v1.0.pdf",
             "release_date": datetime(2023, 1, 15), "end_actuality": datetime(2024, 1, 1),
             "description": "Базовая прошивка ДВС Weichai", "producer": "Weichai", 
             "is_actual": False, "is_archive": True, "is_critical": False, 
             "status": "serial", "tractor_model": "K-7", "previous_sw_version": None},
             
            {"name": "Weichai WP12 ECU v2.0", "path": "weichai/weichai_v2.0.bin", "path_instruction": "weichai/weichai_v2.0.pdf",
             "release_date": datetime(2024, 1, 10), "end_actuality": None,
             "description": "Major обновление экологии Euro-5", "producer": "Weichai", 
             "is_actual": True, "is_archive": False, "is_critical": True, 
             "status": "serial", "tractor_model": "K-7", "previous_sw_version": None},
             
            # Для ДВС Cummins
            {"name": "Cummins X12 ECU v1.0", "path": "cummins/cummins_v1.0.bin", "path_instruction": "cummins/cummins_v1.0.pdf",
             "release_date": datetime(2023, 3, 20), "end_actuality": datetime(2024, 2, 1),
             "description": "Базовая прошивка ДВС Cummins", "producer": "Cummins", 
             "is_actual": False, "is_archive": True, "is_critical": False, 
             "status": "serial", "tractor_model": "K-525", "previous_sw_version": None},
             
            {"name": "Cummins X12 ECU v2.0", "path": "cummins/cummins_v2.0.bin", "path_instruction": "cummins/cummins_v2.0.pdf",
             "release_date": datetime(2024, 2, 15), "end_actuality": None,
             "description": "Обновление ДВС Cummins", "producer": "Cummins", 
             "is_actual": True, "is_archive": False, "is_critical": False, 
             "status": "serial", "tractor_model": "K-525", "previous_sw_version": None},
             
            # Для КПП-728
            {"name": "КПП-728 Controller v1.0", "path": "kpp/kpp728_v1.0.bin", "path_instruction": "kpp/kpp728_v1.0.pdf",
             "release_date": datetime(2023, 5, 1), "end_actuality": datetime(2024, 1, 1),
             "description": "Базовая прошивка КПП-728", "producer": "Кировец", 
             "is_actual": False, "is_archive": True, "is_critical": False, 
             "status": "serial", "tractor_model": "K-7", "previous_sw_version": None},
             
            {"name": "КПП-728 Controller v2.0", "path": "kpp/kpp728_v2.0.bin", "path_instruction": "kpp/kpp728_v2.0.pdf",
             "release_date": datetime(2024, 2, 1), "end_actuality": None,
             "description": "Major обновление КПП-728", "producer": "Кировец", 
             "is_actual": True, "is_archive": False, "is_critical": True, 
             "status": "serial", "tractor_model": "K-7", "previous_sw_version": None},
             
            # Для КПП-730
            {"name": "КПП-730 Controller v1.0", "path": "kpp/kpp730_v1.0.bin", "path_instruction": "kpp/kpp730_v1.0.pdf",
             "release_date": datetime(2023, 6, 1), "end_actuality": None,
             "description": "Базовая прошивка КПП-730", "producer": "Кировец", 
             "is_actual": True, "is_archive": False, "is_critical": False, 
             "status": "in operation", "tractor_model": "K-742МСТ", "previous_sw_version": None},
             
            # Для гидравлики
            {"name": "Hydraulic Control v1.0", "path": "hydro/hydro_v1.0.bin", "path_instruction": "hydro/hydro_v1.0.pdf",
             "release_date": datetime(2023, 3, 15), "end_actuality": datetime(2024, 3, 1),
             "description": "Базовая прошивка гидравлики", "producer": "Гидросила", 
             "is_actual": False, "is_archive": True, "is_critical": False, 
             "status": "serial", "tractor_model": "K-7", "previous_sw_version": None},
             
            {"name": "Hydraulic Control v2.0", "path": "hydro/hydro_v2.0.bin", "path_instruction": "hydro/hydro_v2.0.pdf",
             "release_date": datetime(2024, 4, 1), "end_actuality": None,
             "description": "Major обновление гидравлики", "producer": "Гидросила", 
             "is_actual": True, "is_archive": False, "is_critical": True, 
             "status": "experienced", "tractor_model": "K-7", "previous_sw_version": None},
             
            # Для рулевого управления
            {"name": "Steering Control v1.0", "path": "steer/steer_v1.0.bin", "path_instruction": "steer/steer_v1.0.pdf",
             "release_date": datetime(2023, 6, 1), "end_actuality": None,
             "description": "Базовая прошивка рулевого", "producer": "Кировец", 
             "is_actual": True, "is_archive": False, "is_critical": True, 
             "status": "serial", "tractor_model": "K-7", "previous_sw_version": None},
             
            # --- ДОБАВЛЕНО ПО ДЛЯ АВТОПИЛОТА ---
            {"name": "AgroPilot Autopilot v1.0", "path": "autopilot/agropilot_v1.0.bin", "path_instruction": "autopilot/agropilot_v1.0.pdf",
             "release_date": datetime(2023, 8, 15), "end_actuality": datetime(2024, 6, 1),
             "description": "Базовая версия автопилота AgroPilot", "producer": "Cognitive Technologies", 
             "is_actual": False, "is_archive": True, "is_critical": False, 
             "status": "experienced", "tractor_model": "K-7", "previous_sw_version": None},
             
            {"name": "AgroPilot Autopilot v2.0", "path": "autopilot/agropilot_v2.0.bin", "path_instruction": "autopilot/agropilot_v2.0.pdf",
             "release_date": datetime(2024, 6, 10), "end_actuality": None,
             "description": "Автопилот с поддержкой RTK и AI-распознаванием", "producer": "Cognitive Technologies", 
             "is_actual": True, "is_archive": False, "is_critical": True, 
             "status": "serial", "tractor_model": "K-7", "previous_sw_version": None},
             
            {"name": "GeoPilot System v1.0", "path": "autopilot/geopilot_v1.0.bin", "path_instruction": "autopilot/geopilot_v1.0.pdf",
             "release_date": datetime(2024, 1, 20), "end_actuality": None,
             "description": "Геодезическая система автопилотирования", "producer": "ГеоСкан", 
             "is_actual": True, "is_archive": False, "is_critical": False, 
             "status": "serial", "tractor_model": "K-525", "previous_sw_version": None},
             
            {"name": "RTK-Pilot Pro v1.0", "path": "autopilot/rtkpilot_v1.0.bin", "path_instruction": "autopilot/rtkpilot_v1.0.pdf",
             "release_date": datetime(2024, 3, 5), "end_actuality": None,
             "description": "Высокоточный RTK автопилот", "producer": "RTK Systems", 
             "is_actual": True, "is_archive": False, "is_critical": False, 
             "status": "experienced", "tractor_model": "K-744", "previous_sw_version": None},
        ]

        softwares = []
        sw_by_key = {}

        for s_data in softwares_data:
            existing = session.query(Software).filter_by(path=s_data["path"]).first()
            if not existing:
                sw = Software(**s_data)
                session.add(sw)
                session.flush()
                softwares.append(sw)
                
                # Ключи для поиска
                if "Weichai" in s_data["name"]:
                    key = f"Weichai-ECU-{s_data['name'].split('v')[-1].strip()}"
                elif "Cummins" in s_data["name"]:
                    key = f"Cummins-ECU-{s_data['name'].split('v')[-1].strip()}"
                elif "КПП-728" in s_data["name"]:
                    key = f"KPP-728-{s_data['name'].split('v')[-1].strip()}"
                elif "КПП-730" in s_data["name"]:
                    key = "KPP-730-1.0"
                elif "Hydraulic" in s_data["name"]:
                    key = f"HydroCtrl-{s_data['name'].split('v')[-1].strip()}"
                elif "Steering" in s_data["name"]:
                    key = "SteerCtrl-1.0"
                elif "AgroPilot" in s_data["name"]:
                    key = f"AgroPilot-{s_data['name'].split('v')[-1].strip()}"
                elif "GeoPilot" in s_data["name"]:
                    key = "GeoPilot-1.0"
                elif "RTK-Pilot" in s_data["name"]:
                    key = "RTKPilot-1.0"
                else:
                    key = s_data["name"][:20]
                
                sw_by_key[key] = sw
                
                # Обновляем previous_sw_version для версий 2.0
                if "v2.0" in s_data["name"] and "Weichai" in s_data["name"]:
                    prev_sw = session.query(Software).filter_by(name="Weichai WP12 ECU v1.0").first()
                    if prev_sw:
                        sw.previous_sw_version = prev_sw.id
                elif "v2.0" in s_data["name"] and "Cummins" in s_data["name"]:
                    prev_sw = session.query(Software).filter_by(name="Cummins X12 ECU v1.0").first()
                    if prev_sw:
                        sw.previous_sw_version = prev_sw.id
                elif "v2.0" in s_data["name"] and "КПП-728" in s_data["name"]:
                    prev_sw = session.query(Software).filter_by(name="КПП-728 Controller v1.0").first()
                    if prev_sw:
                        sw.previous_sw_version = prev_sw.id
                elif "v2.0" in s_data["name"] and "Hydraulic" in s_data["name"]:
                    prev_sw = session.query(Software).filter_by(name="Hydraulic Control v1.0").first()
                    if prev_sw:
                        sw.previous_sw_version = prev_sw.id
                elif "v2.0" in s_data["name"] and "AgroPilot" in s_data["name"]:
                    prev_sw = session.query(Software).filter_by(name="AgroPilot Autopilot v1.0").first()
                    if prev_sw:
                        sw.previous_sw_version = prev_sw.id
            else:
                softwares.append(existing)

        session.flush()
        print(f"✅ Добавлено/обновлено {len(softwares)} ПО (включая {len([sw for sw in softwares if 'Pilot' in sw.name])} для автопилотов).")

        # --- 4. Связи ПО и Компонентов (ДОБАВЛЕНЫ СВЯЗИ ДЛЯ АВТОПИЛОТА) ---
        component_sw_mapping = {
            "ДВС Weichai WP12": ["Weichai-ECU-1.0", "Weichai-ECU-2.0"],
            "ДВС Cummins X12": ["Cummins-ECU-1.0", "Cummins-ECU-2.0"],
            "КПП-728": ["KPP-728-1.0", "KPP-728-2.0"],
            "КПП-730": ["KPP-730-1.0"],
            "Гидрораспределитель Р-80": ["HydroCtrl-1.0", "HydroCtrl-2.0"],
            "Гидронасос НШ-50": ["HydroCtrl-1.0", "HydroCtrl-2.0"],
            "Рулевая колонка РК-7": ["SteerCtrl-1.0"],
            "Рулевой механизм РМ-7": ["SteerCtrl-1.0"],
            
            # Связи для автопилотов
            "Автопилот АгроПилот v1": ["AgroPilot-1.0"],
            "Автопилот АгроПилот v2": ["AgroPilot-2.0"],
            "Автопилот GeoPilot": ["GeoPilot-1.0"],
            "Автопилот RTK-Pilot": ["RTKPilot-1.0"],
        }

        software_component_links = []
        
        for comp in components:
            sw_keys = component_sw_mapping.get(comp.name, [])
            for sw_key in sw_keys:
                sw = sw_by_key.get(sw_key)
                if sw:
                    existing_link = session.query(Software_Component_Link).filter_by(
                        component_id=comp.id,
                        software_id=sw.id
                    ).first()
                    
                    if not existing_link:
                        link = Software_Component_Link(
                            component_id=comp.id,
                            software_id=sw.id
                        )
                        session.add(link)
                        software_component_links.append(link)

        session.flush()
        print(f"✅ Добавлено {len(software_component_links)} связей ПО-Компоненты.")

        # --- 5. Связи Тракторов с ПО и Компонентами ---
        tractor_links_count = 0
        
        for tractor in tractors_data:
            # Для каждого трактора выбираем несколько связей
            num_links = random.randint(2, 5)
            selected_links = random.sample(software_component_links, min(num_links, len(software_component_links)))
            
            for sw_link in selected_links:
                existing_tractor_link = session.query(Tractor_Software_And_Component_Link).filter_by(
                    tractor_id=tractor.id,
                    soft_comp_link_id=sw_link.id
                ).first()
                
                if not existing_tractor_link:
                    tractor_link = Tractor_Software_And_Component_Link(
                        is_recom=random.choice([True, False]),
                        tractor_id=tractor.id,
                        soft_comp_link_id=sw_link.id
                    )
                    session.add(tractor_link)
                    tractor_links_count += 1

        session.flush()
        print(f"✅ Добавлено {tractor_links_count} связей Трактор-ПО-Компоненты.")

        # --- 6. СОЗДАНИЕ ТЕСТОВЫХ СООБЩЕНИЙ ---
        if moderators and (dealers or engineers):
            print(f"\n📨 СОЗДАНИЕ ТЕСТОВЫХ СООБЩЕНИЙ")
            
            messages_created = 0
            replies_created = 0
            
            for moderator in moderators[:2]:
                
                # Создаем сообщения от дилеров
                for dealer in dealers[:3] if dealers else []:
                    for _ in range(random.randint(2, 3)):
                        msg = SupportMessage(
                            content=f"Вопрос от дилера {dealer.username}: Проблема с трактором VIN_{random.randint(1,50):05d}",
                            sender_id=dealer.id,
                            is_read=False,
                            is_closed=random.choice([True, False]),
                            parent_message_id=None
                        )
                        session.add(msg)
                        session.flush()
                        messages_created += 1
                        
                        # Создаем статусы прочтения для всех модераторов
                        for mod in moderators:
                            read_status = MessageReadStatus(
                                message_id=msg.id,
                                moderator_id=mod.id,
                                is_read=(mod.id == moderator.id and random.choice([True, False])),
                                read_at=datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 24)) if random.choice([True, False]) else None
                            )
                            session.add(read_status)
                        
                        # Некоторые сообщения получают ответы
                        if random.choice([True, False]):
                            for reply_mod in random.sample(moderators, random.randint(1, len(moderators))):
                                reply = SupportMessage(
                                    content=f"Ответ от модератора {reply_mod.username}: Проверьте настройки",
                                    sender_id=reply_mod.id,
                                    is_read=False,
                                    is_closed=False,
                                    parent_message_id=msg.id
                                )
                                session.add(reply)
                                session.flush()
                                replies_created += 1
                                
                                for mod in moderators:
                                    if mod.id != reply_mod.id:
                                        read_status = MessageReadStatus(
                                            message_id=reply.id,
                                            moderator_id=mod.id,
                                            is_read=False,
                                            read_at=None
                                        )
                                        session.add(read_status)
                
                # Создаем сообщения от инженеров
                for engineer in engineers[:2] if engineers else []:
                    for _ in range(random.randint(1, 2)):
                        msg = SupportMessage(
                            content=f"Технический вопрос от инженера {engineer.username}: Нужно обновление ПО",
                            sender_id=engineer.id,
                            is_read=False,
                            is_closed=False,
                            parent_message_id=None
                        )
                        session.add(msg)
                        session.flush()
                        messages_created += 1
                        
                        for mod in moderators:
                            read_status = MessageReadStatus(
                                message_id=msg.id,
                                moderator_id=mod.id,
                                is_read=(mod.id == moderator.id and random.choice([True, False])),
                                read_at=datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 24)) if random.choice([True, False]) else None
                            )
                            session.add(read_status)
                        
                        if random.choice([True, True, False]):
                            for reply_mod in random.sample(moderators, random.randint(1, len(moderators))):
                                reply = SupportMessage(
                                    content=f"Ответ от модератора {reply_mod.username}: Рекомендуем обновиться",
                                    sender_id=reply_mod.id,
                                    is_read=False,
                                    is_closed=False,
                                    parent_message_id=msg.id
                                )
                                session.add(reply)
                                session.flush()
                                replies_created += 1
                                
                                for mod in moderators:
                                    if mod.id != reply_mod.id:
                                        read_status = MessageReadStatus(
                                            message_id=reply.id,
                                            moderator_id=mod.id,
                                            is_read=False,
                                            read_at=None
                                        )
                                        session.add(read_status)
            
            print(f"✅ Создано сообщений:")
            print(f"   • Корневых сообщений: {messages_created}")
            print(f"   • Ответов: {replies_created}")
            print(f"   • Всего сообщений: {messages_created + replies_created}")

        # --- 7. Вывод статистики ---
        session.commit()
        
        print("\n" + "="*70)
        print("📊 СТАТИСТИКА ЗАПОЛНЕНИЯ БАЗЫ ДАННЫХ")
        print("="*70)
        print(f"\n🚜 Тракторы:")
        print(f"   • Всего: {len(tractors_data)}")
        
        print(f"\n🔧 Компоненты:")
        print(f"   • Всего: {len(components)}")
        print(f"   • Из них автопилотов: {len([c for c in components if c.type == 'AUTOPILOT'])}")
        
        print(f"\n💾 ПО:")
        print(f"   • Всего: {len(softwares)}")
        print(f"   • Из них для автопилотов: {len([sw for sw in softwares if 'Pilot' in sw.name])}")
        
        # Проверяем, что все ПО имеют name
        softwares_without_name = [sw for sw in softwares if sw.name is None]
        if softwares_without_name:
            print(f"   ⚠️ ВНИМАНИЕ: {len(softwares_without_name)} ПО без name!")
        else:
            print(f"   ✅ Все ПО имеют заполненное поле name")
        
        print(f"\n🔗 Связи:")
        print(f"   • ПО-Компоненты: {len(software_component_links)}")
        print(f"   • Трактор-ПО-Компоненты: {tractor_links_count}")
        
        total_messages = session.query(SupportMessage).count()
        root_messages = session.query(SupportMessage).filter(SupportMessage.parent_message_id == None).count()
        replies = session.query(SupportMessage).filter(SupportMessage.parent_message_id != None).count()
        
        print(f"\n📨 Обратная связь:")
        print(f"   • Всего сообщений: {total_messages}")
        print(f"   • Корневых сообщений: {root_messages}")
        print(f"   • Ответов: {replies}")
        print(f"   • Статусов прочтения: {session.query(MessageReadStatus).count()}")
        
        print(f"\n✅ База данных успешно заполнена!")
        print("="*70)

    except Exception as e:
        session.rollback()
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    fill_realistic_data()