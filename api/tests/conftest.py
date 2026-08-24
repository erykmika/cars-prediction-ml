import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["MODEL_PATH"] = "/tmp/nonexistent_model.joblib"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["REFRESH_TOKEN_EXPIRE_DAYS"] = "7"

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import User
from app.db.session import get_db
from app.main import app
from app.services.auth_service import create_access_token

test_engine = create_engine("sqlite:///./test.db", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


# Pre-computed bcrypt hash for "testpass" (8 chars) using bcrypt directly
TEST_PASSWORD_HASH = "$2b$12$GLxZ96xBe1Hgavw39Q2zN.VUy4UCc4GDHRYlhq9FOsonSb2.3JwoW"


@pytest.fixture
def test_user():
    db = TestingSessionLocal()
    user = User(
        username="testuser",
        hashed_password=TEST_PASSWORD_HASH,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    db.delete(user)
    db.commit()
    db.close()


@pytest.fixture
def auth_headers(test_user):
    access_token = create_access_token({"sub": test_user.username})
    return {"Authorization": f"Bearer {access_token}"}
