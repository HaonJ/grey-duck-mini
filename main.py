from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from typing import List

# Import our DB setup and Player model from database.py!
from database import SessionLocal, Player

app = FastAPI(title="Ultimate Frisbee MMR")

# Dependency to open and close DB session for each API request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 1. PYDANTIC SCHEMAS
class PlayerCreate(BaseModel):
    name: str

class PlayerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    mu: float
    sigma: float
    ordinal: float
    wins: int
    losses: int


# 2. ENDPOINT: Create a new player
@app.post("/players", response_model=PlayerResponse, status_code=201)
def create_player(player_in: PlayerCreate, db: Session = Depends(get_db)):
    # Clean up name string (remove extra whitespace)
    clean_name = player_in.name.strip().title()

    # Check if a player with this name already exists in DB
    existing_player = db.query(Player).filter(Player.name == clean_name).first()
    if existing_player:
        # Raise HTTP 400 Bad Request error if duplicate
        raise HTTPException(status_code=400, detail="Player already exists!")

    # CREATE NEW PLAYER MODEL:
    # Fill in the Player object with clean_name
    # new_player = Player(name=clean_name)
    new_player = Player(name=clean_name)

    # Save to SQLite database using SQLAlchemy
    db.add(new_player)
    db.commit()      # Write changes to disk
    db.refresh(new_player) # Load generated id from DB

    return new_player

@app.get("/leaderboard", response_model=List[PlayerResponse])
def get_leaderboard(db: Session = Depends(get_db)):
    all_players = db.query(Player).all()
    
    sorted_players = sorted(all_players, key=lambda p:p.ordinal, reverse=True)
    return sorted_players

from itertools import combinations
from openskill.models import PlackettLuce

# Initialize OpenSkill model
model = PlackettLuce()

# --- NEW PYDANTIC SCHEMAS ---
class MatchmakingRequest(BaseModel):
    player_ids: List[int]  # List of exactly 6 player IDs

class TeamMatchupResponse(BaseModel):
    team_a: List[PlayerResponse]
    team_b: List[PlayerResponse]
    win_probability_a: float

# Updated check inside POST /generate-teams:
@app.post("/generate-teams", response_model=TeamMatchupResponse)
def generate_teams(req: MatchmakingRequest, db: Session = Depends(get_db)):
    num_players = len(req.player_ids)
    if num_players < 4:
        raise HTTPException(status_code=400, detail="Matchmaking requires at least 4 players.")

    players = db.query(Player).filter(Player.id.in_(req.player_ids)).all()
    if len(players) != num_players:
        raise HTTPException(status_code=404, detail="One or more player IDs were not found.")

    player_ratings = [(p, model.rating(mu=p.mu, sigma=p.sigma)) for p in players]

    # Half the players go to Team A, remaining to Team B
    team_size = num_players // 2

    best_team_a = None
    best_team_b = None
    best_balance = float('inf')
    best_win_prob_a = 0.50

    # Generate combinations based on team_size
    all_combos = list(combinations(player_ratings, team_size))

    # Evaluate combinations (capping at 100 iterations for speed if pool is large)
    for team_a_tuples in all_combos[:100]:
        team_b_tuples = [p for p in player_ratings if p not in team_a_tuples]

        os_team_a = [rating for _, rating in team_a_tuples]
        os_team_b = [rating for _, rating in team_b_tuples]

        win_probs = model.predict_win([os_team_a, os_team_b])
        win_prob_a = win_probs[0]
        balance_diff = abs(win_prob_a - 0.50)

        if balance_diff < best_balance:
            best_balance = balance_diff
            best_win_prob_a = win_prob_a
            best_team_a = [db_p for db_p, _ in team_a_tuples]
            best_team_b = [db_p for db_p, _ in team_b_tuples]

    return {
        "team_a": best_team_a,
        "team_b": best_team_b,
        "win_probability_a": round(best_win_prob_a, 4)
    }

class RecordMatchRequest(BaseModel):
    team_a_ids: List[int]
    team_b_ids: List[int]
    winner: str  # "team_a", "team_b", or "draw"

@app.post("/matches/record")
def record_match(req: RecordMatchRequest, db: Session = Depends(get_db)):
    team_a_players = db.query(Player).filter(Player.id.in_(req.team_a_ids)).all()
    team_b_players = db.query(Player).filter(Player.id.in_(req.team_b_ids)).all()

    if not team_a_players or not team_b_players:
        raise HTTPException(status_code=400, detail="Invalid player IDs provided.")

    # Convert DB models to OpenSkill Rating objects
    team_a_ratings = [model.rating(mu=p.mu, sigma=p.sigma) for p in team_a_players]
    team_b_ratings = [model.rating(mu=p.mu, sigma=p.sigma) for p in team_b_players]

    # OpenSkill rate ranking: lower index = better rank
    if req.winner == "team_a":
        ranks = [1, 2]
    elif req.winner == "team_b":
        ranks = [2, 1]
    else:  # draw
        ranks = [1, 1]

    # Calculate new ratings
    updated_a, updated_b = model.rate([team_a_ratings, team_b_ratings], ranks=ranks)

    # Update Team A players in DB
    for db_p, os_r in zip(team_a_players, updated_a):
        db_p.mu = os_r.mu
        db_p.sigma = os_r.sigma
        if req.winner == "team_a":
            db_p.wins += 1
        elif req.winner == "team_b":
            db_p.losses += 1

    # Update Team B players in DB
    for db_p, os_r in zip(team_b_players, updated_b):
        db_p.mu = os_r.mu
        db_p.sigma = os_r.sigma
        if req.winner == "team_b":
            db_p.wins += 1
        elif req.winner == "team_a":
            db_p.losses += 1

    db.commit()

    return {"message": "Match recorded and ratings updated successfully!"}

# --- PYDANTIC SCHEMAS ---
class RecordMatchRequest(BaseModel):
    team_a_ids: List[int]
    team_b_ids: List[int]
    winner: str  # "team_a", "team_b", or "draw"


# --- ROUTE: Record Match Results & Update Ratings ---
@app.post("/matches/record")
def record_match(req: RecordMatchRequest, db: Session = Depends(get_db)):
    team_a_players = db.query(Player).filter(Player.id.in_(req.team_a_ids)).all()
    team_b_players = db.query(Player).filter(Player.id.in_(req.team_b_ids)).all()

    if not team_a_players or not team_b_players:
        raise HTTPException(status_code=400, detail="Invalid player IDs provided.")

    # Convert DB models to OpenSkill Rating objects
    team_a_ratings = [model.rating(mu=p.mu, sigma=p.sigma) for p in team_a_players]
    team_b_ratings = [model.rating(mu=p.mu, sigma=p.sigma) for p in team_b_players]

    # OpenSkill ranking: 1 = 1st place, 2 = 2nd place
    if req.winner == "team_a":
        ranks = [1, 2]
    elif req.winner == "team_b":
        ranks = [2, 1]
    else:  # draw
        ranks = [1, 1]

    # Calculate updated ratings
    updated_a, updated_b = model.rate([team_a_ratings, team_b_ratings], ranks=ranks)

    # Apply updates to Team A players
    for db_p, os_r in zip(team_a_players, updated_a):
        db_p.mu = os_r.mu
        db_p.sigma = os_r.sigma
        if req.winner == "team_a":
            db_p.wins += 1
        elif req.winner == "team_b":
            db_p.losses += 1

    # Apply updates to Team B players
    for db_p, os_r in zip(team_b_players, updated_b):
        db_p.mu = os_r.mu
        db_p.sigma = os_r.sigma
        if req.winner == "team_b":
            db_p.wins += 1
        elif req.winner == "team_a":
            db_p.losses += 1

    db.commit()

    return {"message": "Match recorded successfully! Ratings updated."}

@app.post("/admin/reset-ratings")
def reset_all_ratings(db: Session = Depends(get_db)):
    players = db.query(Player).all()
    for player in players:
        player.mu = 25.0
        player.sigma = 8.333
        player.wins = 0
        player.losses = 0
    db.commit()
    return {"message": f"Successfully reset MMR stats for {len(players)} players!"}