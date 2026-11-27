# データベース接続・セッション管理を一元化するモジュール。
# 他のモデルファイル（app/auth/models.py など）はここで定義する Base を継承する。
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# DATABASE_URL は環境変数で切り替え可能にしている。
# 通常実行では ./app.db（SQLiteファイル）を使うが、
# テスト実行時（tests/conftest.py）は別のURLに上書きして本番データと混在しないようにする。
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./app.db")

# SQLiteはデフォルトで「作成したスレッドでしか使えない」制約があるが、
# FastAPIはリクエストごとに別スレッドで処理することがあるため check_same_thread=False で解除する。
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

# SessionLocal はDBとの対話（クエリ発行・コミット等）を行うためのセッションを作るファクトリ。
# autocommit=False: 明示的に commit するまで自動で確定しない（意図しない書き込みを防ぐ）。
# autoflush=False: クエリ実行前に自動でflushしない（挙動を予測しやすくする）。
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# すべてのORMモデル（User, Taskなど）はこの Base を継承することで
# SQLAlchemyにテーブルとして認識される。
Base = declarative_base()


def get_db():
    """
    FastAPIの Depends() から呼び出される、DBセッションを1リクエスト分だけ発行する関数。
    リクエスト処理が終わったら（例外が起きても）必ず db.close() でセッションを閉じる。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
