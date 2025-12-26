import os

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import login_required, login_user, logout_user
from werkzeug.security import check_password_hash

from app.auth_models import Staff  # Flask-Login用
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
    logout_user()
    flash("ログアウトしました。", "info")
    return redirect(url_for("auth.login"))
