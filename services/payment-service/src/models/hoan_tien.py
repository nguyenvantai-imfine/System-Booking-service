from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from src.core.database import Base

class HoanTienModel(Base):
    __tablename__ = "hoan_tien"

    id_hoan_tien = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_thanh_toan = Column(
        Integer,
        ForeignKey("thanh_toan.id_thanh_toan", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    so_tien_hoan = Column(Numeric(18, 2), nullable=False)
    ly_do = Column(String(255), nullable=True)
    ngay_hoan = Column(DateTime, default=datetime.utcnow, nullable=False)

    thanh_toan = relationship("ThanhToanModel", back_populates="hoan_tien")
