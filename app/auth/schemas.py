# APIの入出力の形を定義するスキーマ（Pydanticモデル）。
# DBモデル（app/auth/models.py の User）とは別物で、リクエスト/レスポンスの検証用に使う。
from typing import Literal

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """ユーザー新規登録時に受け取るデータの形。"""

    # ユーザー名は1〜50文字。空文字での登録を防ぐため min_length=1 を指定。
    username: str = Field(min_length=1, max_length=50)
    # パスワードは最低8文字を要求し、簡単すぎるパスワードでの登録を防ぐ。
    password: str = Field(min_length=8, max_length=255)


class UserLogin(BaseModel):
    """ログイン時に受け取るデータの形。"""

    username: str
    password: str


class SortPreferenceUpdate(BaseModel):
    """
    タスク一覧のソート方法を更新する際に受け取るデータの形。
    "due_date"（期限日順）, "title"（タスク名順）, "manual"（手動並び替え順）のいずれかのみ許可する。
    """

    sort_preference: Literal["due_date", "title", "manual"]


class AccountDelete(BaseModel):
    """
    アカウント削除時に受け取るデータの形。
    誤操作・第三者による意図しない削除を防ぐため、本人確認用にパスワードの再入力を必須とする。
    """

    password: str
