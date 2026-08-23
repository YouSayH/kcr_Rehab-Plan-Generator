from sqlalchemy import TIMESTAMP, Boolean, Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from .base import Base

# 中間テーブル (Staff <-> Patient)
# Patient側でも使用するため、ここで定義してエクスポートします
# モデル定義
# staffとpatientsの中間テーブル（多対多）をモデルクラスを介さずに定義
staff_patients_association = Table(
    "staff_patients",
    Base.metadata,
    Column("staff_id", Integer, ForeignKey("staff.id"), primary_key=True),
    Column("patient_id", Integer, ForeignKey("patients.patient_id"), primary_key=True),
)


class Staff(Base):
    __tablename__ = "staff"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    occupation = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="general")
    created_at = Column(TIMESTAMP)

    session_token = Column(String(255), nullable=True, index=True)

    # TRUEの間はパスワード変更画面以外を使用できない (初回ログイン時の強制変更に使用)
    must_change_password = Column(Boolean, nullable=False, default=True)
    password_updated_at = Column(TIMESTAMP, nullable=True)

    # Staffから担当のPatientを 'assigned_patients' という名前で参照
    # secondary引数にはTableオブジェクトを直接渡す
    assigned_patients = relationship("Patient", secondary=staff_patients_association, back_populates="staff_members")

    suggestion_likes = relationship("SuggestionLike", back_populates="staff")
