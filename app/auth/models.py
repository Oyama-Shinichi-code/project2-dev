# ユーザー（アカウント）に関するDBモデルを定義するファイル。
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """
    ユーザーアカウントを表すテーブル。
    パスワードは平文では保存せず、app/auth/security.py の hash_password() で
    ハッシュ化した文字列（hashed_password）のみを保存する。
    """

    __tablename__ = "users"

    # 主キー。自動採番される。
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # ログイン時に使うユーザー名。重複登録を防ぐため unique=True。
    # 検索（ログイン時のルックアップ）が多いため index=True を付与している。
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)

    # bcryptでハッシュ化したパスワード文字列を保存する（平文は一切保存しない）。
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # 登録日時。UTCで統一して記録する（タイムゾーンのずれを防ぐため）。
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # このユーザーが持つタスク一覧（1人のユーザーに対して複数のタスク = 1対多）。
    # cascade="all, delete-orphan" により、ユーザーを削除すると紐づくタスクも自動的に削除される。
    tasks = relationship("Task", back_populates="owner", cascade="all, delete-orphan")
