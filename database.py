import os
from sqlalchemy import Column, Float, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Fetch Turso credentials from environment variables (Render Cloud)
TURSO_DB_URL = os.getenv("TURSO_DATABASE_URL")
TURSO_TOKEN = os.getenv("TURSO_AUTH_TOKEN")

if TURSO_DB_URL and TURSO_TOKEN:
    # --- PRODUCTION MODE (Turso Cloud via Hrana/HTTP) ---
    # Convert libsql:// or https:// to HTTP URL
    http_url = TURSO_DB_URL.replace("libsql://", "https://")
    
    # Connect via Hrana driver
    db_url = f"sqlite+hrana://{http_url.replace('https://', '')}?jwt={TURSO_TOKEN}"
    
    engine = create_engine(db_url)
else:
    # --- LOCAL DEVELOPMENT FALLBACK ---
    engine = create_engine(
        "sqlite:///./ultimate_frisbee.db", connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    mu = Column(Float, default=25.0)
    sigma = Column(Float, default=8.333)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)

    @property
    def ordinal(self) -> float:
        return round(max(0.0, self.mu - (3.0 * self.sigma)), 2)


# Automatically create database tables if they do not exist
Base.metadata.create_all(bind=engine)