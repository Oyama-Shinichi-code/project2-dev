# pytest実行時に自動で読み込まれる共通設定ファイル。
# テスト用のDB・FastAPIクライアントをここで一括して用意し、各テストファイルから使い回す。
import os

# app.database をインポートする前に環境変数を上書きする必要があるため、
# このファイルの先頭（他のappモジュールをimportする前）で設定する。
# これにより、テスト実行中は本番用の app.db ではなく、メモリ上のSQLiteDBが使われる。
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# テスト専用のエンジンを作成する。
# StaticPoolを使うのは、インメモリSQLiteは接続（コネクション）ごとに別のDBとして
# 扱われてしまうため、テスト全体で同じ1つの接続を使い続けるようにするための設定。
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """
    本番用の get_db（app/database.py）の代わりに、テスト用DBセッションを返す関数。
    FastAPIの dependency_overrides によって差し替える。
    """
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# アプリが依存している get_db を、テスト用の override_get_db に差し替える。
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    """
    各テスト関数の実行前にテーブルを作り直し、実行後に破棄する fixture。
    autouse=True により、すべてのテストで自動的に適用される
    （毎テストが他のテストのデータに影響されない、クリーンな状態で始まる）。
    """
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    """テストから使うHTTPクライアント。これを使ってAPIにリクエストを送る。"""
    return TestClient(app)
