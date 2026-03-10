# fill_realistic_data.py
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

        # Если пользователей нет, используем имена из справочников
        if not dealers:
            dealers_names = ["АгроТехСервис", "Кировец-Центр", "СельхозМаш", "АгроИнвест", 
                           "ТехноАгро", "РосАгроМаш", "АгроКомплект", "Механизатор",
                           "АгроСервисПлюс", "ТракторныйДом"]
        else:
            dealers_names = [d.username for d in dealers]

        # --- 1. Добавляем 50 тракторов ---
        tractors_data = []
        models_pool = ["K-7", "K-525", "K-742МСТ", "K-5", "K-700", "K-744", "K-530T", "K-730M", "K-714"]
        regions = ["RU-MOS", "RU-SPE", "RU-KRA", "RU-ROS", "RU-TAT", "RU-BAS", "RU-SYS"]

        # Обычные тракторы
        for i in range(1, 51):
            model = random.choice(models_pool)
            tractor = Tractor(
                model=model,
                vin=f"VIN_{i:05d}",  # VIN_00001...VIN_00050
                oh_hour=random.randint(50, 5000),
                last_activity=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 60)),
                assembly_date=datetime.now(timezone.utc) - timedelta(days=random.randint(30, 1500)),
                region=random.choice(regions[:-1]),  # Все кроме RU-SYS
                consumer=random.choice(dealers_names),
                dealer=random.choice(dealers_names)
            )
            session.add(tractor)
            tractors_data.append(tractor)

        session.flush()
        print(f"\n✅ Добавлено 50 обычных тракторов.")

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
            tractors.append(tractor)

        session.flush()
        print(f"✅ Добавлено {len(tractors)} тракторов (15 обычных + 5 системных).")

        # --- 2. Компоненты с правильными типами (CheckConstraint) ---
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
        print(f"✅ Добавлено/обновлено {len(components)} компонентов.")

        # --- 3. ПО с правильными статусами (CheckConstraint) ---
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
                if "Weichai" in s_data["path"]:
                    key = "Weichai-ECU-" + ("1.0" if "v1.0" in s_data["path"] else "2.0")
                elif "cummins" in s_data["path"].lower():
                    key = "Cummins-ECU-" + ("1.0" if "v1.0" in s_data["path"] else "2.0")
                elif "kpp728" in s_data["path"].lower():
                    key = "KPP-728-" + ("1.0" if "v1.0" in s_data["path"] else "2.0")
                elif "kpp730" in s_data["path"].lower():
                    key = "KPP-730-1.0"
                elif "hydro" in s_data["path"].lower():
                    key = "HydroCtrl-" + ("1.0" if "v1.0" in s_data["path"] else "2.0")
                elif "steer" in s_data["path"].lower():
                    key = "SteerCtrl-1.0"
                else:
                    key = s_data["description"][:20]
                
                sw_by_key[key] = sw
            else:
                softwares.append(existing)

        session.flush()
        print(f"✅ Добавлено/обновлено {len(softwares)} ПО.")

        # --- 4. Связи ПО и Компонентов (Software_Component_Link) ---
        component_sw_mapping = {
            "ДВС Weichai WP12": ["Weichai-ECU-1.0", "Weichai-ECU-2.0"],
            "ДВС Cummins X12": ["Cummins-ECU-1.0", "Cummins-ECU-2.0"],
            "ДВС ЯМЗ-238": ["Weichai-ECU-1.0"],  # Временная заглушка
            "КПП-728": ["KPP-728-1.0", "KPP-728-2.0"],
            "КПП-730": ["KPP-730-1.0"],
            "КПП-740": ["KPP-730-1.0"],  # Временная заглушка
            "Рулевая колонка РК-7": ["SteerCtrl-1.0"],
            "Рулевой механизм РМ-7": ["SteerCtrl-1.0"],
            "Гидрораспределитель Р-80": ["HydroCtrl-1.0", "HydroCtrl-2.0"],
            "Гидронасос НШ-50": ["HydroCtrl-1.0", "HydroCtrl-2.0"],
            "Гидронасос НШ-32": ["HydroCtrl-1.0"],
            "БК-Агро v2": ["SteerCtrl-1.0"],  # Временная заглушка
            "БК-Агро v3": ["SteerCtrl-1.0"],  # Временная заглушка
            "БК-Агро v4": ["SteerCtrl-1.0"],  # Временная заглушка
        }

        software_component_links = []
        
        for comp in components:
            sw_keys = component_sw_mapping.get(comp.name, [])
            for sw_key in sw_keys:
                sw = sw_by_key.get(sw_key)
                if sw:
                    # Проверяем, существует ли уже такая связь
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
        
        # Для обычных тракторов (первые 50)
        for i, tractor in enumerate(tractors_data[:50]):
            # Для каждого компонента выбираем подходящее ПО
            for comp in components:
                links_for_comp = [link for link in software_component_links if link.component_id == comp.id]
                
                if not links_for_comp:
                    continue
                
                # Выбираем ПО в зависимости от группы трактора
                if i < 15:  # Первая группа - старая версия
                    sw_link = links_for_comp[0]
                    is_recom = len(links_for_comp) > 1
                elif i < 30:  # Вторая группа - смешанная
                    sw_link = random.choice(links_for_comp)
                    is_recom = len(links_for_comp) > 1
                else:  # Третья группа - новая версия
                    sw_link = links_for_comp[-1] if len(links_for_comp) > 1 else links_for_comp[0]
                    is_recom = True
                
                # Проверяем, существует ли уже такая связь
                existing_tractor_link = session.query(Tractor_Software_And_Component_Link).filter_by(
                    tractor_id=tractor.id,
                    soft_comp_link_id=sw_link.id
                ).first()
                
                if not existing_tractor_link:
                    tractor_link = Tractor_Software_And_Component_Link(
                        is_recom=is_recom,
                        tractor_id=tractor.id,
                        soft_comp_link_id=sw_link.id
                    )
                    session.add(tractor_link)
                    tractor_links_count += 1

        # Для системных тракторов (индексы 50-57)
        for i, tractor in enumerate(tractors_data[50:], start=50):
            for comp in random.sample(components, min(3, len(components))):
                links_for_comp = [link for link in software_component_links if link.component_id == comp.id]
                if links_for_comp:
                    sw_link = random.choice(links_for_comp)
                    
                    # Проверяем существование связи
                    existing_tractor_link = session.query(Tractor_Software_And_Component_Link).filter_by(
                        tractor_id=tractor.id,
                        soft_comp_link_id=sw_link.id
                    ).first()
                    
                    if not existing_tractor_link:
                        tractor_link = Tractor_Software_And_Component_Link(
                            is_recom=True,
                            tractor_id=tractor.id,
                            soft_comp_link_id=sw_link.id
                        )
                        session.add(tractor_link)
                        tractor_links_count += 1

        session.flush()
        print(f"✅ Добавлено {tractor_links_count} связей Трактор-ПО-Компоненты.")

        # --- 6. СОЗДАНИЕ ТЕСТОВЫХ СООБЩЕНИЙ С ПРАВИЛЬНОЙ СТРУКТУРОЙ (parent_message_id) ---
        if moderators and (dealers or engineers):
            print(f"\n📨 СОЗДАНИЕ ТЕСТОВЫХ СООБЩЕНИЙ С ДРЕВОВИДНОЙ СТРУКТУРОЙ")
            
            messages_created = 0
            replies_created = 0
            
            for moderator in moderators[:2]:  # Берем первых двух модераторов
                
                # Создаем сообщения от дилеров
                for dealer in dealers[:3]:  # Первые 3 дилера
                    # Каждый дилер создает 2-3 корневых сообщения
                    for _ in range(random.randint(2, 3)):
                        msg = SupportMessage(
                            content=f"Вопрос от дилера {dealer.username}: Проблема с трактором VIN_{random.randint(1,50):05d}",
                            sender_id=dealer.id,
                            is_read=False,
                            parent_message_id=None  # Корневое сообщение
                        )
                        session.add(msg)
                        session.flush()
                        messages_created += 1
                        
                        # Создаем статусы прочтения для всех модераторов
                        for mod in moderators:
                            read_status = MessageReadStatus(
                                message_id=msg.id,
                                moderator_id=mod.id,
                                is_read=(mod.id == moderator.id and random.choice([True, False])),  # Частично прочитаны
                                read_at=datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 24)) if random.choice([True, False]) else None
                            )
                            session.add(read_status)
                        
                        # Некоторые сообщения получают ответы от модераторов
                        if random.choice([True, False]):  # 50% сообщений получают ответ
                            for reply_mod in random.sample(moderators, random.randint(1, len(moderators))):
                                reply = SupportMessage(
                                    content=f"Ответ от модератора {reply_mod.username}: Проверьте настройки, возможно проблема в {random.choice(['гидравлике', 'ЭБУ', 'датчиках'])}",
                                    sender_id=reply_mod.id,
                                    is_read=False,
                                    parent_message_id=msg.id  # 👈 Связываем с родительским сообщением
                                )
                                session.add(reply)
                                session.flush()
                                replies_created += 1
                                
                                # Статусы прочтения для ответов
                                for mod in moderators:
                                    if mod.id != reply_mod.id:  # Ответчик уже прочитал свое сообщение
                                        read_status = MessageReadStatus(
                                            message_id=reply.id,
                                            moderator_id=mod.id,
                                            is_read=False,
                                            read_at=None
                                        )
                                        session.add(read_status)
                
                # Создаем сообщения от инженеров
                for engineer in engineers[:2]:  # Первые 2 инженера
                    for _ in range(random.randint(1, 2)):
                        msg = SupportMessage(
                            content=f"Технический вопрос от инженера {engineer.username}: Нужно обновление ПО для {random.choice(['двигателя', 'КПП', 'гидравлики'])}",
                            sender_id=engineer.id,
                            is_read=False,
                            parent_message_id=None  # Корневое сообщение
                        )
                        session.add(msg)
                        session.flush()
                        messages_created += 1
                        
                        # Статусы прочтения
                        for mod in moderators:
                            read_status = MessageReadStatus(
                                message_id=msg.id,
                                moderator_id=mod.id,
                                is_read=(mod.id == moderator.id and random.choice([True, False])),
                                read_at=datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 24)) if random.choice([True, False]) else None
                            )
                            session.add(read_status)
                        
                        # Ответы на технические вопросы (чаще получают ответы)
                        if random.choice([True, True, False]):  # 66% сообщений получают ответ
                            for reply_mod in random.sample(moderators, random.randint(1, len(moderators))):
                                reply = SupportMessage(
                                    content=f"Ответ от модератора {reply_mod.username}: Рекомендуем обновиться до версии {random.choice(['v2.0', 'v1.5', 'v3.0'])}",
                                    sender_id=reply_mod.id,
                                    is_read=False,
                                    parent_message_id=msg.id  # 👈 Связываем с родительским сообщением
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
            
            # Создаем цепочки из нескольких ответов (диалоги)
            if dealers and moderators:
                dealer = dealers[0]
                moderator = moderators[0]
                
                # Создаем диалог с несколькими ответами
                first_msg = SupportMessage(
                    content=f"Срочная проблема! Трактор {random.choice(['K-7', 'K-5'])} не заводится, код ошибки {random.randint(100, 999)}",
                    sender_id=dealer.id,
                    is_read=False,
                    parent_message_id=None
                )
                session.add(first_msg)
                session.flush()
                messages_created += 1
                
                for mod in moderators:
                    session.add(MessageReadStatus(message_id=first_msg.id, moderator_id=mod.id, is_read=False))
                
                # Первый ответ модератора
                reply1 = SupportMessage(
                    content=f"Модератор {moderator.username}: Проверьте предохранители и массу",
                    sender_id=moderator.id,
                    is_read=False,
                    parent_message_id=first_msg.id
                )
                session.add(reply1)
                session.flush()
                replies_created += 1
                
                for mod in moderators:
                    if mod.id != moderator.id:
                        session.add(MessageReadStatus(message_id=reply1.id, moderator_id=mod.id, is_read=False))
                
                # Ответ дилера
                reply2 = SupportMessage(
                    content=f"Дилер {dealer.username}: Предохранители целы, масса в норме. Ошибка {random.randint(100, 999)}",
                    sender_id=dealer.id,
                    is_read=False,
                    parent_message_id=first_msg.id  # Тоже относится к первому сообщению
                )
                session.add(reply2)
                session.flush()
                messages_created += 1  # Считаем как новое сообщение от дилера
                
                for mod in moderators:
                    session.add(MessageReadStatus(message_id=reply2.id, moderator_id=mod.id, is_read=False))
                
                # Второй ответ модератора
                reply3 = SupportMessage(
                    content=f"Модератор {moderator.username}: Попробуйте перепрошить ЭБУ. Нужна помощь?",
                    sender_id=moderator.id,
                    is_read=False,
                    parent_message_id=first_msg.id
                )
                session.add(reply3)
                session.flush()
                replies_created += 1
                
                for mod in moderators:
                    if mod.id != moderator.id:
                        session.add(MessageReadStatus(message_id=reply3.id, moderator_id=mod.id, is_read=False))
            
            print(f"✅ Создано сообщений с древовидной структурой:")
            print(f"   • Корневых сообщений: {messages_created}")
            print(f"   • Ответов: {replies_created}")
            print(f"   • Всего сообщений: {messages_created + replies_created}")

        # --- 7. Вывод статистики с проверкой древовидной структуры ---
        session.commit()
        
        print("\n" + "="*70)
        print("📊 СТАТИСТИКА ЗАПОЛНЕНИЯ БАЗЫ ДАННЫХ")
        print("="*70)
        print(f"\n🚜 Тракторы:")
        print(f"   • Всего: {len(tractors_data)}")
        
        print(f"\n🔧 Компоненты:")
        print(f"   • Всего: {len(components)}")
        
        print(f"\n💾 ПО:")
        print(f"   • Всего: {len(softwares)}")
        
        print(f"\n🔗 Связи:")
        print(f"   • ПО-Компоненты: {len(software_component_links)}")
        print(f"   • Трактор-ПО-Компоненты: {tractor_links_count}")
        
        # Статистика по сообщениям с древовидной структурой
        total_messages = session.query(SupportMessage).count()
        root_messages = session.query(SupportMessage).filter(SupportMessage.parent_message_id == None).count()
        replies = session.query(SupportMessage).filter(SupportMessage.parent_message_id != None).count()
        
        print(f"\n📨 Обратная связь (древовидная структура):")
        print(f"   • Всего сообщений: {total_messages}")
        print(f"   • Корневых сообщений: {root_messages}")
        print(f"   • Ответов: {replies}")
        print(f"   • Статусов прочтения: {session.query(MessageReadStatus).count()}")
        
        # Проверка работы backref
        if root_messages > 0:
            sample_root = session.query(SupportMessage).filter(SupportMessage.parent_message_id == None).first()
            if sample_root:
                reply_count = len(sample_root.replies)  # 👈 Проверка backref
                print(f"\n🔍 Проверка backref (на примере сообщения ID={sample_root.id}):")
                print(f"   • Ответов через backref: {reply_count}")
        
        print(f"\n✅ База данных успешно заполнена с поддержкой древовидной структуры сообщений!")
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