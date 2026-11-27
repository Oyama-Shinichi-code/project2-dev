# 「現在ログインしているユーザーを取得する」処理を共通化するモジュール。
# タスク管理など、ログインが必要なエンドポイントはすべてここの get_current_user を
# Depends() として使うことで、認証チェックを一か所にまとめている。
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.models import User
from app.database import get_db

# セッション（Cookie）内でユーザーIDを保存する際のキー名。
SESSION_KEY = "user_id"


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """
    リクエストのセッションCookieからユーザーIDを取り出し、該当するUserを返す。
    セッションが無い、またはIDに対応するユーザーがDBに存在しない場合は
    401 Unauthorized を返して処理を中断する（呼び出し元のエンドポイントには到達しない）。
    """
    # SessionMiddleware（app/main.py で設定）により request.session が使えるようになっている。
    user_id = request.session.get(SESSION_KEY)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    user = db.get(User, user_id)
    if user is None:
        # セッションにIDは残っているが、DB上のユーザーが削除済み等のケース。
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    return user
