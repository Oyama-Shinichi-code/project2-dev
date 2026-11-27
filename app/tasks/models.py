# タスク（TODO項目）のDBモデルを定義するファイル。
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Task(Base):
    """
    1件のタスク（TODO項目）を表すテーブル。
    必ず1人のユーザー（user_id）に紐づき、他のユーザーからは参照・操作できない
    （アクセス制御はルーター側で、ログイン中のユーザーIDと一致するかをチェックして実現する）。
    """

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # このタスクの所有者となるユーザーのID。外部キー制約でusersテーブルと結びつける。
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    # タスクのタイトル。要件定義書より必須項目。
    title: Mapped[str] = mapped_column(String(200), nullable=False)

    # タスクの詳細説明。任意項目なので nullable=True。
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 期限。任意項目。日付のみを保持する（時刻は持たない）。
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # 完了フラグ。デフォルトは未完了（False）。
    is_done: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # 所有者であるUserへの逆参照（User.tasks と対になる関係）。
    owner = relationship("User", back_populates="tasks")
