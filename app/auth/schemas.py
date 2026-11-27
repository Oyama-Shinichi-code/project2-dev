# APIの入出力の形を定義するスキーマ（Pydanticモデル）。
# DBモデル（app/auth/models.py の User）とは別物で、リクエスト/レスポンスの検証用に使う。
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
