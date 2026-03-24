# app/api/support.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from .. import schemas, crud, models
from ..database import get_session
from ..authorization import get_current_user
from ..log import logger
from ..crud.support import SupportCRUD

router = APIRouter(prefix="/support", tags=["Support Chat"])

# ========== ЭНДПОИНТЫ (названия сохранены как было) ==========

@router.post("/messages")
async def send_to_moderators(
    message: schemas.SupportMessageCreate,  
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    """Отправка сообщения всем модераторам"""
    
    if current_user.role == "moderator":
        raise HTTPException(status_code=400, detail="Moderators cannot send messages to themselves")
    
    new_message = SupportCRUD.send_message_to_moderators(db, current_user.id, message.content)
    
    logger.info(
        f"[support/send] Сообщение отправлено: id={new_message.id}, "
        f"user={current_user.username}"
    )
    
    return {
        "id": new_message.id,
        "content": new_message.content,
        "created_at": new_message.created_at,
        "status": "sent to all moderators"
    }

@router.post("/messages/reply")
async def reply_to_message(
    reply: schemas.SupportReplyRequest,
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    """Ответ модератора на сообщение пользователя"""
    
    if current_user.role != "moderator":
        raise HTTPException(status_code=403, detail="Only moderators can reply")
    
    result = SupportCRUD.moderator_reply(db, current_user.id, reply.message_id, reply.content)
    
    if not result:
        raise HTTPException(status_code=404, detail="Original message not found")
    
    return {
        "status": "reply sent",
        "reply_id": result["reply"].id,
        "reply_content": result["reply"].content,
        "reply_created_at": result["reply"].created_at,
        "original_message_id": result["original_message"].id,
        "original_message_content": result["original_message"].content
    }

@router.get("/conversation/{user_id}")
async def get_conversation_with_user(
    user_id: int,
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    """Получить переписку с конкретным пользователем (только для модераторов)"""
    
    if current_user.role != "moderator":
        raise HTTPException(status_code=403, detail="Only moderators can view conversations")
    
    user = db.query(models.UserDB).filter(models.UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    conversation = SupportCRUD.get_conversation(db, user_id, current_user.id)
    
    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role
        },
        "moderator": {
            "id": current_user.id,
            "username": current_user.username
        },
        "messages": conversation
    }

@router.get("/messages")
async def get_messages(
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    """Получить сообщения (разный ответ для пользователя и модератора)"""
    
    if current_user.role == "moderator":
        users_data = SupportCRUD.get_messages_for_moderator(db, current_user.id)
        
        for user_data in users_data:
            for msg in user_data["messages"]:
                if not msg["is_read"]:
                    SupportCRUD.mark_as_read(db, msg["id"], current_user.id)
                    msg["is_read"] = True
        
        return users_data
    
    else:
        messages = SupportCRUD.get_all_user_messages(db, current_user.id)
        
        return [
            {
                "id": item["message"].id,
                "content": item["message"].content,
                "created_at": item["message"].created_at,
                "is_read": any(r["is_read"] for r in item["read_by"]),
                "read_by": [
                    {
                        "moderator": r["moderator"],
                        "read_at": r["read_at"]
                    }
                    for r in item["read_by"] if r["is_read"]
                ],
                "replies": [
                    {
                        "id": r.id,
                        "content": r.content,
                        "created_at": r.created_at,
                        "sender_id": r.sender_id
                    }
                    for r in item["replies"]
                ]
            }
            for item in messages
        ]

@router.get("/unread")
async def get_unread(
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    """Только для модераторов: количество непрочитанных сообщений"""
    
    if current_user.role != "moderator":
        raise HTTPException(status_code=403, detail="Only for moderators")
    
    count = SupportCRUD.get_unread_count(db, current_user.id)
    return {"unread_count": count}

@router.post("/messages/{message_id}/read")
async def mark_message_read(
    message_id: int,
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    """Отметить сообщение как прочитанное (только для модераторов)"""
    
    if current_user.role != "moderator":
        raise HTTPException(status_code=403, detail="Only moderators can mark messages as read")
    
    read_status = SupportCRUD.mark_as_read(db, message_id, current_user.id)
    
    if read_status:
        return {"status": "marked as read"}
    else:
        raise HTTPException(status_code=404, detail="Message not found")

@router.get("/moderators")
async def get_moderators(
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    """Получить список всех модераторов"""
    moderators = SupportCRUD.get_all_moderators(db)
    return {"moderators": moderators}

@router.get("/users")
async def get_users_for_moderator(
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    """Получить список пользователей, которые писали модератору (только для модераторов)"""
    
    if current_user.role != "moderator":
        raise HTTPException(status_code=403, detail="Only for moderators")
    
    users = SupportCRUD.get_users_for_moderator(db, current_user.id)
    return {"users": users}

@router.get("/unread/replies-count")
async def get_user_unread_replies(
    last_checked: Optional[str] = Query(None),
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    """Получить количество непрочитанных ответов от модераторов (только для пользователей)"""
    
    if current_user.role == "moderator":
        return {"unread_replies_count": 0}
    
    last_checked_dt = None
    if last_checked:
        try:
            clean_date = last_checked.replace('Z', '+00:00')
            last_checked_dt = datetime.fromisoformat(clean_date)
        except ValueError:
            pass
    
    count = SupportCRUD.get_unread_replies_count_for_user(
        db, 
        current_user.id, 
        last_checked_dt
    )
    
    return {"unread_replies_count": count}

# ========== НОВЫЙ ЭНДПОИНТ ДЛЯ УДАЛЕНИЯ ==========

@router.delete("/messages/{message_id}", response_model=schemas.SupportMessageDeleteResponse)
async def delete_message(
    message_id: int,
    delete_request: Optional[schemas.SupportMessageDeleteRequest] = Body(None),
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    """
    Удаление сообщения
    
    - **Пользователи**: могут удалять только свои сообщения
    - **Модераторы**: могут удалять любые сообщения
    - При удалении родительского сообщения все ответы удаляются каскадом
    - Удаление физическое (без возможности восстановления)
    """
    
    reason = delete_request.reason if delete_request else None
    
    if reason:
        logger.info(
            f"[support/delete] Причина удаления: {reason}, "
            f"message_id={message_id}, user={current_user.username}"
        )
    
    result = SupportCRUD.delete_message(
        db=db,
        message_id=message_id,
        user_id=current_user.id,
        user_role=current_user.role
    )
    
    return schemas.SupportMessageDeleteResponse(
        status="deleted",
        message_id=result["message_id"],
        deleted_at=result["deleted_at"],
        deleted_by=current_user.username,
        cascade_deleted=result["cascade_deleted"]
    )