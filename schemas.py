from datetime import datetime
from pydantic import BaseModel


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

    @property
    def ordinal(self) -> float:
        # Standardized MMR Scale (Default starting rating ~ 500.0)
        return round(max(0.0, self.mu - (1.5 * self.sigma)), 1)

    class Config:
        from_attributes = True


class MatchCreate(BaseModel):
    team1_players: list[str]
    team2_players: list[str]
    team1_score: int
    team2_score: int


class MatchUpdate(MatchCreate):
    pass


class MatchResponse(BaseModel):
    id: int
    created_at: datetime
    team1_players: str
    team2_players: str
    team1_score: int
    team2_score: int
    mmr_change: float

    class Config:
        from_attributes = True