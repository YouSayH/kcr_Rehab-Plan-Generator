from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user


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
