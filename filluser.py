"""
Скрипт для добавления пользователей через SQLAlchemy
Учитывает обновленную структуру модели UserDB с поддержкой обратной связи
"""

from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Импорт моделей и конфигурации из вашего приложения
try:
    from app.models import Base, UserDB, SupportMessage, MessageReadStatus
    from app.config import settings
    from passlib.context import CryptContext
except ImportError as e:
    logger.error(f"Ошибка импорта: {e}")
    logger.info("Попытка импорта альтернативных путей...")
    try:
        from models import UserDB, SupportMessage, MessageReadStatus
        from config import settings
        from passlib.context import CryptContext
    except ImportError as e2:
        logger.error(f"Не удалось импортировать зависимости: {e2}")
        logger.error("Убедитесь, что скрипт запускается из корня проекта")
        exit(1)

# Настройка контекста хеширования (должна совпадать с вашим приложением)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def add_user(username: str, password: str, role: str) -> bool:
    """
    Универсальная функция добавления/обновления пользователя
    
    Args:
        username: Имя пользователя
        password: Пароль в открытом виде
        role: Роль пользователя ('moderator', 'dealer', 'engineer')
    
    Returns:
        bool: True если успешно, False если ошибка
    """
    engine = create_engine(settings.get_url())
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        # Хеширование пароля
        hashed_password = pwd_context.hash(password)
        logger.info(f"🔐 Генерация хеша для '{username}'...")
        
        # Создание пользователя
        new_user = UserDB(
            username=username,
            password_hash=hashed_password,
            role=role
        )
        
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        
        logger.info(f"✅ Пользователь '{username}' успешно создан:")
        logger.info(f"   ID: {new_user.id} | Роль: {new_user.role}")
        return True
        
    except IntegrityError as e:
        session.rollback()
        
        # Проверка на дубликат username
        if "username" in str(e.orig).lower() or "unique" in str(e.orig).lower():
            logger.warning(f"⚠️ Пользователь '{username}' уже существует. Обновление...")
            
            existing_user = session.query(UserDB).filter(UserDB.username == username).first()
            if existing_user:
                existing_user.password_hash = pwd_context.hash(password)
                existing_user.role = role
                session.commit()
                session.refresh(existing_user)
                
                logger.info(f"✅ Данные пользователя '{username}' обновлены:")
                logger.info(f"   ID: {existing_user.id} | Роль: {existing_user.role}")
                return True
            else:
                logger.error(f"Не удалось найти пользователя '{username}' для обновления")
                return False
        else:
            logger.error(f"❌ Ошибка целостности БД для '{username}': {e}")
            return False
            
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Ошибка при добавлении '{username}': {e}", exc_info=True)
        return False
        
    finally:
        session.close()


def add_user_stringer() -> bool:
    """Добавление пользователя stringer (moderator)"""
    return add_user(username="stringer", password="string", role="moderator")


def add_user_engineer() -> bool:
    """Добавление пользователя engineer"""
    return add_user(username="engineer", password="engineer", role="engineer")


def add_user_dealer() -> bool:
    """
    Добавление пользователя dealer с именем дилера из БД.
    Имя совпадает с одним из дилеров: "АгроТехСервис"
    """
    dealer_name = "АгроТехСервис"
    return add_user(username=dealer_name, password="dealer123", role="dealer")


def add_user_dealer2() -> bool:
    """Дополнительный дилер для тестирования"""
    return add_user(username="ТехноАгро", password="dealer123", role="dealer")


def add_user_dealer3() -> bool:
    """Дополнительный дилер для тестирования"""
    return add_user(username="АгроИмпорт", password="dealer123", role="dealer")


def verify_user_exists(username: str) -> bool:
    """Проверка существования пользователя в БД"""
    engine = create_engine(settings.get_url())
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        user = session.query(UserDB).filter(UserDB.username == username).first()
        
        if user:
            logger.info(f"🔍 Найден: {user.username} | Роль: {user.role} | ID: {user.id} | Хеш: {user.password_hash[:20]}...")
            
            # Проверяем связи с сообщениями (опционально)
            sent_count = session.query(SupportMessage).filter(SupportMessage.sender_id == user.id).count()
            read_status_count = session.query(MessageReadStatus).filter(MessageReadStatus.moderator_id == user.id).count()
            
            logger.info(f"   📨 Отправлено сообщений: {sent_count}")
            if user.role == "moderator":
                logger.info(f"   👁️ Статусов прочтения: {read_status_count}")
            
            return True
        else:
            logger.warning(f"❌ Пользователь '{username}' не найден в БД")
            return False
    finally:
        session.close()


def get_all_users() -> None:
    """Получение списка всех пользователей в БД"""
    engine = create_engine(settings.get_url())
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        users = session.query(UserDB).order_by(UserDB.id).all()
        
        logger.info("\n" + "="*70)
        logger.info("📋 ВСЕ ПОЛЬЗОВАТЕЛИ В СИСТЕМЕ")
        logger.info("="*70)
        
        for user in users:
            sent_count = session.query(SupportMessage).filter(SupportMessage.sender_id == user.id).count()
            logger.info(f"ID: {user.id:3} | {user.username:20} | Роль: {user.role:10} | Сообщений: {sent_count}")
        
        logger.info("="*70)
        logger.info(f"Всего пользователей: {len(users)}")
        
    finally:
        session.close()


if __name__ == "__main__":
    logger.info("="*70)
    logger.info("👥 ДОБАВЛЕНИЕ ПОЛЬЗОВАТЕЛЕЙ В БАЗУ ДАННЫХ")
    logger.info("="*70)
    
    # Список пользователей для создания
    users_to_create = [
        {"func": add_user_stringer, "name": "stringer", "role": "moderator", "password": "string"},
        {"func": add_user_engineer, "name": "engineer", "role": "engineer", "password": "engineer"},
        {"func": add_user_dealer, "name": "АгроТехСервис", "role": "dealer", "password": "dealer123"},
        {"func": add_user_dealer2, "name": "ТехноАгро", "role": "dealer", "password": "dealer123"},
        {"func": add_user_dealer3, "name": "АгроИмпорт", "role": "dealer", "password": "dealer123"},
    ]
    
    results = []
    
    for user_info in users_to_create:
        logger.info(f"\n📝 Создание пользователя: {user_info['name']} ({user_info['role']})")
        logger.info("-"*50)
        success = user_info["func"]()
        results.append((user_info["name"], user_info["role"], success))
    
    # Проверка всех пользователей
    logger.info("\n" + "="*70)
    logger.info("🔍 ПРОВЕРКА СУЩЕСТВОВАНИЯ ПОЛЬЗОВАТЕЛЕЙ")
    logger.info("="*70)
    
    all_ok = True
    for name, role, _ in results:
        exists = verify_user_exists(name)
        if not exists:
            all_ok = False
    
    # Показываем всех пользователей в системе
    get_all_users()
    
    # Итоговый отчёт
    logger.info("\n" + "="*70)
    logger.info("📋 ИТОГОВЫЙ ОТЧЁТ")
    logger.info("="*70)
    
    for name, role, success in results:
        status = "✅" if success else "❌"
        logger.info(f"{status} {name:20} | Роль: {role:10} | {'Успешно' if success else 'Ошибка'}")
    
    if all_ok:
        logger.info("\n🎉 ВСЕ ПОЛЬЗОВАТЕЛИ ГОТОВЫ К ИСПОЛЬЗОВАНИЮ!")
        logger.info("\n🔑 Учётные данные для входа:")
        logger.info("   • stringer        | Пароль: string      | Роль: moderator")
        logger.info("   • engineer        | Пароль: engineer    | Роль: engineer")
        logger.info("   • АгроТехСервис   | Пароль: dealer123   | Роль: dealer")
        logger.info("   • ТехноАгро        | Пароль: dealer123   | Роль: dealer")
        logger.info("   • АгроИмпорт       | Пароль: dealer123   | Роль: dealer")
        
        logger.info("\n📨 Для тестирования обратной связи:")
        logger.info("   - Отправляйте сообщения от dealer или engineer к moderator")
        logger.info("   - Модератор stringer увидит все сообщения")
        logger.info("   - Статус прочтения отслеживается в MessageReadStatus")
    else:
        logger.error("\n❌ Не все пользователи созданы. Проверьте логи выше.")
        exit(1)
    
    logger.info("="*70)