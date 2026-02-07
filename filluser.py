"""
Скрипт для добавления пользователя stringer через SQLAlchemy
Учитывает реальную структуру модели UserDB из вашего проекта
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
    from app.models import Base, UserDB  # ИСПРАВЛЕНО: UserDB вместо User
    from app.config import settings
    from passlib.context import CryptContext  # Используем passlib напрямую
except ImportError as e:
    logger.error(f"Ошибка импорта: {e}")
    logger.info("Попытка импорта альтернативных путей...")
    
    # Альтернативный импорт (адаптируйте под вашу структуру проекта)
    try:
        from models import UserDB
        from config import settings
        from passlib.context import CryptContext
    except ImportError as e2:
        logger.error(f"Не удалось импортировать зависимости: {e2}")
        logger.error("Убедитесь, что скрипт запускается из корня проекта")
        exit(1)


# Настройка контекста хеширования (должна совпадать с вашим приложением)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def add_user_stringer():
    """Добавление пользователя stringer в БД"""
    
    # Создание подключения к БД
    engine = create_engine(settings.get_url())
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        # Хеширование пароля
        plain_password = "string"
        hashed_password = pwd_context.hash(plain_password)
        
        logger.info(f"Сгенерирован хеш пароля: {hashed_password[:30]}...")
        
        # Создание пользователя (ИСПРАВЛЕНО: поля согласно модели UserDB)
        new_user = UserDB(
            username="stringer",
            password_hash=hashed_password,  # ИСПРАВЛЕНО: password_hash вместо hashed_password
            role="moderator"                # ИСПРАВЛЕНО: нет полей email, is_active, created_at
        )
        
        # Добавление в сессию
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        
        logger.info(f"✅ Пользователь успешно создан:")
        logger.info(f"   ID: {new_user.id}")
        logger.info(f"   Username: {new_user.username}")
        logger.info(f"   Role: {new_user.role}")
        
        return True
        
    except IntegrityError as e:
        session.rollback()
        
        # Проверка на дубликат по уникальному полю username
        if "username" in str(e.orig).lower() or "unique" in str(e.orig).lower():
            logger.warning("⚠️ Пользователь 'stringer' уже существует. Обновление данных...")
            
            # Обновление существующего пользователя
            existing_user = session.query(UserDB).filter(UserDB.username == "stringer").first()
            if existing_user:
                existing_user.password_hash = pwd_context.hash("string")
                existing_user.role = "moderator"
                session.commit()
                session.refresh(existing_user)
                
                logger.info(f"✅ Данные пользователя обновлены:")
                logger.info(f"   ID: {existing_user.id}")
                logger.info(f"   Role: {existing_user.role}")
                return True
            else:
                logger.error("Не удалось найти существующего пользователя для обновления")
                return False
        else:
            logger.error(f"Ошибка целостности БД: {e}")
            return False
            
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Ошибка при добавлении пользователя: {e}", exc_info=True)
        return False
        
    finally:
        session.close()


def verify_user_exists():
    """Проверка существования пользователя в БД"""
    
    engine = create_engine(settings.get_url())
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        user = session.query(UserDB).filter(UserDB.username == "stringer").first()
        
        if user:
            logger.info(f"\n🔍 Проверка пользователя в БД:")
            logger.info(f"   Найден пользователь: {user.username}")
            logger.info(f"   Роль: {user.role}")
            logger.info(f"   Хеш пароля (превью): {user.password_hash[:20]}...")
            return True
        else:
            logger.warning("❌ Пользователь 'stringer' не найден в БД")
            return False
            
    finally:
        session.close()


if __name__ == "__main__":
    logger.info("="*60)
    logger.info("Добавление пользователя 'stringer' (роль: moderator)")
    logger.info("="*60)
    
    # Шаг 1: Добавление/обновление пользователя
    success = add_user_stringer()
    
    if success:
        # Шаг 2: Проверка существования
        verify_user_exists()
        
        logger.info("\n" + "="*60)
        logger.info("✅ Пользователь 'stringer' готов к использованию!")
        logger.info("   Логин: stringer")
        logger.info("   Пароль: string")
        logger.info("   Роль: moderator")
        logger.info("="*60)
    else:
        logger.error("\n❌ Не удалось добавить пользователя. Проверьте логи выше.")
        exit(1)