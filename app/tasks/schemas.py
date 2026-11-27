# タスクAPIの入出力の形を定義するスキーマ（Pydanticモデル）。
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class TaskCreate(BaseModel):
    """タスク新規作成時に受け取るデータの形。"""

    # タイトルは必須。空文字での作成を防ぐため min_length=1。
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    due_date: date | None = None


class TaskUpdate(BaseModel):
    """
    タスク編集時に受け取るデータの形。
    すべての項目を任意（None許容）にしており、「変更したい項目だけ」を
    送ってもらう部分更新（PATCH的な使い方）を想定している。
    """

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    due_date: date | None = None
    is_done: bool | None = None


class TaskOut(BaseModel):
    """タスク情報をレスポンスとして返す際の形。"""

    id: int
    title: str
    description: str | None
    due_date: date | None
    is_done: bool
    created_at: datetime
    updated_at: datetime

    # SQLAlchemyのモデルインスタンス（ORMオブジェクト）から直接このスキーマを
    # 作れるようにするための設定（from_attributes=True が無いと辞書しか受け付けない）。
    model_config = ConfigDict(from_attributes=True)
