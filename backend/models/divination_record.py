"""占卜历史记录ORM模型"""

from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func

from db.database import Base


class DivinationRecord(Base):
    __tablename__ = "divination_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    question = Column(String(500), nullable=False)
    method = Column(String(20), nullable=False)
    hexagram_data = Column(Text, nullable=False)
    changed_hexagram_data = Column(Text, nullable=True)
    analysis_data = Column(Text, nullable=False)
    fortune = Column(String(10), nullable=False)
    hexagram_name = Column(String(20), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
