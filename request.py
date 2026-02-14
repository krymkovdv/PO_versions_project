import requests
import time
from datetime import datetime
import json

url = "https://agromonitor.kirovets-ptz.com/auth/login?jwt=1"
data = {
    # "login": "Kirovets_ptz36",
    # "password": "MkVvTOP4TG"
    "login": "Precision_machines",
    "password": "de2_ty7NMX"
}

response = requests.post(url, json=data)
# print(response)
jwt = response.json()["jwt"]
headers={"Authorization": jwt}

date_from = int(datetime(2025, 10, 10).timestamp() * 1000)  # 1760025600000
date_to = int(datetime(2026, 10, 20).timestamp() * 1000) 

payload = {
    "vehicleId": 1279000004,
    "dateFrom": date_from,
    "dateTo": date_to
}



# jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MTYxMDMyNzAsImxvZ2luIjoicnVkZW1vcnUiLCJ1dWlkIjoiM2ZlODMzZjgtNGE1OC0zZjc0LWI4NTUtZmU4MmExZWY1Nzc0IiwiYXV0b2NoZWNrX2lkIjoxMDc5ODAyLCJwZXJtaXNzaW9ucyI6WyIjVXNlciIsIm1hcHMueWFuZGV4Lm1hcCIsImFzZS5yZXBvcnRzLmV2ZW50cyIsImFzZS5yZXBvcnRzLmdyb3Vwc3RhdCIsImFzZS5yZXBvcnRzLmRyZCIsImFzZS5yZXBvcnRzLm1hcmNocm91dGUucm91dGVyZXBvcnQiLCJhc2UucmVwb3J0cy5kcml2ZXJzcmVwb3J0IiwiYXNlLnJlcG9ydHMuZ2Vvem9uZXNyZXBvcnQiLCJhc2UucmVwb3J0cy5mdWVsZXZlbnRzcmVwb3J0IiwiYXNlLnJlcG9ydHMuZ3JvdXBldmVudHMiLCJhc2UucmVwb3J0cy5ncm91cHdvcmsyIiwiYXNlLnJlcG9ydHMuc2hpZnRzIiwiYXNlLnJlcG9ydHMubW92ZW1lbnRieXN0YW5kcmVwb3J0IiwiYXNlLnJlcG9ydHMubWFyY2hyb3V0ZS5jdXJyZW50cnVucyIsImFzZS5yZXBvcnRzLmxvZyIsImFzZS5yZXBvcnRzLmRlbGl2ZXJ5IiwiYXNlLnJlcG9ydHMucGhvdG9yZXBvcnQiLCJhc2UucmVwb3J0cy5tYXAyIiwiYXNlLnJlcG9ydHMubG9jYXRpb24iLCJhc2UucmVwb3J0cy5mdWVsbGV2ZWxzIiwiYXNlLnJlcG9ydHMud29ya2Vkb3V0aG91cnMiLCJhc2UucmVwb3J0cy5lbmdpbmVycG0iLCJhc2UucmVwb3J0cy5zcGVlZCIsImFzZS5yZXBvcnRzLnZvbHRhZ2UiLCJhc2UucmVwb3J0cy51bml2ZXJzYWwiLCJhc2UucmVwb3J0cy5tb3ZlbWVudGJ5cGVyaW9kIiwiYXNlLnJlcG9ydHMud29ya2J5dGltZSIsImFzZS5yZXBvcnRzLmxvYWRieXRpbWUiLCJhc2UucmVwb3J0cy5tb3ZlbWVudGRpc3RyaWJ1dGlvbiIsImFzZS5yZXBvcnRzLndvcmtkaXN0cmlidXRpb25ieXRpbWUiLCJhc2UucmVwb3J0cy5sb2FkZGlzdHJpYnV0aW9uIiwiYXNlLnJlcG9ydHMuZ3JvdXByYXRpbmdzIiwiYXNlLnJlcG9ydHMuY29uc29saWRhdGVkcmVwb3J0IiwiYXNlLnJlcG9ydHMubG9jYXRpb24yIiwiYXNlLnJlcG9ydHMudHJhY2siLCJhc2UucmVwb3J0cy5tb3ZlbWVudGJ0d3N0YW5kcmVwb3J0IiwiYXNlLnJlcG9ydHMudGlyZXByZXNzdXJlIiwiYXNlLnJlcG9ydHZpc2liaWxpdHkiLCJtYXBzLndpa2kubWFwIiwibWFwcy5vbW5pY29tbS5tYXAiLCJtYXBzLm9tbmljb21tLmphbXMiLCJhc2UudXNlcnJlcG9ydHNjb250cm9sIiwiYXNlLnRwbXMiLCJhc2UubW9kYnVzZ2VuIiwic2VydmljZS5mdWVsYmFsYW5jZSIsImFzZS5mdWVsbWFzcyIsImZhcm1pbmcuYWNjZXNzIiwibmZ1ZWwuYWNjZXNzIiwiYXNlLmdyb3Vwcy52ZWhpY2xlLmN1c3RvbSIsImFzZS5ncm91cHMudmVoaWNsZS52aWV3IiwiYXNlLmdyb3Vwcy52ZWhpY2xlLnZpZXdwcm9maWxlIiwiYXNlLmdyb3Vwcy5kcml2ZXIuY3VzdG9tIiwiYXNlLmdyb3Vwcy5kcml2ZXIudmlldyIsImFzZS5ncm91cHMuZ2Vvem9uZS5jdXN0b20iLCJhc2UuZ3JvdXBzLmdlb3pvbmUudmlldyIsImFzZS5ncm91cHMucm91dGUuY3VzdG9tIiwiYXNlLmdyb3Vwcy5yb3V0ZS52aWV3IiwiYXNlLnJlcG9ydHMubWFuYWdlcnJlcG9ydCIsImFzZS5yZXBvcnRzLnJlZnJpZ2VyYXRvcnN0YXRlIiwic2VydmljZS5yZXBvcnRzLmZ1ZWxiYWxhbmNlIiwic2VydmljZS5yZXBvcnRzLmZ1ZWxzaGVldCIsInNlcnZpY2UucmVwb3J0cy5uZnVlbGRyZCIsInNlcnZpY2UucmVwb3J0cy5uZnVlbGdyb3Vwc3RhdCIsImFzZS5yZXBvcnRzLnBlcmlvZGljc2VydmljZSIsImFzZS5yZXBvcnRzLmxvY2F0aW9ucmVwb3J0Iiwic2VydmljZS5yZXBvcnRzLm5mdWVsbGV2ZWxzIiwiYXNlLnJlcG9ydHMucmVmcmlnZXJhdG9yd29yayIsImF1dG9jaGVjay5hY2Nlc3MiLCJzZXJ2aWNlLmJpbGxpbmcubmV3IiwibWFwcy53aWtpLm1hcCIsIm1hcHMuc3B1dG5pay5tYXAiLCJzZXJ2aWNlLmNvcHMucmVhZCIsInNlcnZpY2UuY29wcy51cGRhdGUiLCJzZXJ2aWNlLmNvcHMuYWRkIiwic2VydmljZS5DQU5fYnlfZW1kZCJdLCJkcml2ZXJncm91cF9pZCI6ImE3OTk4N2ExLTg3NTEtMzdjYi1hMWY5LTZlZWRjYjQxMmFlYiIsInZlaGljbGVncm91cF9pZCI6IjkyZjUwMTljLTI5MDgtMzdhMi04NWRlLTdmYTcwZmFmNWZiNiIsInVzZXJncm91cF9pZCI6bnVsbCwiZ2Vvem9uZWdyb3VwX2lkIjoiOWJlYzNlYWEtMGM2NS0zMDY2LTkzNTQtODM0MDIzOTUyYzdjIiwicm91dGVncm91cF9pZCI6ImUwMGQyODlmLTcxZTEtMzJmNC1hMWJlLTliZjIzMTQ2MjVjNCIsInNlcnZlcl9uYW1lIjoiZ29vc2UiLCJtYXhfcmVwb3J0X3BlcmlvZCI6MTIsInNlcnZlciI6eyJpZCI6MzEsImhvc3QiOiJodHRwOi8vMTAuNTUuNi4xMzEiLCJwb3J0Ijo4MDgwLCJzbHVnIjoiZ29vc2UiLCJmcWRuIjoiMTAuNTUuNi4xMzEiLCJ2b2x1bWVfdW5pdHMiOiJMIiwibGlnaHQiOjB9LCJyb2xlcyI6W3siaWQiOjQsIm5hbWUiOiJVc2VyIiwic2x1ZyI6InVzZXIiLCJ3ZWlnaHQiOjEwfV0sIndsIjp7fSwiaWF0IjoxNzU1MDY4NzY3LCJleHAiOjE3NTUwNzIzNjcsImF1ZCI6ImFzZSJ9.OHKz-mi6P-1qV723B_W-rYg0fRPn-vbOrSbmtS8x7LI"
# url = "https://agromonitor.kirovets-ptz.com/ls/api/v1/click/log"
# url_vehicles = "https://agromonitor.kirovets-ptz.com/ls/api/v2/activity/vehicles"
# url_users = "https://agromonitor.kirovets-ptz.com/ls/api/v1/users"
# url_log = "https://agromonitor.kirovets-ptz.com/ls/api/v1/click/log"
url_tractor = "https://agromonitor.kirovets-ptz.com/ls/api/v1/click/log/additional"

try:
    # Отправка POST запроса с базовой аутентификацией
    response = requests.post(
        url_tractor,
        json=payload,
        headers={"Authorization": "JWT " + jwt},
        timeout=30
    )
    
    # Вывод статуса и результата
    print(f"Статус код: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        print("\n" + "="*80)
        print(f"ДАННЫЕ ТЕЛЕМЕТРИИ ТРАКТОРА (vehicleId: {payload['vehicleId']})")
        print("="*80)
        
        # Парсинг exCanData
        if data.get('exCanData'):
            print(f"\n📊 CAN-ДАННЫЕ ({len(data['exCanData'])} записей):\n")
            
            for idx, record in enumerate(data['exCanData'], 1):
                print(f"{'─'*80}")
                print(f"Запись #{idx}")
                print(f"{'─'*80}")
                
                # Временная метка
                event_date = record.get('eventDate')
                if event_date:
                    dt = datetime.fromtimestamp(event_date)
                    print(f"📅 Время: {dt.strftime('%d.%m.%Y %H:%M:%S')} ({event_date})")
                
                # Парсинг вложенного JSON
                json_data_str = record.get('jsonData', '{}')
                try:
                    json_data = json.loads(json_data_str)
                    
                    if json_data:
                        print(f"\nПараметры:")
                        print(f"{'─'*80}")
                        
                        # Сортируем параметры для красивого вывода
                        for param_name, param_value in sorted(json_data.items()):
                            # Форматируем название параметра
                            param_name_clean = param_name.strip()
                            
                            # Определяем категорию параметра для группировки
                            category = "⚙️ Прочее"
                            if "температура" in param_name.lower() or "°С" in param_name:
                                category = "🌡️ Температура"
                            elif "давление" in param_name.lower() or "кПа" in param_name:
                                category = "💨 Давление"
                            elif "обороты" in param_name.lower() or "об/мин" in param_name:
                                category = "🔄 Обороты"
                            elif "расход" in param_name.lower() or "л/ч" in param_name:
                                category = "⛽ Расход топлива"
                            elif "счётчик" in param_name.lower() or "моточас" in param_name.lower():
                                category = "⏱️ Моточасы"
                            elif "крутящий" in param_name.lower() or "%" in param_name:
                                category = "💪 Мощность/Момент"
                            elif "передача" in param_name.lower():
                                category = "🚗 Трансмиссия"
                            elif "загрузка" in param_name.lower():
                                category = "📈 Загрузка"
                            elif "одометр" in param_name.lower() or "км" in param_name:
                                category = "📍 Пробег"
                            
                            # Вывод параметра
                            print(f"{category:20} {param_name_clean:50} {param_value}")
                    
                    else:
                        print("⚠️ Нет данных")
                        
                except json.JSONDecodeError as e:
                    print(f"❌ Ошибка парсинга JSON: {e}")
                    print(f"   Данные: {json_data_str[:100]}...")
                
                print()
        
        else:
            print("\n📊 CAN-ДАННЫЕ: Нет записей")
        
        # Modbus данные
        if data.get('modbusData'):
            print(f"\n🔌 MODBUS-ДАННЫЕ ({len(data['modbusData'])} записей):")
            for idx, record in enumerate(data['modbusData'], 1):
                print(f"  {idx}. {record}")
        else:
            print(f"\n🔌 MODBUS-ДАННЫЕ: Нет записей")
        
        # Пользовательские параметры
        if data.get('userParams'):
            print(f"\n👤 ПОЛЬЗОВАТЕЛЬСКИЕ ПАРАМЕТРЫ ({len(data['userParams'])} записей):")
            for idx, record in enumerate(data['userParams'], 1):
                print(f"  {idx}. {record}")
        else:
            print(f"\n👤 ПОЛЬЗОВАТЕЛЬСКИЕ ПАРАМЕТРЫ: Нет записей")
        
        print("\n" + "="*80)
        
    else:
        print(f"Ошибка: {response.status_code}")
        print(f"Тело ответа: {response.text}")
        
except requests.exceptions.RequestException as e:
    print(f"Ошибка при выполнении запроса: {e}")



# print(jwt)
# response = requests.get(url_vehicles, headers={"Authorization": "JWT " + jwt})
# # print(response.json())
# if response.status_code == 200:
#     now = time.time()
#     # with open('./text.txt', mode="w+", encoding="utf-8") as f:
#     #     f.write(response.text)
#     data = response.json()
#     for each in data:
#         response = requests.post(url=url_log, json={
#             "terminalId": each['id'], "dateFrom": each["dateID"]//1000, "dateTo": each["dateID"]//1000}, headers={"Authorization": "JWT " + jwt})
#         print(response.text)
#     print(time.time()-now)
#     # response = requests.post(url=url_log, json={
#     #                                  "terminalId": data['objects'][0]['terminal_id'], "dateFrom": "1755175926", "dateTo": "1755176926"}, headers={"Authorization": "JWT " + jwt})
#     # print(response.json())
#     # url = "https://online.omnicomm.ru/ls/api/v1/clicl/"+data[0]["uuid"] + "/state/"
#     # # print(jwt)
#     # response = requests.get(url, headers={"Authorization": "JWT " + jwt})
# else:
#     # print(response.text)
#     pass
# # print(response.text)
