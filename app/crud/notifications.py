# app/crud/notifications.py
from sqlalchemy.orm import Session
from .. import models
from .support import DealerNotificationCRUD
from pathlib import Path
import re

def extract_version_from_name(name: str) -> str:
    """Извлекает версию из имени файла (например, v1.2.3 или 1.2.3)"""
    if not name:
        return "unknown"
    match = re.search(r'v?(\d+(?:\.\d+)*)', name)
    return match.group(1) if match else "new"

def create_notifications_for_software_update(db: Session, software_id: int, software: models.Software):
    """Создаёт уведомления для всех дилеров, чьи тракторы используют данное ПО."""
    # 1. Найти все связи ПО с компонентами
    soft_comp_links = db.query(models.Software_Component_Link).filter(
        models.Software_Component_Link.software_id == software_id
    ).all()
    if not soft_comp_links:
        return
    soft_comp_link_ids = [link.id for link in soft_comp_links]

    # 2. Найти все связи тракторов с этими компонентами и ПО
    tractor_links = db.query(models.Tractor_Software_And_Component_Link).filter(
        models.Tractor_Software_And_Component_Link.soft_comp_link_id.in_(soft_comp_link_ids)
    ).all()
    tractor_ids = {link.tractor_id for link in tractor_links}
    if not tractor_ids:
        return

    # 3. Найти дилеров (пользователей с ролью dealer) по текстовому полю tractor.dealer
    dealer_ids = set()
    for tractor_id in tractor_ids:
        tractor = db.query(models.Tractor).get(tractor_id)
        if tractor and tractor.dealer:
            dealer_user = db.query(models.UserDB).filter(
                models.UserDB.username == tractor.dealer,
                models.UserDB.role == "dealer"
            ).first()
            if dealer_user:
                dealer_ids.add(dealer_user.id)

    if not dealer_ids:
        return

    # 4. Получить название и версию ПО
    software_name = software.name or (software.path and Path(software.path).name) or f"ID {software_id}"
    software_version = extract_version_from_name(software_name)

    # 5. Создать уведомления (по одному на дилера, если нет непрочитанного такого же)
    for dealer_id in dealer_ids:
        existing = db.query(models.DealerNotification).filter(
            models.DealerNotification.dealer_id == dealer_id,
            models.DealerNotification.software_id == software_id,
            models.DealerNotification.is_read == False
        ).first()
        if not existing:
            DealerNotificationCRUD.create_notification(
                db=db,
                dealer_id=dealer_id,
                tractor_id=None,  # общее уведомление о ПО
                software_id=software_id,
                software_name=software_name,
                software_version=software_version,
                message=f"Обновлено ПО: {software_name} (версия {software_version})"
            )