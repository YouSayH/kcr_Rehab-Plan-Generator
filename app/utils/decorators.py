from functools import wraps

from flask import flash, g, jsonify, redirect, request, url_for
from flask_login import current_user

from app.utils.helpers import has_permission_for_patient


def admin_required(f):
    """
    管理者権限が必要なルートに付与するデコレータ
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            flash("この操作には管理者権限が必要です。", "danger")
            # 注: Blueprint化の際に 'plan.index' 等に変更が必要になる場合があります
            return redirect(url_for("plan.index"))
        return f(*args, **kwargs)

    return decorated_function


#: 複数の場所に食い違う patient_id が指定された場合を表す番兵
_CONFLICT = object()


def _extract_patient_id(kwargs):
    """リクエストから patient_id を取り出す。

    URLパス・クエリ文字列・フォーム・JSONボディの **すべて** を調べ、
    値が食い違っていたら _CONFLICT を返します。

    最初に見つかった1件で打ち切ってはいけません。ビューによって
    patient_id を読む場所が異なる（save_patient_info は request.form、
    like_suggestion は JSONボディ）ため、「デコレータが検証した値」と
    「ビューが実際に扱う値」がずれ、クエリ文字列に自分の担当患者IDを、
    本文に他人の患者IDを入れるだけで認可を迂回できてしまいます。

    値が見つからない場合は None を返します。
    """
    sources = [kwargs, request.view_args or {}, request.args, request.form]

    # JSON ボディ (Content-Type が違う場合に例外を投げないよう silent=True)
    if request.is_json:
        payload = request.get_json(silent=True)
        if isinstance(payload, dict):
            sources.append(payload)

    found = set()
    for source in sources:
        value = source.get("patient_id")
        if value in (None, ""):
            continue
        try:
            # フォームやJSONからは文字列で届くため正規化する
            found.add(int(value))
        except (TypeError, ValueError):
            # 数値でない patient_id は不正な入力として扱う
            return _CONFLICT

    if not found:
        return None
    if len(found) > 1:
        # 同一リクエスト内で patient_id が食い違っている＝迂回の試み
        return _CONFLICT
    return found.pop()


def _deny(message):
    """APIならJSONの403、画面遷移ならフラッシュ付きリダイレクトを返す。"""
    if request.is_json or request.path.startswith("/api/"):
        return jsonify({"error": message}), 403
    flash(message, "danger")
    return redirect(url_for("plan.index"))


def patient_access_required(allow_missing=False):
    """担当患者以外の患者データへのアクセスを拒否するデコレータ。

    patient_id を URLパス・クエリ文字列・フォーム・JSONボディから探し、
    has_permission_for_patient() で担当患者か管理者かを検証します。

    Args:
        allow_missing: patient_id が無いリクエストを許可するかどうか。
            新規患者の登録画面のように、まだ患者が存在しない場合に True を指定します。
            既定は False で、patient_id が無ければ拒否します。

    使い方:
        @plan_bp.route("/foo")
        @login_required
        @patient_access_required()
        def foo():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            patient_id = _extract_patient_id(kwargs)

            if patient_id is _CONFLICT:
                return _deny("患者の指定が不正です。")

            if patient_id is None:
                if allow_missing:
                    g.patient_id = None
                    return f(*args, **kwargs)
                return _deny("患者が指定されていません。")

            if not has_permission_for_patient(current_user, patient_id):
                return _deny("この患者の情報にアクセスする権限がありません。")

            # 検証済みの値をビューから参照できるようにする。
            # ビューが自前でリクエストを読み直すと、検証した値とずれる余地が残るため。
            g.patient_id = patient_id
            return f(*args, **kwargs)

        return decorated_function

    return decorator
