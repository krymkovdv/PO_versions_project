import logging
import sys

# Создание и настройка логгера приложения
logger = logging.getLogger("app")
logger.setLevel(logging.INFO)
logger.propagate = False

# Настройка обработчиков логов только если они еще не были добавлены
if not logger.handlers:
    # Форматтер для сообщений лога
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    # Обработчик для записи логов в файл
    file_handler = logging.FileHandler("app.log", encoding="utf-8")
    # Обработчик для вывода логов в консоль
    stream_handler = logging.StreamHandler(sys.stdout)
    # Применение форматтера к обработчикам
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    # Добавление обработчиков к логгеру
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)