from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import database, schemas, crud

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

database.Base.metadata.create_all(bind=database.engine)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"status": "Grey Duck Mini API is live!"}

@app.get("/players/", response_model=list[schemas.PlayerResponse])
def read_players(db: Session = Depends(get_db)):
    return crud.get_players(db)

@app.post("/players/", response_model=schemas.PlayerResponse)
def create_player(player: schemas.PlayerCreate, db: Session = Depends(get_db)):
    db_player = crud.get_player_by_name(db, name=player.name)
    if db_player:
        raise HTTPException(status_code=400, detail="Player already exists")
    return crud.create_player(db=db, player=player)

@app.get("/matches/", response_model=list[schemas.MatchResponse])
def read_matches(db: Session = Depends(get_db)):
    return crud.get_matches(db)

@app.post("/matches/", response_model=schemas.MatchResponse)
def create_match(match: schemas.MatchCreate, db: Session = Depends(get_db)):
    return crud.record_match(db=db, match_data=match)