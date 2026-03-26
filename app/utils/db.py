"""
数据库 Session 管理 + 初始化
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session as SASession
from app.models import Base

_engine = None
_SessionFactory = None

SCHEMA_VERSION = 1


def _get_db_path() -> str:
    from app.utils.config_manager import ConfigManager
    return ConfigManager().get("database", "path", "data/bom.db")


def get_engine():
    global _engine
    if _engine is None:
        db_path = _get_db_path()
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
        _engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            echo=False,
        )
    return _engine


def get_session() -> SASession:
    global _SessionFactory
    if _SessionFactory is None:
        _SessionFactory = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _SessionFactory()


def init_db():
    """建表 + 首次初始化默认超管"""
    engine = get_engine()
    Base.metadata.create_all(engine)
    _ensure_default_admin()
    _ensure_schema_version(engine)


def _ensure_default_admin():
    from app.models import User
    from app.utils.security import hash_password

    with get_session() as session:
        existing = session.query(User).filter_by(username="admin", is_deleted=0).first()
        if existing is None:
            admin = User(
                username="admin",
                password_hash=hash_password("Admin@1234"),
                role="super_admin",
                display_name="超级管理员",
                must_change_pwd=1,
            )
            session.add(admin)
            session.commit()


def _ensure_schema_version(engine):
    with engine.connect() as conn:
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS _schema_version (version INTEGER NOT NULL)"
        ))
        row = conn.execute(text("SELECT version FROM _schema_version")).fetchone()
        if row is None:
            conn.execute(text(f"INSERT INTO _schema_version VALUES ({SCHEMA_VERSION})"))
            conn.commit()
