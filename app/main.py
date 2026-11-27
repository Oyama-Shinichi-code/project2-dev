# FastAPIアプリケーションのエントリーポイント。
# `uvicorn app.main:app --reload` で起動する。
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.auth.router import router as auth_router
from app.config import SECRET_KEY
from app.database import Base, engine
from app.tasks.router import router as tasks_router
from app.views import router as views_router

# アプリ起動時に、まだ存在しないテーブルをDBに作成する。
# 既にテーブルが存在する場合は何もしない（既存データは壊さない）。
Base.metadata.create_all(bind=engine)

app = FastAPI(title="project2")

# セッションCookieを使えるようにするミドルウェア。
# これを登録することで、各リクエストの request.session が利用可能になる
# （app/auth/dependencies.py の get_current_user が内部で使用している）。
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# CSS/JSなどの静的ファイルを /static パス以下で配信する設定。
# app/static/css/style.css は "/static/css/style.css" でアクセスできるようになる。
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 認証系・タスク管理系のAPIエンドポイント（/api/...）と、HTML画面用のルート（/login等）を
# アプリに登録する。将来、新しい機能（例: データ処理ツール）を追加する際は、
# 同様に新しいルーターファイルを作って include_router するだけで拡張できる構成にしている。
app.include_router(auth_router)
app.include_router(tasks_router)
app.include_router(views_router)


@app.get("/health")
def health_check():
    """アプリが正常に起動しているかを確認するための簡易エンドポイント。"""
    return {"status": "ok"}
