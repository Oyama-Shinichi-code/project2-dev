# パスワードのハッシュ化・検証をまとめたモジュール。
# 平文パスワードを直接DBに保存することは絶対に行わず、必ずこの関数経由でハッシュ化する。
from passlib.context import CryptContext

# bcryptアルゴリズムを使うよう設定。bcryptは計算に時間をかける設計になっており、
# 総当たり攻撃（ブルートフォース）に強いため、パスワードハッシュの定番として使われる。
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """平文パスワードを受け取り、bcryptでハッシュ化した文字列を返す。DB保存用。"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    ログイン時に使用。入力された平文パスワードが、DBに保存されているハッシュ値と
    一致するかどうかを検証する（ハッシュは元に戻せないため、再ハッシュして比較する）。
    """
    return pwd_context.verify(plain_password, hashed_password)
