# fill_realistic_data.py
from datetime import datetime, timezone, timedelta, date
from app.database import get_session
from app.models import (
    Tractor,
    Component,
    Software,
    Software_Component_Link,
    Tractor_Software_And_Component_Link,
)
from sqlalchemy.orm import Session
import random


def fill_realistic_data():
    session: Session = next(get_session())

    try:
        print("Заполняем базу данных реалистичными данными...")

        # --- 1. Тракторы ---
        models_pool = ["K-7", "K-525", "K-742МСТ", "K-5", "K-700", "K-744", "K-530T", "K-730M", "K-714"]
        regions = ["RU-MOS", "RU-SPE", "RU-KRA", "RU-ROS", "RU-TAT", "RU-BAS", "RU-SYS"]
        consumers = ["АгроТехСервис", "Кировец-Центр", "СельхозМаш", "АгроИнвест",
                     "ТехноАгро", "РосАгроМаш", "АгроКомплект", "Механизатор",
                     "АгроСервисПлюс", "ТракторныйДом"]
        dealers = ["СЦ-Москва", "СЦ-СПб", "СЦ-Краснодар", "СЦ-Ростов",
                   "СЦ-Казань", "СЦ-Уфа", "СЦ-Воронеж", "СЦ-Саратов", "СЦ-Системный"]

        tractors = []
        # Обычные тракторы (15 штук)
        for i in range(1, 16):
            model = random.choice(models_pool)
            tractor = Tractor(
                model=model,
                vin=f"VIN_{i:05d}",
                oh_hour=random.randint(50, 5000),
                last_activity=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 60)),
                assembly_date=datetime.now(timezone.utc) - timedelta(days=random.randint(30, 1500)),
                region=random.choice(regions),
                consumer=random.choice(consumers),
                dealer=random.choice(dealers)
            )
            session.add(tractor)
            tractors.append(tractor)

        # Системные тракторы (5 штук) — с особым VIN
        for i in range(1, 6):
            model = random.choice(models_pool)
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
            tractors.append(tractor)

        session.flush()
        print(f"✅ Добавлено {len(tractors)} тракторов (15 обычных + 5 системных).")

        # --- 2. Компоненты ---
        components_data = [
            {"type": "DVS", "name": "ДВС Weichai WP12", "producer": "Weichai"},
            {"type": "KPP", "name": "КПП-728", "producer": "Кировец"},
            {"type": "RK", "name": "Рулевая колонка РК-7", "producer": "Кировец"},
            {"type": "HR", "name": "Гидрораспределитель Р-80", "producer": "Гидросила"},
            {"type": "BK", "name": "БК-Агро v2", "producer": "АгроЭлектроника"},
        ]

        components = []
        for c_data in components_data:
            comp = Component(**c_data)
            session.add(comp)
            components.append(comp)

        session.flush()
        print(f"✅ Добавлено {len(components)} компонентов.")
# --- 3. ПО (Software) ---
        # Для каждого компонента создадим 2-3 версии ПО
        softwares_data = [
            # DVS
            {"path": "weichai_v1.0.bin", "release_date": datetime(2023, 1, 15),
             "description": "Базовая прошивка ДВС Weichai", "producer": "Weichai",
             "is_actual": False, "is_archive": False, "is_critical": False,
             "status": "serial", "tractor_model": "Universal",
             "path_instruction": "weichai_v1.0_manual.pdf"},
            {"path": "weichai_v2.0.bin", "release_date": datetime(2024, 1, 10),
             "description": "Major обновление экологии Euro-5", "producer": "Weichai",
             "is_actual": True, "is_archive": False, "is_critical": True,
             "status": "serial", "tractor_model": "Universal",
             "path_instruction": "weichai_v2.0_manual.pdf"},
            # KPP
            {"path": "kpp728_v1.0.bin", "release_date": datetime(2023, 5, 1),
             "description": "Базовая прошивка КПП-728", "producer": "Кировец",
             "is_actual": False, "is_archive": False, "is_critical": False,
             "status": "serial", "tractor_model": "Universal",
             "path_instruction": "kpp728_v1.0_manual.pdf"},
            {"path": "kpp728_v2.0.bin", "release_date": datetime(2024, 2, 1),
             "description": "Major обновление КПП-728", "producer": "Кировец",
             "is_actual": True, "is_archive": False, "is_critical": False,
             "status": "serial", "tractor_model": "Universal",
             "path_instruction": "kpp728_v2.0_manual.pdf"},
            # RK
            {"path": "rk7_v1.0.bin", "release_date": datetime(2023, 6, 1),
             "description": "Базовая прошивка рулевого", "producer": "Кировец",
             "is_actual": True, "is_archive": False, "is_critical": False,
             "status": "serial", "tractor_model": "Universal",
             "path_instruction": "rk7_v1.0_manual.pdf"},
            # HR
            {"path": "hr80_v1.0.bin", "release_date": datetime(2023, 3, 15),
             "description": "Базовая прошивка гидравлики", "producer": "Гидросила",
             "is_actual": False, "is_archive": False, "is_critical": False,
             "status": "experienced", "tractor_model": "Universal",
             "path_instruction": "hr80_v1.0_manual.pdf"},
            {"path": "hr80_v2.0.bin", "release_date": datetime(2024, 4, 1),
             "description": "Major обновление гидравлики", "producer": "Гидросила",
             "is_actual": True, "is_archive": False, "is_critical": False,
             "status": "serial", "tractor_model": "Universal",
             "path_instruction": "hr80_v2.0_manual.pdf"},
            # BK
            {"path": "bk_v1.5.bin", "release_date": datetime(2024, 1, 1),
             "description": "Minor обновление БК", "producer": "АгроЭлектроника",
             "is_actual": False, "is_archive": False, "is_critical": False,
             "status": "experienced", "tractor_model": "Universal",
             "path_instruction": "bk_v1.5_manual.pdf"},
            {"path": "bk_v2.0.bin", "release_date": datetime(2024, 5, 1),
             "description": "Major обновление БК", "producer": "АгроЭлектроника",
             "is_actual": True, "is_archive": False, "is_critical": False,
             "status": "serial", "tractor_model": "Universal",
             "path_instruction": "bk_v2.0_manual.pdf"},
        ]

        # Создаём ПО, пока без previous_sw_version
        software_objects = []
        for sw_data in softwares_data:
            # Заполним end_actuality для устаревших версий
            if not sw_data["is_actual"]:
                sw_data["end_actuality"] = datetime(2024, 6, 1)
            sw = Software(**sw_data)
            session.add(sw)
            software_objects.append(sw)

        session.flush()
# Устанавливаем previous_sw_version для связей версий (по именам)
        # В реальности можно связать по логике, но для простоты оставим NULL.
        # Если нужно, можно добавить логику здесь.
        print(f"✅ Добавлено {len(software_objects)} ПО.")

        # --- 4. Связи ПО <-> Компонент (Software_Component_Link) ---
        # Определим, какие версии к каким компонентам относятся
        comp_map = {comp.name: comp for comp in components}
        sw_map = {sw.path: sw for sw in software_objects}

        # Связка: компонент -> список путей ПО
        comp_sw_paths = {
            "ДВС Weichai WP12": ["weichai_v1.0.bin", "weichai_v2.0.bin"],
            "КПП-728": ["kpp728_v1.0.bin", "kpp728_v2.0.bin"],
            "Рулевая колонка РК-7": ["rk7_v1.0.bin"],
            "Гидрораспределитель Р-80": ["hr80_v1.0.bin", "hr80_v2.0.bin"],
            "БК-Агро v2": ["bk_v1.5.bin", "bk_v2.0.bin"],
        }

        soft_comp_links = []
        for comp_name, sw_paths in comp_sw_paths.items():
            comp = comp_map.get(comp_name)
            if not comp:
                continue
            for path in sw_paths:
                sw = sw_map.get(path)
                if not sw:
                    continue
                link = Software_Component_Link(
                    component_id=comp.id,
                    software_id=sw.id
                )
                session.add(link)
                soft_comp_links.append(link)

        session.flush()
        print(f"✅ Добавлено {len(soft_comp_links)} связей ПО-компонент.")

        # --- 5. Установка ПО на тракторы (Tractor_Software_And_Component_Link) ---
        # Для каждого трактора и каждого компонента выберем одну из доступных версий ПО
        # и создадим запись, указывающую, что эта версия установлена.
        # Для обычных тракторов (первые 15) и для системных (последние 5) сделаем одинаково.

        # Сгруппируем ссылки по компоненту для удобства выбора
        links_by_component = {}
        for link in soft_comp_links:
            comp_id = link.component_id
            links_by_component.setdefault(comp_id, []).append(link)

        tractor_links = []
        for tractor in tractors:
            for comp in components:
                available_links = links_by_component.get(comp.id, [])
                if not available_links:
                    continue
                # Случайно выбираем одну из версий (можно сделать bias к актуальным)
                chosen_link = random.choice(available_links)
                # Флаг is_recom: True, если выбранная версия является последней (по дате релиза)
                # Упростим: будем считать рекомендуемой ту, у которой is_actual = True
                sw = session.get(Software, chosen_link.software_id)
                is_recom = sw.is_actual if sw else False

                t_link = Tractor_Software_And_Component_Link(
                    tractor_id=tractor.id,
                    soft_comp_link_id=chosen_link.id,
                    is_recom=is_recom
                )
                session.add(t_link)
                tractor_links.append(t_link)

        session.flush()
        print(f"✅ Добавлено {len(tractor_links)} записей о ПО на тракторах.")

        # --- 6. Коммит ---
        session.commit()

        print("\n" + "=" * 70)
        print("✅ РЕАЛИСТИЧНЫЕ ДАННЫЕ УСПЕШНО ДОБАВЛЕНЫ!")
        print("=" * 70)
        print(f"\n📊 Итоговая статистика:")
        print(f"   • Тракторов: {len(tractors)}")
        print(f"   • Компонентов: {len(components)}")
        print(f"   • ПО: {len(software_objects)}")
        print(f"   • Связей ПО-компонент: {len(soft_comp_links)}")
        print(f"   • Записей о ПО на тракторах: {len(tractor_links)}")

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