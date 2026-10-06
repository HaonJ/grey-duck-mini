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
        return round(max(0.0, self.mu - (3.0 * self.sigma)), 2)

    class Config:
        from_attributes = True