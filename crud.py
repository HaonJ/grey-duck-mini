from openskill.models import PlackettLuce
from sqlalchemy.orm import Session
import database, schemas

model = PlackettLuce()


def get_players(db: Session):
    return db.query(database.Player).all()


def get_player_by_name(db: Session, name: str):
    return db.query(database.Player).filter(database.Player.name == name).first()


def create_player(db: Session, player: schemas.PlayerCreate):
    db_player = database.Player(name=player.name)
    db.add(db_player)
    db.commit()
    db.refresh(db_player)
    return db_player


def get_matches(db: Session):
    return (
        db.query(database.Match).order_by(database.Match.created_at.desc()).all()
    )


def record_match(db: Session, match_data: schemas.MatchCreate):
    # Fetch player records
    t1_objs = [get_player_by_name(db, name) for name in match_data.team1_players]
    t2_objs = [get_player_by_name(db, name) for name in match_data.team2_players]

    # Format for OpenSkill
    t1_ratings = [model.rating(mu=p.mu, sigma=p.sigma) for p in t1_objs]
    t2_ratings = [model.rating(mu=p.mu, sigma=p.sigma) for p in t2_objs]

    # Ranks: lower number = higher placement (0 is winner, 1 is loser)
    if match_data.team1_score > match_data.team2_score:
        ranks = [0, 1]
        for p in t1_objs:
            p.wins += 1
        for p in t2_objs:
            p.losses += 1
    else:
        ranks = [1, 0]
        for p in t1_objs:
            p.losses += 1
        for p in t2_objs:
            p.wins += 1

    # Recalculate ratings
    new_ratings = model.rate([t1_ratings, t2_ratings], ranks=ranks)

    for idx, p in enumerate(t1_objs):
        p.mu = new_ratings[0][idx].mu
        p.sigma = new_ratings[0][idx].sigma

    for idx, p in enumerate(t2_objs):
        p.mu = new_ratings[1][idx].mu
        p.sigma = new_ratings[1][idx].sigma

    # Save match record
    db_match = database.Match(
        team1_players=", ".join(match_data.team1_players),
        team2_players=", ".join(match_data.team2_players),
        team1_score=match_data.team1_score,
        team2_score=match_data.team2_score,
    )
    db.add(db_match)
    db.commit()
    db.refresh(db_match)
    return db_match