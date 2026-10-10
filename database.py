import os
from datetime import datetime
from sqlalchemy import Column, DateTime, Float, Integer, String, create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

TURSO_DB_URL = os.getenv("TURSO_DATABASE_URL")
TURSO_TOKEN = os.getenv("TURSO_AUTH_TOKEN")

if TURSO_DB_URL and TURSO_TOKEN:
    clean_url = TURSO_DB_URL.replace("libsql://", "").replace("https://", "")
    db_url = f"sqlite+libsql://{clean_url}?secure=true"
    engine = create_engine(db_url, connect_args={"auth_token": TURSO_TOKEN})
else:
    engine = create_engine(
        "sqlite:///./ultimate_frisbee.db", connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    mu = Column(Float, default=1000.0)
    sigma = Column(Float, default=333.33)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    team1_players = Column(String, nullable=False)
    team2_players = Column(String, nullable=False)
    team1_score = Column(Integer, nullable=False)
    team2_score = Column(Integer, nullable=False)
    mmr_change = Column(Float, default=0.0)


# Create missing tables
Base.metadata.create_all(bind=engine)

# Auto-migrate: Safely add 'mmr_change' column if it doesn't exist yet
try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE matches ADD COLUMN mmr_change FLOAT DEFAULT 0.0;"))
        conn.commit()
except Exception:
    # Column already exists or table was just created; safely ignore
    pass