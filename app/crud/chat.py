# app/crud/chat.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime, timezone
from typing import List, Dict, Optional
from .. import models

class SupportCRUD:
    @staticmethod
    def send_message_to_moderators(db: Session, sender_id: int, content: str):
        """Отправка сообщения всем модераторам"""
        # Создаем сообщение (parent_message_id = None, так как это новое сообщение)
        message = models.SupportMessage(
            sender_id=sender_id,
            content=content,
            parent_message_id=None  # Явно указываем, что это не ответ
        )
        db.add(message)
        db.flush()
        
        # Получаем всех модераторов
        moderators = db.query(models.UserDB).filter(models.UserDB.role == "moderator").all()
        
        # Создаем записи о прочтении для каждого модератора
        for mod in moderators:
            read_status = models.MessageReadStatus(
                message_id=message.id,
                moderator_id=mod.id,
                is_read=False
            )
            db.add(read_status)
        
        db.commit()
        db.refresh(message)
        return message
    
    @staticmethod
    def moderator_reply(db: Session, moderator_id: int, original_message_id: int, content: str):
        # ... (поиск оригинала) ...
        original_message = db.query(models.SupportMessage).filter(
            models.SupportMessage.id == original_message_id
        ).first()
        
        if not original_message:
            return None
        
        # Создаем ответ
        reply_message = models.SupportMessage(
            sender_id=moderator_id,
            content=content,
            parent_message_id=original_message_id
        )
        db.add(reply_message)
        db.flush()
        
        # --- ИЗМЕНЕНИЕ НАЧАЛО ---
        
        # 1. Создаем статус прочтения для АВТОРА оригинального сообщения (ПОЛЬЗОВАТЕЛЯ)
        # Именно это позволит пользователю увидеть уведомление
        user_read_status = models.MessageReadStatus(
            message_id=reply_message.id,
            moderator_id=original_message.sender_id, # Используем поле moderator_id для хранения ID того, кто должен прочитать
            is_read=False
        )
        db.add(user_read_status)
        
        # 2. Создаем статусы для ДРУГИХ модераторов (как было раньше)
        other_moderators = db.query(models.UserDB).filter(
            and_(
                models.UserDB.role == "moderator",
                models.UserDB.id != moderator_id
            )
        ).all()
        
        for mod in other_moderators:
            mod_read_status = models.MessageReadStatus(
                message_id=reply_message.id,
                moderator_id=mod.id,
                is_read=False
            )
            db.add(mod_read_status)
        
        # Отмечаем оригинальное сообщение как прочитанное этим модератором
        read_status = db.query(models.MessageReadStatus).filter(
            and_(
                models.MessageReadStatus.message_id == original_message_id,
                models.MessageReadStatus.moderator_id == moderator_id
            )
        ).first()
        
        if read_status:
            read_status.is_read = True
            read_status.read_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(reply_message)
        
        return {
            "reply": reply_message,
            "original_message": original_message
        }
    
    @staticmethod
    def get_conversation(db: Session, user_id: int, moderator_id: int = None):
        """Получить всю переписку пользователя с древовидной структурой"""
        # Получаем все корневые сообщения (не ответы) от пользователя
        root_messages = db.query(models.SupportMessage).filter(
            models.SupportMessage.sender_id == user_id,
            models.SupportMessage.parent_message_id == None  # Только корневые сообщения
        ).order_by(
            models.SupportMessage.created_at.desc()
        ).all()
        
        result = []
        for root_msg in root_messages:
            # Получаем все ответы на это сообщение (включая ответы модераторов)
            replies = db.query(models.SupportMessage).filter(
                models.SupportMessage.parent_message_id == root_msg.id
            ).order_by(
                models.SupportMessage.created_at.asc()
            ).all()
            
            # Информация о прочтении
            read_statuses = db.query(
                models.MessageReadStatus, models.UserDB.username
            ).join(
                models.UserDB, models.UserDB.id == models.MessageReadStatus.moderator_id
            ).filter(
                models.MessageReadStatus.message_id == root_msg.id
            ).all()
            
            message_data = {
                "id": root_msg.id,
                "content": root_msg.content,
                "created_at": root_msg.created_at,
                "sender": "user",
                "sender_name": root_msg.sender.username,
                "is_read": any(status.is_read for status, _ in read_statuses),
                "read_by": [
                    {"moderator": username, "read_at": status.read_at}
                    for status, username in read_statuses if status.is_read
                ],
                "replies": [
                    {
                        "id": reply.id,
                        "content": reply.content,
                        "created_at": reply.created_at,
                        "sender": "moderator",
                        "sender_name": reply.sender.username,
                        "moderator_id": reply.sender_id
                    }
                    for reply in replies
                ]
            }
            result.append(message_data)
        
        return result
    
    @staticmethod
    def get_messages_for_moderator(db: Session, moderator_id: int):
        """Получить все сообщения для конкретного модератора (с группировкой по пользователям)"""
        # Получаем всех пользователей, которые писали сообщения
        users_with_messages = db.query(
            models.UserDB.id,
            models.UserDB.username,
            models.UserDB.role
        ).join(
            models.SupportMessage, models.SupportMessage.sender_id == models.UserDB.id
        ).filter(
            models.UserDB.role.in_(["dealer", "engineer"])
        ).distinct().all()
        
        result = []
        for user_id, username, role in users_with_messages:
            # Получаем все корневые сообщения этого пользователя
            user_messages = db.query(
                models.SupportMessage,
                models.MessageReadStatus.is_read
            ).outerjoin(
                models.MessageReadStatus,
                and_(
                    models.MessageReadStatus.message_id == models.SupportMessage.id,
                    models.MessageReadStatus.moderator_id == moderator_id
                )
            ).filter(
                models.SupportMessage.sender_id == user_id,
                models.SupportMessage.parent_message_id == None  # Только корневые
            ).order_by(
                models.SupportMessage.created_at.desc()
            ).all()
            
            user_data = {
                "user_id": user_id,
                "username": username,
                "role": role,
                "messages": []
            }
            
            for msg, is_read in user_messages:
                # Получаем ответы на это сообщение
                replies = db.query(models.SupportMessage).filter(
                    models.SupportMessage.parent_message_id == msg.id
                ).order_by(
                    models.SupportMessage.created_at.asc()
                ).all()
                
                user_data["messages"].append({
                    "id": msg.id,
                    "content": msg.content,
                    "created_at": msg.created_at,
                    "is_read": is_read or False,
                    "replies": [
                        {
                            "id": reply.id,
                            "content": reply.content,
                            "created_at": reply.created_at,
                            "moderator_id": reply.sender_id,
                            "moderator_name": reply.sender.username
                        }
                        for reply in replies
                    ]
                })
            
            if user_data["messages"]:
                result.append(user_data)
        
        return result
    
    @staticmethod
    def get_all_user_messages(db: Session, user_id: int):
        """Получить все сообщения пользователя с ответами и АВТОМАТИЧЕСКИ отметить ответы как прочитанные"""
        
        # 1. Получаем все корневые сообщения пользователя
        messages = db.query(
            models.SupportMessage
        ).filter(
            models.SupportMessage.sender_id == user_id,
            models.SupportMessage.parent_message_id == None
        ).order_by(
            models.SupportMessage.created_at.desc()
        ).all()
        
        # 2. Собираем ID всех ответов, которые мы сейчас вернем пользователю
        # Чтобы потом отметить их как прочитанные
        reply_ids_to_mark = []
        
        result = []
        for msg in messages:
            # Информация о прочтении (для корневых сообщений)
            read_statuses = db.query(
                models.MessageReadStatus, models.UserDB.username
            ).join(
                models.UserDB, models.UserDB.id == models.MessageReadStatus.moderator_id
            ).filter(
                models.MessageReadStatus.message_id == msg.id
            ).all()
            
            # Ответы на это сообщение
            replies = db.query(models.SupportMessage).filter(
                models.SupportMessage.parent_message_id == msg.id
            ).order_by(
                models.SupportMessage.created_at.asc()
            ).all()
            
            # Собираем ID ответов для массовой пометки
            for reply in replies:
                reply_ids_to_mark.append(reply.id)
            
            result.append({
                "message": msg,
                "read_by": [
                    {"moderator": username, "is_read": status.is_read, "read_at": status.read_at}
                    for status, username in read_statuses
                ],
                "replies": [
                    {
                        "id": reply.id,
                        "content": reply.content,
                        "created_at": reply.created_at,
                        "moderator_name": reply.sender.username
                    }
                    for reply in replies
                ]
            })
        
        # 3. МАССОВОЕ ОБНОВЛЕНИЕ СТАТУСОВ (Если есть что обновлять)
        if reply_ids_to_mark:
            # Находим все записи в MessageReadStatus для этих ответов, принадлежащие пользователю
            # и которые еще не прочитаны
            unread_statuses = db.query(models.MessageReadStatus).filter(
                models.MessageReadStatus.message_id.in_(reply_ids_to_mark),
                models.MessageReadStatus.moderator_id == user_id, # ID пользователя в поле moderator_id
                models.MessageReadStatus.is_read == False
            ).all()
            
            if unread_statuses:
                for status in unread_statuses:
                    status.is_read = True
                    status.read_at = datetime.now(timezone.utc)
                
                db.commit() # Фиксируем изменения только если что-то изменили
        
        return result
    
    @staticmethod
    def mark_as_read(db: Session, message_id: int, moderator_id: int):
        """Отметить сообщение как прочитанное модератором"""
        read_status = db.query(models.MessageReadStatus).filter(
            models.MessageReadStatus.message_id == message_id,
            models.MessageReadStatus.moderator_id == moderator_id
        ).first()
        
        if read_status and not read_status.is_read:
            read_status.is_read = True
            read_status.read_at = datetime.now(timezone.utc)
            db.commit()
        
        return read_status
    
    @staticmethod
    def get_unread_count(db: Session, moderator_id: int) -> int:
        """Получить количество непрочитанных сообщений для модератора"""
        count = db.query(models.MessageReadStatus).join(
            models.SupportMessage, 
            models.MessageReadStatus.message_id == models.SupportMessage.id
            ).filter(
            models.MessageReadStatus.moderator_id == moderator_id,
            models.MessageReadStatus.is_read == False,
            models.SupportMessage.parent_message_id == None
        ).count()
        return count
    
    @staticmethod
    def get_all_moderators(db: Session) -> List[dict]:
        """Получить список всех модераторов"""
        moderators = db.query(models.UserDB).filter(
            models.UserDB.role == "moderator"
        ).all()
        
        return [
            {"id": mod.id, "username": mod.username}
            for mod in moderators
        ]
    
    @staticmethod
    def get_users_for_moderator(db: Session, moderator_id: int) -> List[dict]:
        """Получить список пользователей с их последними сообщениями"""
        # Получаем всех пользователей, которые писали сообщения
        users_data = db.query(
            models.UserDB.id,
            models.UserDB.username,
            models.UserDB.role,
            func.max(models.SupportMessage.created_at).label("last_message")
        ).join(
            models.SupportMessage, models.SupportMessage.sender_id == models.UserDB.id
        ).filter(
            models.UserDB.role.in_(["dealer", "engineer"])
        ).group_by(
            models.UserDB.id, models.UserDB.username, models.UserDB.role
        ).order_by(
            func.max(models.SupportMessage.created_at).desc()
        ).all()
        
        result = []
        for user_id, username, role, last_message in users_data:
            # Считаем непрочитанные корневые сообщения
            unread = db.query(models.MessageReadStatus).join(
                models.SupportMessage,
                and_(
                    models.SupportMessage.id == models.MessageReadStatus.message_id,
                    models.SupportMessage.sender_id == user_id,
                    models.SupportMessage.parent_message_id == None  # Только корневые
                )
            ).filter(
                models.MessageReadStatus.moderator_id == moderator_id,
                models.MessageReadStatus.is_read == False
            ).count()
            
            result.append({
                "user_id": user_id,
                "username": username,
                "role": role,
                "last_message": last_message,
                "unread_count": unread
            })
        
        return result
    
    @staticmethod
    def get_unread_replies_count_for_user(
        db: Session, 
        user_id: int, 
        last_checked_at: Optional[datetime] = None
    ) -> int:
        """
        Получить количество непрочитанных ОТВЕТОВ от модераторов для пользователя.
        Учитывает только ответы (parent_message_id != None).
        """
        
        # 1. Находим ID всех корневых сообщений этого пользователя
        # (Ответы могут быть только на наши сообщения)
        user_root_messages = db.query(models.SupportMessage.id).filter(
            models.SupportMessage.sender_id == user_id,
            models.SupportMessage.parent_message_id == None
        ).all()
        
        root_ids = [m.id for m in user_root_messages]
        if not root_ids:
            return 0

        # 2. Строим запрос к таблице статусов прочтения
        # Нам нужно найти записи в MessageReadStatus, где is_read=False
        # И само сообщение является ОТВЕТОМ (parent_id in root_ids) И написано НЕ пользователем
        
        query = db.query(models.MessageReadStatus).join(
            models.SupportMessage,
            models.MessageReadStatus.message_id == models.SupportMessage.id
        ).filter(
            models.MessageReadStatus.moderator_id == user_id, # Статус хранится для пользователя как "модератора" своей ветки? 
            # СТОП! В вашей схеме MessageReadStatus.moderator_id ссылается на UserDB.id.
            # Для пользователя мы тоже создаем запись в этой таблице? 
            # Да, в send_message_to_moderators мы создаем статусы для модераторов.
            # А когда модератор отвечает, мы должны создать статус для ПОЛЬЗОВАТЕЛЯ.
            
            # ПРОВЕРКА АРХИТЕКТУРЫ:
            # Сейчас в moderator_reply вы создаете статусы только для ДРУГИХ МОДЕРАТОРОВ.
            # Для пользователя статус НЕ создается автоматически. Это нужно исправить.
            
            models.MessageReadStatus.is_read == False,
            models.SupportMessage.parent_message_id.in_(root_ids),
            models.SupportMessage.sender_id != user_id # Только ответы от других (модераторов)
        )

        # Фильтр по времени (если пользователь уже заходил и смотрел историю)
        if last_checked_at:
            query = query.filter(models.SupportMessage.created_at > last_checked_at)

        return query.count()