from sqlalchemy.exc import IntegrityError

import app.core.database as database
from app.models import LikedItemDetail, Patient, RehabilitationPlan, Staff


def get_staff_by_username(username: str):
    db = database.SessionLocal()
    try:
        staff = db.query(Staff).filter(Staff.username == username).first()
        if staff:
            return {c.name: getattr(staff, c.name) for c in staff.__table__.columns}
        return None
    finally:
        db.close()


def get_staff_by_id(staff_id: int):
    db = database.SessionLocal()
    try:
        staff = db.query(Staff).filter(Staff.id == staff_id).first()
        if staff:
            return {c.name: getattr(staff, c.name) for c in staff.__table__.columns}
        return None
    finally:
        db.close()


def create_staff(username: str, hashed_password: str, occupation: str, role: str = "general"):
    db = database.SessionLocal()
    try:
        new_staff = Staff(username=username, password=hashed_password, occupation=occupation, role=role)
        db.add(new_staff)
        db.commit()
    finally:
        db.close()

def get_all_staff():
    db = database.SessionLocal()
    try:
        staff_list = db.query(Staff.id, Staff.username, Staff.occupation, Staff.role).order_by(Staff.id).all()
        return [{"id": s.id, "username": s.username, "occupation": s.occupation, "role": s.role} for s in staff_list]
    finally:
        db.close()

def delete_staff_by_id(staff_id: int):
    db = database.SessionLocal()
    try:
        staff_to_delete = db.query(Staff).filter(Staff.id == staff_id).first()
        if staff_to_delete:
            db.delete(staff_to_delete)
            db.commit()
    finally:
        db.close()

# --- 担当患者割り当て関連 ---

def get_assigned_patients(staff_id: int):
    db = database.SessionLocal()
    try:
        staff = db.query(Staff).filter(Staff.id == staff_id).first()
        if staff:
            return [{"patient_id": p.patient_id, "name": p.name} for p in staff.assigned_patients]
        return []
    finally:
        db.close()


def assign_patient_to_staff(staff_id: int, patient_id: int):
    db = database.SessionLocal()
    try:
        staff = db.query(Staff).filter(Staff.id == staff_id).first()
        patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
        if staff and patient:
            staff.assigned_patients.append(patient)
            db.commit()
    except IntegrityError:
        db.rollback()
        raise
    finally:
        db.close()


def unassign_patient_from_staff(staff_id: int, patient_id: int):
    db = database.SessionLocal()
    try:
        staff = db.query(Staff).filter(Staff.id == staff_id).first()
        patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
        if staff and patient and patient in staff.assigned_patients:
            staff.assigned_patients.remove(patient)
            db.commit()
    finally:
        db.close()

def get_patients_for_staff_with_liked_items(staff_id: int):
    """指定された職員がいいねをしたことがある患者のリストを取得する"""
    db = database.SessionLocal()
    try:
        # LikedItemDetail と RehabilitationPlan を経由して Patient を取得
        patients = (
            db.query(Patient)
            .join(RehabilitationPlan, Patient.patient_id == RehabilitationPlan.patient_id)
            .join(LikedItemDetail, RehabilitationPlan.plan_id == LikedItemDetail.rehabilitation_plan_id)
            .filter(LikedItemDetail.staff_id == staff_id)
            .distinct()
            .all()
        )
        return [{"patient_id": p.patient_id, "name": p.name} for p in patients]
    finally:
        db.close()




