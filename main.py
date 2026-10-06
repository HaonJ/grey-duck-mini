from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import database, schemas, crud

app = FastAPI()

# Enable CORS for GitHub Pages frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize database tables
database.Base.metadata.create_all(bind=database.engine)

# Dependency to get database session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Root endpoint for status check
@app.get("/")
def read_root():
    return {"status": "Grey Duck Mini API is live!"}

# Get all players
@app.get("/players/", response_model=list[schemas.PlayerResponse])
def read_players(db: Session = Depends(get_db)):
    return crud.get_players(db)

# Create a new player
@app.post("/players/", response_model=schemas.PlayerResponse)
def create_player(player: schemas.PlayerCreate, db: Session = Depends(get_db)):
    db_player = crud.get_player_by_name(db, name=player.name)
    if db_player:
        raise HTTPException(status_code=400, detail="Player already exists")
    return crud.create_player(db=db, player=player)