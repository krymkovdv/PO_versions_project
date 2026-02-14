# import requests
# import time
# from datetime import datetime
# import json

# url = "https://agromonitor.kirovets-ptz.com/auth/login?jwt=1"
# data = {
#     # "login": "Kirovets_ptz36",
#     # "password": "MkVvTOP4TG"
#     "login": "Precision_machines",
#     "password": "de2_ty7NMX"
# }

# response = requests.post(url, json=data)
# # print(response)
# jwt = response.json()["jwt"]
# headers={"Authorization": jwt}

# date_from = int(datetime(2026, 2, 9).timestamp() * 1000)  # 1760025600000
# date_to = int(datetime(2026, 2, 14).timestamp() * 1000) 

# payload = {
#     "vehicleId": 1279000004,
#     "dateFrom": date_from,
#     "dateTo": date_to
# }



# # jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MTYxMDMyNzAsImxvZ2luIjoicnVkZW1vcnUiLCJ1dWlkIjoiM2ZlODMzZjgtNGE1OC0zZjc0LWI4NTUtZmU4MmExZWY1Nzc0IiwiYXV0b2NoZWNrX2lkIjoxMDc5ODAyLCJwZXJtaXNzaW9ucyI6WyIjVXNlciIsIm1hcHMueWFuZGV4Lm1hcCIsImFzZS5yZXBvcnRzLmV2ZW50cyIsImFzZS5yZXBvcnRzLmdyb3Vwc3RhdCIsImFzZS5yZXBvcnRzLmRyZCIsImFzZS5yZXBvcnRzLm1hcmNocm91dGUucm91dGVyZXBvcnQiLCJhc2UucmVwb3J0cy5kcml2ZXJzcmVwb3J0IiwiYXNlLnJlcG9ydHMuZ2Vvem9uZXNyZXBvcnQiLCJhc2UucmVwb3J0cy5mdWVsZXZlbnRzcmVwb3J0IiwiYXNlLnJlcG9ydHMuZ3JvdXBldmVudHMiLCJhc2UucmVwb3J0cy5ncm91cHdvcmsyIiwiYXNlLnJlcG9ydHMuc2hpZnRzIiwiYXNlLnJlcG9ydHMubW92ZW1lbnRieXN0YW5kcmVwb3J0IiwiYXNlLnJlcG9ydHMubWFyY2hyb3V0ZS5jdXJyZW50cnVucyIsImFzZS5yZXBvcnRzLmxvZyIsImFzZS5yZXBvcnRzLmRlbGl2ZXJ5IiwiYXNlLnJlcG9ydHMucGhvdG9yZXBvcnQiLCJhc2UucmVwb3J0cy5tYXAyIiwiYXNlLnJlcG9ydHMubG9jYXRpb24iLCJhc2UucmVwb3J0cy5mdWVsbGV2ZWxzIiwiYXNlLnJlcG9ydHMud29ya2Vkb3V0aG91cnMiLCJhc2UucmVwb3J0cy5lbmdpbmVycG0iLCJhc2UucmVwb3J0cy5zcGVlZCIsImFzZS5yZXBvcnRzLnZvbHRhZ2UiLCJhc2UucmVwb3J0cy51bml2ZXJzYWwiLCJhc2UucmVwb3J0cy5tb3ZlbWVudGJ5cGVyaW9kIiwiYXNlLnJlcG9ydHMud29ya2J5dGltZSIsImFzZS5yZXBvcnRzLmxvYWRieXRpbWUiLCJhc2UucmVwb3J0cy5tb3ZlbWVudGRpc3RyaWJ1dGlvbiIsImFzZS5yZXBvcnRzLndvcmtkaXN0cmlidXRpb25ieXRpbWUiLCJhc2UucmVwb3J0cy5sb2FkZGlzdHJpYnV0aW9uIiwiYXNlLnJlcG9ydHMuZ3JvdXByYXRpbmdzIiwiYXNlLnJlcG9ydHMuY29uc29saWRhdGVkcmVwb3J0IiwiYXNlLnJlcG9ydHMubG9jYXRpb24yIiwiYXNlLnJlcG9ydHMudHJhY2siLCJhc2UucmVwb3J0cy5tb3ZlbWVudGJ0d3N0YW5kcmVwb3J0IiwiYXNlLnJlcG9ydHMudGlyZXByZXNzdXJlIiwiYXNlLnJlcG9ydHZpc2liaWxpdHkiLCJtYXBzLndpa2kubWFwIiwibWFwcy5vbW5pY29tbS5tYXAiLCJtYXBzLm9tbmljb21tLmphbXMiLCJhc2UudXNlcnJlcG9ydHNjb250cm9sIiwiYXNlLnRwbXMiLCJhc2UubW9kYnVzZ2VuIiwic2VydmljZS5mdWVsYmFsYW5jZSIsImFzZS5mdWVsbWFzcyIsImZhcm1pbmcuYWNjZXNzIiwibmZ1ZWwuYWNjZXNzIiwiYXNlLmdyb3Vwcy52ZWhpY2xlLmN1c3RvbSIsImFzZS5ncm91cHMudmVoaWNsZS52aWV3IiwiYXNlLmdyb3Vwcy52ZWhpY2xlLnZpZXdwcm9maWxlIiwiYXNlLmdyb3Vwcy5kcml2ZXIuY3VzdG9tIiwiYXNlLmdyb3Vwcy5kcml2ZXIudmlldyIsImFzZS5ncm91cHMuZ2Vvem9uZS5jdXN0b20iLCJhc2UuZ3JvdXBzLmdlb3pvbmUudmlldyIsImFzZS5ncm91cHMucm91dGUuY3VzdG9tIiwiYXNlLmdyb3Vwcy5yb3V0ZS52aWV3IiwiYXNlLnJlcG9ydHMubWFuYWdlcnJlcG9ydCIsImFzZS5yZXBvcnRzLnJlZnJpZ2VyYXRvcnN0YXRlIiwic2VydmljZS5yZXBvcnRzLmZ1ZWxiYWxhbmNlIiwic2VydmljZS5yZXBvcnRzLmZ1ZWxzaGVldCIsInNlcnZpY2UucmVwb3J0cy5uZnVlbGRyZCIsInNlcnZpY2UucmVwb3J0cy5uZnVlbGdyb3Vwc3RhdCIsImFzZS5yZXBvcnRzLnBlcmlvZGljc2VydmljZSIsImFzZS5yZXBvcnRzLmxvY2F0aW9ucmVwb3J0Iiwic2VydmljZS5yZXBvcnRzLm5mdWVsbGV2ZWxzIiwiYXNlLnJlcG9ydHMucmVmcmlnZXJhdG9yd29yayIsImF1dG9jaGVjay5hY2Nlc3MiLCJzZXJ2aWNlLmJpbGxpbmcubmV3IiwibWFwcy53aWtpLm1hcCIsIm1hcHMuc3B1dG5pay5tYXAiLCJzZXJ2aWNlLmNvcHMucmVhZCIsInNlcnZpY2UuY29wcy51cGRhdGUiLCJzZXJ2aWNlLmNvcHMuYWRkIiwic2VydmljZS5DQU5fYnlfZW1kZCJdLCJkcml2ZXJncm91cF9pZCI6ImE3OTk4N2ExLTg3NTEtMzdjYi1hMWY5LTZlZWRjYjQxMmFlYiIsInZlaGljbGVncm91cF9pZCI6IjkyZjUwMTljLTI5MDgtMzdhMi04NWRlLTdmYTcwZmFmNWZiNiIsInVzZXJncm91cF9pZCI6bnVsbCwiZ2Vvem9uZWdyb3VwX2lkIjoiOWJlYzNlYWEtMGM2NS0zMDY2LTkzNTQtODM0MDIzOTUyYzdjIiwicm91dGVncm91cF9pZCI6ImUwMGQyODlmLTcxZTEtMzJmNC1hMWJlLTliZjIzMTQ2MjVjNCIsInNlcnZlcl9uYW1lIjoiZ29vc2UiLCJtYXhfcmVwb3J0X3BlcmlvZCI6MTIsInNlcnZlciI6eyJpZCI6MzEsImhvc3QiOiJodHRwOi8vMTAuNTUuNi4xMzEiLCJwb3J0Ijo4MDgwLCJzbHVnIjoiZ29vc2UiLCJmcWRuIjoiMTAuNTUuNi4xMzEiLCJ2b2x1bWVfdW5pdHMiOiJMIiwibGlnaHQiOjB9LCJyb2xlcyI6W3siaWQiOjQsIm5hbWUiOiJVc2VyIiwic2x1ZyI6InVzZXIiLCJ3ZWlnaHQiOjEwfV0sIndsIjp7fSwiaWF0IjoxNzU1MDY4NzY3LCJleHAiOjE3NTUwNzIzNjcsImF1ZCI6ImFzZSJ9.OHKz-mi6P-1qV723B_W-rYg0fRPn-vbOrSbmtS8x7LI"
# # url = "https://agromonitor.kirovets-ptz.com/ls/api/v1/click/log"
# # url_vehicles = "https://agromonitor.kirovets-ptz.com/ls/api/v2/activity/vehicles"
# # url_users = "https://agromonitor.kirovets-ptz.com/ls/api/v1/users"
# # url_log = "https://agromonitor.kirovets-ptz.com/ls/api/v1/click/log"
# url_tractor = "https://agromonitor.kirovets-ptz.com/ls/api/v1/click/log/additional"

# try:
#     # Отправка POST запроса с базовой аутентификацией
#     response = requests.post(
#         url_tractor,
#         json=payload,
#         headers={"Authorization": "JWT " + jwt},
#         timeout=30
#     )
    
#     # Вывод статуса и результата
#     print(f"Статус код: {response.status_code}")
    
#     if response.status_code == 200:
#         print(response.json())
# except requests.exceptions.RequestException as e:
#     print(f"Ошибка при выполнении запроса: {e}")


import requests
import time
from datetime import datetime
import json
import sys

def parse_json_safely(json_str):
    """Безопасный парсинг вложенного JSON"""
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # Попытка извлечь данные из обрезанной строки
        result = {}
        try:
            parts = json_str.strip('{}').split('","')
            for part in parts:
                if '":"' in part:
                    key, value = part.split('":', 1)
                    result[key.strip('"')] = value.strip('"')
        except:
            pass
        return result

def format_timestamp(ts):
    """Преобразование timestamp в читаемый формат"""
    try:
        dt = datetime.fromtimestamp(ts)
        return dt.strftime('%d.%m.%Y %H:%M:%S')
    except:
        return f"Некорректный timestamp: {ts}"

def display_page(records, page_num, page_size=5):
    """Отображение одной страницы данных"""
    start_idx = page_num * page_size
    end_idx = start_idx + page_size
    page_records = records[start_idx:end_idx]
    total_pages = (len(records) - 1) // page_size + 1
    
    print("\n" + "="*100)
    print(f"📖 СТРАНИЦА {page_num + 1} из {total_pages} | Всего записей: {len(records)}")
    print("="*100)
    
    if not page_records:
        print("⚠️  Нет записей для отображения")
        return
    
    for idx, record in enumerate(page_records, start=start_idx + 1):
        ts = record.get('eventDate', 0)
        time_str = format_timestamp(ts)
        
        print(f"\n{'─'*100}")
        print(f"📌 Запись #{idx:3d} | Время: {time_str} | Timestamp: {ts}")
        print(f"{'─'*100}")
        
        try:
            params = parse_json_safely(record.get('jsonData', '{}'))
            
            if not params:
                print("   ⚠️  Нет параметров")
                continue
            
            # Группировка по категориям
            categories = {
                "🌡️ Температура": [],
                "💨 Давление": [],
                "🔄 Обороты/Передачи": [],
                "⏱️ Моточасы/Пробег": [],
                "⛽ Расход/Загрузка": [],
                "🔧 Прочее": []
            }
            
            for name, value in params.items():
                name_clean = name.strip()
                name_lower = name_clean.lower()
                
                if "температура" in name_lower or "°с" in name_clean:
                    categories["🌡️ Температура"].append((name_clean, value))
                elif "давление" in name_lower or "кпа" in name_clean.lower():
                    categories["💨 Давление"].append((name_clean, value))
                elif "обороты" in name_lower or "передача" in name_lower or "об/мин" in name_clean:
                    categories["🔄 Обороты/Передачи"].append((name_clean, value))
                elif "моточас" in name_lower or "одометр" in name_lower or "км" in name_clean or "час" in name_lower:
                    categories["⏱️ Моточасы/Пробег"].append((name_clean, value))
                elif "расход" in name_lower or "загрузка" in name_lower or "л/ч" in name_clean or "%" in name_clean:
                    categories["⛽ Расход/Загрузка"].append((name_clean, value))
                else:
                    categories["🔧 Прочее"].append((name_clean, value))
            
            # Вывод категорий
            for category, items in categories.items():
                if items:
                    print(f"\n{category}")
                    for name, value in items:
                        print(f"   • {name:55} = {value}")
        
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            preview = record.get('jsonData', '')[:60]
            print(f"   Данные: {preview}...")
    
    print("\n" + "="*100)
    print("Управление: [n] след. | [p] пред. | [q] выход | [1-9] номер страницы")
    print("="*100)

def paginate_data(data, page_size=5):
    """Цикл пагинации"""
    records = data.get('exCanData', [])
    
    if not records:
        print("\n❌ Нет данных CAN-шины")
        return
    
    current_page = 0
    total_pages = (len(records) - 1) // page_size + 1
    
    while True:
        display_page(records, current_page, page_size)
        
        try:
            cmd = input("\n➡️  Команда: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\n\n👋 Прервано пользователем")
            break
        
        if cmd in ['q', 'quit', 'exit']:
            print("\n👋 До свидания!")
            break
        elif cmd in ['n', 'next']:
            if current_page < total_pages - 1:
                current_page += 1
            else:
                print("⚠️  Последняя страница")
        elif cmd in ['p', 'prev', 'previous']:
            if current_page > 0:
                current_page -= 1
            else:
                print("⚠️  Первая страница")
        elif cmd.isdigit():
            page_num = int(cmd) - 1
            if 0 <= page_num < total_pages:
                current_page = page_num
            else:
                print(f"⚠️  Неверная страница (1-{total_pages})")
        else:
            print("❓ Неизвестная команда")

def main():
    print("="*100)
    print("🚜 ЗАПРОС ТЕЛЕМЕТРИИ ТРАКТОРА | vehicleId: 1279000004")
    print("="*100)
    
    # 1. Авторизация (ИСПРАВЛЕНО: убраны лишние пробелы в URL!)
    print("\n🔐 Авторизация...")
    auth_url = "https://agromonitor.kirovets-ptz.com/auth/login?jwt=1"  # БЕЗ пробелов в конце!
    auth_data = {
        "login": "Precision_machines",
        "password": "de2_ty7NMX"
    }
    
    try:
        response = requests.post(auth_url, json=auth_data, timeout=10)
        response.raise_for_status()
        jwt_token = response.json()["jwt"]
        print("✅ Авторизация успешна")
    except Exception as e:
        print(f"❌ Ошибка авторизации: {e}")
        return
    
    # 2. Запрос данных (ИСПРАВЛЕНО: убраны лишние пробелы в URL!)
    print("\n📡 Запрос данных за период 04-05 февраля 2026...")
    date_from = int(datetime(2026, 2, 4).timestamp() * 1000)
    date_to = int(datetime(2026, 2, 5, 23, 59, 59).timestamp() * 1000)
    
    payload = {
        "vehicleId": 1279000004,
        "dateFrom": date_from,
        "dateTo": date_to
    }
    
    api_url = "https://agromonitor.kirovets-ptz.com/ls/api/v1/click/log/additional"  # БЕЗ пробелов!
    
    try:
        start = time.time()
        response = requests.post(
            api_url,
            json=payload,
            headers={"Authorization": f"JWT {jwt_token}"},
            timeout=30
        )
        elapsed = time.time() - start
        
        print(f"⏱️  Запрос выполнен за {elapsed:.2f} сек")
        print(f"📄 Статус: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Получено записей CAN: {len(data.get('exCanData', []))}")
            print(f"✅ Modbus записей: {len(data.get('modbusData', []))}")
            print(f"✅ Пользовательских параметров: {len(data.get('userParams', []))}")
            
            # 3. Запуск пагинации
            paginate_data(data, page_size=5)
            
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            print(f"📄 Ответ: {response.text[:200]}...")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка сети: {e}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Скрипт завершён")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()