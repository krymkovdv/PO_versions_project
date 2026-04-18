#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app import models
from app.crud.software import normalize_tractor_model  # или скопируйте функцию сюда

def main():
    db = SessionLocal()
    try:
        software_list = db.query(models.Software).all()
        print(f"Найдено записей: {len(software_list)}")
        updated = 0
        for sw in software_list:
            old = sw.tractor_model
            if not old:
                continue
            new = normalize_tractor_model(old)
            if new != old:
                sw.tractor_model = new
                updated += 1
                print(f"✅ id={sw.id}: {old[:80]} -> {new[:80]}")
        if updated:
            db.commit()
            print(f"\nОбновлено {updated} записей.")
        else:
            print("Ничего не требует исправления.")
    except Exception as e:
        db.rollback()
        print(f"Ошибка: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()