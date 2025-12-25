from flask_login import UserMixin


class Staff(UserMixin):
    # コンストラクタ。ログイン時にデータベースから取得した職員情報をここに格納します。
    def __init__(self, staff_id, username, role, occupation):
        self.id = staff_id
        self.username = username
        self.role = role
        self.occupation = occupation
