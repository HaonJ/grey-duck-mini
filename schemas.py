from pydantic import BaseModel
from datetime import datetime

class PlayerBase(BaseModel):
    name: str

class PlayerCreate(PlayerBase):
    pass

class PlayerResponse(PlayerBase):
    id: int
    mu: float
    sigma: float
    wins: int
    losses: int

    class Config:
        from_attributes = True

class MatchCreate(BaseModel):
    team1_players: list[str]
    team2_players: list[str]
    team1_score: int
    team2_score: int

class MatchResponse(BaseModel):
    id: int
    created_at: datetime
    team1_players: str
    team2_players: str
    team1_score: int
    team2_score: int

    class Config:
        from_attributes = True