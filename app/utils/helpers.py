
from app.crud import staff as staff_crud


def has_permission_for_patient(user, patient_id):
    """
    指定された患者に対するアクセス権限をチェックする。
    管理者であるか、担当患者であれば True を返す。

    ルートに付与する場合は、この関数を直接呼ぶのではなく
    app.utils.decorators.patient_access_required を使ってください。
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
