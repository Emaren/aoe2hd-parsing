from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, DateTime
from .base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    uid = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, index=True)
    in_game_name = Column(String, nullable=True)
    verified = Column(Boolean, default=False)
    wallet_address = Column(String(100), nullable=True)
    lock_name = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    token = Column(String(128), nullable=True)

    def __repr__(self):
        return f"<User {self.uid}>"

    def to_dict(self):
        return {
            "id": self.id,
            "uid": self.uid,
            "email": self.email,
            "in_game_name": self.in_game_name,
            "verified": self.verified,
            "wallet_address": self.wallet_address,
            "lock_name": self.lock_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "token": self.token,
        }
