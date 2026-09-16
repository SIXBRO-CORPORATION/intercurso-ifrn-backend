import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db")
os.environ.setdefault("DATABASE_URL_SYNC", "postgresql://test:test@localhost:5432/test_db")
os.environ.setdefault("SUAP_CLIENT_ID", "test-client-id")
os.environ.setdefault("SUAP_CLIENT_SECRET", "test-client-secret")
os.environ.setdefault("SUAP_REDIRECT_URI", "http://localhost:8000/api/auth/callback")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("MOBILE_DEEP_LINK_SCHEME", "testapp")
os.environ.setdefault("MOBILE_DEEP_LINK_PATH", "callback")