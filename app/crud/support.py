# app/crud/support.py
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from .. import models
from ..log import logger
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from collections import defaultdict
from sqlalchemy import func

class SupportCRUD:
    
    @staticmethod
    def send_message_to_moderators(db: Session, user_id: int, content: str) -> models.SupportMessage:
        """Отправка сообщения всем модераторам"""
        new_message = models.SupportMessage(
            sender_id=user_id,
            content=content,
            is_read=False
        )
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        
        # Создаём записи о статусе прочтения для всех модераторов
        moderators = db.query(models.UserDB).filter(
            models.UserDB.role == "moderator"
        ).all()
        
        for mod in moderators:
            read_status = models.MessageReadStatus(
                message_id=new_message.id,
                moderator_id=mod.id,
                is_read=False
            )
            db.add(read_status)
        
        db.commit()
        logger.info(f"[support] Сообщение отправлено: message_id={new_message.id}, user_id={user_id}")
        return new_message
    
    @staticmethod
    def moderator_reply(db: Session, moderator_id: int, message_id: int, content: str) -> Optional[Dict[str, Any]]:
        """Ответ модератора на сообщение"""
        original_message = db.query(models.SupportMessage).filter(
            models.SupportMessage.id == message_id
        ).first()
        
        if not original_message:
            return None
        
        reply = models.SupportMessage(
            sender_id=moderator_id,
            content=content,
            parent_message_id=message_id,
            is_read=False
        )
        db.add(reply)
        db.commit()
        db.refresh(reply)
        
        logger.info(f"[support] Ответ отправлен: reply_id={reply.id}, original_id={message_id}")
        
        return {
            "reply": reply,
            "original_message": original_message
        }
    
    # ========== НОВЫЕ МЕТОДЫ ДЛЯ УДАЛЕНИЯ (без изменений БД) ==========
    
    @staticmethod
    def delete_message(
        db: Session, 
        message_id: int, 
        user_id: int, 
        user_role: str
    ) -> Dict[str, Any]:
        """
        Удаление сообщения (физическое удаление из БД)
        
        Правила:
        - Пользователи могут удалять только свои сообщения
        - Модераторы могут удалять любые сообщения
        - При удалении родительского сообщения удаляются все ответы (каскад через ORM)
        """
        message = db.query(models.SupportMessage).filter(
            models.SupportMessage.id == message_id
        ).first()
        
        if not message:
            logger.warning(f"[support/delete] Сообщение не найдено: id={message_id}")
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Проверка прав доступа
        if user_role != "moderator" and message.sender_id != user_id:
            logger.warning(
                f"[support/delete] Недостаточно прав: user_id={user_id}, "
                f"message_sender={message.sender_id}, role={user_role}"
            )
            raise HTTPException(
                status_code=403, 
                detail="You can only delete your own messages"
            )
        
        # Подсчёт ответов для каскадного удаления
        cascade_count = 0
        if message.parent_message_id is None:  # Это родительское сообщение
            cascade_count = db.query(models.SupportMessage).filter(
                models.SupportMessage.parent_message_id == message_id
            ).count()
        
        # Удаляем все связанные записи о прочтении
        db.query(models.MessageReadStatus).filter(
            models.MessageReadStatus.message_id == message_id
        ).delete()
        
        # Удаляем все ответы (каскад)
        if cascade_count > 0:
            db.query(models.SupportMessage).filter(
                models.SupportMessage.parent_message_id == message_id
            ).delete()
        
        # Логирование перед удалением
        logger.info(
            f"[support/delete] Удаление сообщения: id={message_id}, "
            f"sender={message.sender_id}, by={user_id}, role={user_role}, "
            f"cascade={cascade_count}, content_preview={message.content[:50]}"
        )
        
        # Удаляем само сообщение
        db.delete(message)
        db.commit()
        
        return {
            "message_id": message_id,
            "deleted_at": datetime.now(timezone.utc),
            "deleted_by": user_id,
            "cascade_deleted": cascade_count
        }
    
    from datetime import datetime, timezone


    @staticmethod
    def get_all_user_messages(db: Session, user_id: int):
        # 1. Получаем все корневые сообщения пользователя
        root_messages = db.query(models.SupportMessage).filter(
            models.SupportMessage.sender_id == user_id,
            models.SupportMessage.parent_message_id == None
        ).all()
        
        if not root_messages:
            return []

        # 2. Собираем ID корневых сообщений для оптимизации запросов
        root_ids = [msg.id for msg in root_messages]

        # 3. Получаем ВСЕ ответы на эти сообщения одним запросом (вместо цикла)
        all_replies = db.query(models.SupportMessage).filter(
            models.SupportMessage.parent_message_id.in_(root_ids)
        ).all()


        replies_by_parent = defaultdict(list)
        for reply in all_replies:
            if not reply.is_read:
                reply.is_read = True
                # Если нужно фиксировать время прочтения в самой таблице сообщений (если бы было поле read_at)
                # reply.read_at = datetime.now(timezone.utc) 
            replies_by_parent[reply.parent_message_id].append(reply)

        result = []
        
        for msg in root_messages:
            # 5. Получаем статусы прочтения (для модераторов) для корневого сообщения
            read_statuses = db.query(models.MessageReadStatus).filter(
                models.MessageReadStatus.message_id == msg.id
            ).all()

            read_by = [
                {
                    "moderator": status.moderator_id,
                    "read_at": status.read_at,
                    "is_read": status.is_read
                }
                for status in read_statuses
            ]
            
            # 6. Формируем список ответов для текущего сообщения
            current_replies = replies_by_parent.get(msg.id, [])
            
            result.append({
                "id": msg.id,
                "content": msg.content,
                "created_at": msg.created_at,
                "is_read": msg.is_read,
                "is_closed": msg.is_closed,
                "read_by": read_by,
                "replies": [{"id": r.id, "content": r.content, "is_read": r.is_read} for r in current_replies]
            })
        
        # 7. ✅ СОХРАНЯЕМ изменения в базе (самое важное!)
        # Это запишет is_read = True для всех ответов в базу данных
        db.commit()
        
        return result

    @staticmethod
    def get_messages_for_moderator(db: Session, moderator_id: int) -> List[Dict[str, Any]]:
        """Получить все сообщения для модератора"""
        users = db.query(models.UserDB).filter(
            models.UserDB.role != "moderator"
        ).all()
        
        result = []
        for user in users:
            messages = db.query(models.SupportMessage).filter(
                models.SupportMessage.sender_id == user.id,
                models.SupportMessage.parent_message_id == None
            ).order_by(models.SupportMessage.created_at.desc()).all()
            
            if messages:
                user_messages = []
                for msg in messages:
                    replies = db.query(models.SupportMessage).filter(
                        models.SupportMessage.parent_message_id == msg.id
                    ).order_by(models.SupportMessage.created_at.asc()).all()
                    
                    user_messages.append({
                        "id": msg.id,
                        "content": msg.content,
                        "created_at": msg.created_at,
                        "is_read": msg.is_read,
                        "is_closed": msg.is_closed,
                        "replies": [
                            {
                                "id": reply.id,
                                "content": reply.content,
                                "created_at": reply.created_at,
                                "moderator_name": reply.moderator_name if hasattr(reply, 'moderator_name') else "Модератор"
                            }
                            for reply in replies
                        ]
                    })
                
                result.append({
                    "user_id": user.id,
                    "username": user.username,
                    "role": user.role,
                    "messages": user_messages
                })
        
        return result
    
    @staticmethod
    def mark_as_read(db: Session, message_id: int, moderator_id: int) -> bool:
        """Отметить сообщение как прочитанное"""
        read_status = db.query(models.MessageReadStatus).filter(
            models.MessageReadStatus.message_id == message_id,
            models.MessageReadStatus.moderator_id == moderator_id
        ).first()
        
        if not read_status:
            # Создаём запись если её нет
            read_status = models.MessageReadStatus(
                message_id=message_id,
                moderator_id=moderator_id,
                is_read=True,
                read_at=datetime.now(timezone.utc)
            )
            db.add(read_status)
            db.commit()
            return True
        
        read_status.is_read = True
        read_status.read_at = datetime.now(timezone.utc)
        db.commit()
        
        return True
    
    @staticmethod
    def get_unread_count(db: Session, moderator_id: int) -> int:
        """Получить количество непрочитанных сообщений"""
        count = db.query(models.MessageReadStatus).join(
            models.SupportMessage,
            models.MessageReadStatus.message_id == models.SupportMessage.id
        ).filter(
            models.MessageReadStatus.moderator_id == moderator_id,
            models.MessageReadStatus.is_read == False
        ).count()
        
        return count
    
    @staticmethod
    def get_all_moderators(db: Session) -> List[Dict[str, Any]]:
        """Получить всех модераторов"""
        moderators = db.query(models.UserDB).filter(
            models.UserDB.role == "moderator"
        ).all()
        
        return [
            {
                "id": m.id,
                "username": m.username
            }
            for m in moderators
        ]
    
    @staticmethod
    def get_users_for_moderator(db: Session, moderator_id: int) -> List[Dict[str, Any]]:
        """Получить пользователей, которые писали модератору"""
        users = db.query(models.UserDB).join(
            models.SupportMessage,
            models.UserDB.id == models.SupportMessage.sender_id
        ).filter(
            models.UserDB.role != "moderator"
        ).distinct().all()
        
        return [
            {
                "id": u.id,
                "username": u.username
            }
            for u in users
        ]
    
    @staticmethod
    def get_unread_replies_count_for_user(
        db: Session, 
        user_id: int, 
        last_checked: Optional[datetime] = None
    ) -> int:
        """Получить количество непрочитанных ответов для пользователя"""
        query = db.query(models.SupportMessage).filter(
            models.SupportMessage.parent_message_id.in_(
                db.query(models.SupportMessage.id).filter(
                    models.SupportMessage.sender_id == user_id
                )
            ),
            models.SupportMessage.sender_id != user_id,
            models.SupportMessage.is_read == False
        )
        
        if last_checked:
            query = query.filter(models.SupportMessage.created_at > last_checked)
        
        return query.count()
    
    @staticmethod
    def get_conversation(db: Session, user_id: int, moderator_id: int) -> List[Dict[str, Any]]:
        """Получить переписку между пользователем и модератором"""
        messages = db.query(models.SupportMessage).filter(
            (models.SupportMessage.sender_id == user_id) | 
            (models.SupportMessage.sender_id == moderator_id)
        ).order_by(models.SupportMessage.created_at.asc()).all()
        
        result = []
        for msg in messages:
            sender = db.query(models.UserDB).filter(
                models.UserDB.id == msg.sender_id
            ).first()
            
            read_status = db.query(models.MessageReadStatus).filter(
                models.MessageReadStatus.message_id == msg.id
            ).all()
            
            result.append({
                "id": msg.id,
                "content": msg.content,
                "created_at": msg.created_at,
                "sender": "moderator" if msg.sender_id == moderator_id else "user",
                "sender_name": sender.username if sender else "Unknown",
                "is_read": any(rs.is_read for rs in read_status),
                "read_by_moderators": [
                    {
                        "moderator_id": rs.moderator_id,
                        "read_at": rs.read_at.isoformat() if rs.read_at else None
                    }
                    for rs in read_status if rs.is_read
                ],
                "is_reply_to": msg.parent_message_id
            })
        
        return result



    @staticmethod
    def read_message(db: Session, moderator_id: int, message_id: int) -> models.MessageReadStatus:
        now = datetime.now(timezone.utc)

        # 1. Находим или создаём статус прочтения для модератора
        read_status = db.query(models.MessageReadStatus).filter(
            models.MessageReadStatus.message_id == message_id,
            models.MessageReadStatus.moderator_id == moderator_id
        ).first()

        # 2. Находим само сообщение
        message = db.query(models.SupportMessage).filter(
            models.SupportMessage.id == message_id
        ).first()
        
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")

        # 3. Определяем НОВЫЙ статус (тоггл)
        new_read_value = not read_status.is_read if read_status else True

        # 4. Обновляем MessageReadStatus
        if not read_status:
            read_status = models.MessageReadStatus(
                message_id=message_id,
                moderator_id=moderator_id,
                is_read=new_read_value,
                read_at=now if new_read_value else None
            )
            db.add(read_status)
        else:
            read_status.is_read = new_read_value
            if new_read_value:
                read_status.read_at = now
            else:
                read_status.read_at = None  

        message.is_read = new_read_value

        db.commit()
        db.refresh(read_status)
        return read_status

    @staticmethod
    def close_message(db: Session, message_id: int, moderator_id: int) -> models.SupportMessage:
        message = db.query(models.SupportMessage).filter(
            models.SupportMessage.id == message_id
        ).first()
        
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")

        # 🔁 Тогглим статус закрытия
        message.is_closed = not message.is_closed
        
        # Если закрываем — устанавливаем ОБА поля is_read в True
        if message.is_closed:
            message.is_read = True  # ✅ Глобальный статус
            
            # ✅ Обновляем статус прочтения для этого модератора
            read_status = db.query(models.MessageReadStatus).filter(
                models.MessageReadStatus.message_id == message_id,
                models.MessageReadStatus.moderator_id == moderator_id
            ).first()
            
            if read_status:
                read_status.is_read = True  # ✅ Персональный статус
                if read_status.read_at is None:
                    read_status.read_at = datetime.now(timezone.utc)
            else:
                # Если записи не было — создаём с is_read=True
                read_status = models.MessageReadStatus(
                    message_id=message_id,
                    moderator_id=moderator_id,
                    is_read=True,
                    read_at=datetime.now(timezone.utc)
                )
                db.add(read_status)


        db.commit()
        db.refresh(message)
        return message

        



    @staticmethod
    def get_unread_count_for_moderator(
        db: Session, 
        moderator_id: int, 
        include_closed: bool = False  # ✅ Опционально: учитывать закрытые или нет
    ) -> int:
        """
        Возвращает количество сообщений, которые модератор ещё не прочитал.
        Считает только корневые сообщения (не ответы).
        """
        query = db.query(func.count(models.MessageReadStatus.id)).join(
            models.SupportMessage,
            models.MessageReadStatus.message_id == models.SupportMessage.id
        ).filter(
            models.MessageReadStatus.moderator_id == moderator_id,
            models.SupportMessage.is_read == False,
            models.SupportMessage.parent_message_id == None  # ✅ Только главные сообщения, не ответы
        )
        
        # ✅ Опционально: исключить закрытые обращения из подсчёта
        if not include_closed:
            query = query.filter(models.SupportMessage.is_closed == False)
        
        return query.scalar() or 0