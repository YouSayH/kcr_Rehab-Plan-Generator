
from app.crud import plan as plan_crud
from app.crud import staff as staff_crud


def has_permission_for_patient(user, patient_id):
    """
    指定された患者に対するアクセス権限をチェックする。
    管理者であるか、担当患者であれば True を返す。
    """
    if not user.is_authenticated:
        return False

    # 管理者は常にアクセス可能
    if user.role == "admin":
        return True

    # 担当患者リストを取得してチェック
    assigned_patients = staff_crud.get_assigned_patients(user.id)
    # 効率化のため、IDのセットを作成して存在確認
    assigned_patient_ids = {p["patient_id"] for p in assigned_patients}

    return patient_id in assigned_patient_ids


def get_plan_checked(plan_id, user):
    """
    指定されたIDの計画書を取得し、存在確認とアクセス権限チェックを行う共通関数。

    Returns:
        plan_data: 計画書データ

    Raises:
        ValueError: 計画書が存在しない場合
        PermissionError: アクセス権限がない場合
    """
    plan_data = plan_crud.get_plan_by_id(plan_id)
    if not plan_data:
        raise ValueError("Plan not found")

    patient_id = plan_data["patient_id"]
    if not has_permission_for_patient(user, patient_id):
        raise PermissionError("Permission denied")

    return plan_data
