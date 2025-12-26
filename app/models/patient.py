from datetime import date

from sqlalchemy import TIMESTAMP, Column, Date, Integer, String
from sqlalchemy.orm import relationship

from .base import Base
from .staff import staff_patients_association  # 中間テーブルをインポート


class Patient(Base):
    __tablename__ = "patients"
    patient_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    date_of_birth = Column(Date)
    gender = Column(String(10))
    created_at = Column(TIMESTAMP)

    # PatientからRehabilitationPlanを 'plans' という名前で参照
    plans = relationship("RehabilitationPlan", back_populates="patient", cascade="all, delete-orphan")

    # Patientから担当のStaffを 'staff_members' という名前で参照
    staff_members = relationship("Staff", secondary=staff_patients_association, back_populates="assigned_patients")

    suggestion_likes = relationship("SuggestionLike", back_populates="patient")

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        today = date.today()
        return (
            today.year
            - self.date_of_birth.year
            - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        )
