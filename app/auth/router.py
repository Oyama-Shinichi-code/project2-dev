# 認証関連（登録・ログイン・ログアウト）のAPIエンドポイントを定義するルーター。
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.dependencies import SESSION_KEY, get_current_user
from app.auth.models import User
from app.auth.schemas import AccountDelete, UserCreate, UserLogin
from app.auth.security import hash_password, verify_password
from app.database import get_db

# このルーターに属するエンドポイントはすべて /api/auth から始まる。
# "/api" プレフィックスを付けることで、HTML画面用のパス（app/views.py で定義、/login や /tasks など）
# とAPIのパスが衝突しないように明確に分離している。
router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    新規ユーザー登録。
    同名のユーザー名が既に存在する場合は 400 Bad Request を返す。
    """
    existing = db.query(User).filter(User.username == user_in.username).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")

    # パスワードは平文のまま保存せず、必ずハッシュ化してからDBに書き込む。
    new_user = User(username=user_in.username, hashed_password=hash_password(user_in.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"id": new_user.id, "username": new_user.username}


@router.post("/login")
def login(credentials: UserLogin, request: Request, db: Session = Depends(get_db)):
    """
    ログイン処理。ユーザー名とパスワードを検証し、成功したらセッションにユーザーIDを保存する。
    以降のリクエストは、このセッションCookieを使って「ログイン済み」と判定される。
    """
    user = db.query(User).filter(User.username == credentials.username).first()

    # ユーザーが存在しない場合と、パスワードが違う場合を同じエラーメッセージにすることで、
    # 「そのユーザー名が存在するかどうか」が外部から推測されにくいようにしている。
    if user is None or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    request.session[SESSION_KEY] = user.id
    return {"id": user.id, "username": user.username}


@router.post("/logout")
def logout(request: Request):
    """ログアウト処理。セッションからユーザーIDの情報を削除する。"""
    request.session.pop(SESSION_KEY, None)
    return {"message": "Logged out"}


@router.get("/me")
def read_current_user(current_user: User = Depends(get_current_user)):
    """現在ログイン中のユーザー情報を返す。未ログインなら get_current_user が401を返す。"""
    return {"id": current_user.id, "username": current_user.username}


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    body: AccountDelete,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    ログイン中のユーザー自身のアカウントを削除する。
    誤操作・第三者による削除を防ぐため、パスワードの再入力による本人確認を必須とする。
    User.tasks に cascade="all, delete-orphan" を設定しているため（app/auth/models.py）、
    ユーザーを削除すると紐づくタスクもDB側で自動的に削除される。
    """
    if not verify_password(body.password, current_user.hashed_password):
        # パスワード不一致。ログイン失敗時と違い、ここでは「ログイン済みの本人かどうか」の
        # 確認なので 403 Forbidden を返す（401は「そもそも誰か分からない」場合に使う）。
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Incorrect password")

    db.delete(current_user)
    db.commit()

    # アカウントを削除した以上、このセッション（ログイン状態）も無効化する。
    request.session.pop(SESSION_KEY, None)

    return None
