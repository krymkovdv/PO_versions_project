# app/crud/support.py
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from .. import models
from ..log import logger
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status

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
    
    @staticmethod
    def get_all_user_messages(db: Session, user_id: int) -> List[Dict[str, Any]]:
        """Получить все сообщения пользователя"""
        messages = db.query(models.SupportMessage).filter(
            models.SupportMessage.sender_id == user_id,
            models.SupportMessage.parent_message_id == None  # Только родительские
        ).order_by(models.SupportMessage.created_at.desc()).all()
        
        result = []
        for msg in messages:
            replies = db.query(models.SupportMessage).filter(
                models.SupportMessage.parent_message_id == msg.id
            ).all()
            
            read_status = db.query(models.MessageReadStatus).filter(
                models.MessageReadStatus.message_id == msg.id
            ).all()
            
            result.append({
                "message": msg,
                "replies": replies,
                "read_by": [
                    {
                        "moderator": rs.moderator_id,
                        "is_read": rs.is_read,
                        "read_at": rs.read_at
                    }
                    for rs in read_status
                ]
            })
        
        return result
    
    @staticmethod
    def get_messages_for_moderator(db: Session, moderator_id: int) -> List[Dict[str, Any]]:
        """Получить все сообщения для модератора (группированные по пользователям)"""
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
                    ).all()
                    
                    read_status = db.query(models.MessageReadStatus).filter(
                        models.MessageReadStatus.message_id == msg.id,
                        models.MessageReadStatus.moderator_id == moderator_id
                    ).first()
                    
                    user_messages.append({
                        "id": msg.id,
                        "content": msg.content,
                        "created_at": msg.created_at,
                        "is_read": read_status.is_read if read_status else False,
                        "replies": replies
                    })
                
                result.append({
                    "user": {
                        "id": user.id,
                        "username": user.username
                    },
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