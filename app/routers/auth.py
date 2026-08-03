import os

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from app.auth_models import Staff  # Flask-Login用
from app.core.bootstrap import MIN_PASSWORD_LENGTH
from app.core.database import SessionLocal

# CRUDと、トークン保存用にDBセッションとDBモデルを直接インポート
from app.crud import staff as staff_crud
from app.models import Staff as DBStaff  # auth_models.Staffと区別するため別名にする

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """ログインページ"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        staff_info = staff_crud.get_staff_by_username(username)

        # ユーザーが存在し、かつパスワードが正しいかチェック
        # check_password_hashが、入力されたパスワードとDBのハッシュ値を比較してくれます。
        if staff_info and check_password_hash(staff_info["password"], password):
            # ログイン成功。ユーザー情報をStaffクラスに格納
            # ここで使用しているStaffクラスは app/auth_models.py のものです
            staff = Staff(
                staff_id=staff_info["id"],
                username=staff_info["username"],
                role=staff_info["role"],
                occupation=staff_info["occupation"],
                must_change_password=bool(staff_info.get("must_change_password")),
            )

            # セッショントークン生成
            new_token = os.urandom(24).hex()  # 24バイトのランダムな文字列

            # トークン保存 (ここはCRUD関数がないため直接DB操作)
            try:
                db = SessionLocal()
                # app.models.Staff (DBStaff) を使用
                db_staff = db.query(DBStaff).filter(DBStaff.id == staff.id).first()
                if db_staff:
                    db_staff.session_token = new_token
                    db.commit()
            finally:
                db.close()

            # トークンをセッションに保存
            session["session_token"] = new_token  # Flaskのセッションに保存

            # Flask-Loginのlogin_user関数で、ユーザーをログイン状態にする
            login_user(staff)
            # ログイン後のトップページにリダイレクト(indexはまだmain.pyにあるのでそのまま参照可)
            return redirect(url_for("plan.index"))
        else:
            flash("ユーザー名またはパスワードが正しくありません。", "danger")
    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    """ログアウト処理"""
    # DB側のトークンも破棄する。これを消さないと、コピーされた署名付きcookieを
    # 送るだけでログアウト後もユーザーが復元されてしまう。
    try:
        staff_crud.clear_session_token(current_user.id)
    except Exception:
        # トークン破棄に失敗してもログアウト自体は成立させる
        current_app.logger.exception("ログアウト時のセッショントークン破棄に失敗しました。")

    logout_user()
    session.clear()
    flash("ログアウトしました。", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    """パスワード変更ページ。

    初回ログイン時は must_change_password が立っており、
    app/__init__.py の before_request ガードによってここへ誘導されます。
    """
    forced = bool(getattr(current_user, "must_change_password", False))

    if request.method == "POST":
        current_password = request.form.get("current_password") or ""
        new_password = request.form.get("new_password") or ""
        confirm_password = request.form.get("confirm_password") or ""

        staff_info = staff_crud.get_staff_by_id(current_user.id)
        if not staff_info:
            flash("ユーザー情報が取得できませんでした。再度ログインしてください。", "danger")
            return redirect(url_for("auth.logout"))

        if not check_password_hash(staff_info["password"], current_password):
            flash("現在のパスワードが正しくありません。", "danger")
        elif len(new_password) < MIN_PASSWORD_LENGTH:
            flash(f"新しいパスワードは{MIN_PASSWORD_LENGTH}文字以上にしてください。", "danger")
        elif new_password != confirm_password:
            flash("新しいパスワードと確認用パスワードが一致しません。", "danger")
        elif new_password == current_password:
            flash("現在のパスワードとは異なるパスワードを設定してください。", "danger")
        else:
            staff_crud.update_password(current_user.id, generate_password_hash(new_password))
            # update_password が session_token を破棄するため、このセッションも無効になる。
            # 利用者を混乱させないよう、明示的にログアウトして再ログインを促す。
            logout_user()
            session.clear()
            flash("パスワードを変更しました。新しいパスワードでログインしてください。", "success")
            return redirect(url_for("auth.login"))

    return render_template("change_password.html", forced=forced, min_length=MIN_PASSWORD_LENGTH)
