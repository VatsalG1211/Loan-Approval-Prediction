from sqlalchemy.orm import Session
from . import models

def get_user_by_email(db: Session, email: str):
    try:
        return db.query(models.User).filter(models.User.email == email).first()
    except Exception as e:
        print(f"Database error: {e}")
        raise
