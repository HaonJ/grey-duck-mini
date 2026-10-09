from openskill.models import PlackettLuce
from sqlalchemy.orm import Session
import database, schemas

# Base OpenSkill model scaled 40x for human-readable numbers (~500 start)
model = PlackettLuce()
SCALE = 40.0


def get_players(db: Session):
    return db.query(database.Player).all()


def get_player_by_name(db: Session, name: str):
    return db.query(database.Player).filter(database.Player.name == name).first()


def create_player(db: Session, player: schemas.PlayerCreate):
    db_player = database.Player(name=player.name, mu=1000.0, sigma=333.33)
    db.add(db_player)
    db.commit()
    db.refresh(db_player)
    return db_player


def get_matches(db: Session):
    return (
        db.query(database.Match).order_by(database.Match.created_at.desc()).all()
    )


def recalculate_all_stats(db: Session):
    """Recomputes all player ratings and stats chronologically from match 1."""
    players = db.query(database.Player).all()
    for p in players:
        p.mu = 1000.0
        p.sigma = 333.33
        p.wins = 0
        p.losses = 0

    matches = (
        db.query(database.Match).order_by(database.Match.created_at.asc()).all()
    )
    for match in matches:
        apply_match_effects(db, match)

    db.commit()


def apply_match_effects(db: Session, match: database.Match):
    t1_names = [n.strip() for n in match.team1_players.split(",") if n.strip()]
    t2_names = [n.strip() for n in match.team2_players.split(",") if n.strip()]

    t1_objs = [get_player_by_name(db, name) for name in t1_names if get_player_by_name(db, name)]
    t2_objs = [get_player_by_name(db, name) for name in t2_names if get_player_by_name(db, name)]

    if not t1_objs or not t2_objs:
        return

    # Convert scaled values back to base OpenSkill for computation
    t1_ratings = [model.rating(mu=p.mu / SCALE, sigma=p.sigma / SCALE) for p in t1_objs]
    t2_ratings = [model.rating(mu=p.mu / SCALE, sigma=p.sigma / SCALE) for p in t2_objs]

    t1_win = match.team1_score > match.team2_score
    ranks = [0, 1] if t1_win else [1, 0]

    # Point Differential Multiplier (Blowout games shift MMR up to 60% more)
    score_diff = abs(match.team1_score - match.team2_score)
    margin_weight = 1.0 + (min(score_diff, 10) * 0.06)

    # Record Wins & Losses
    if t1_win:
        for p in t1_objs:
            p.wins += 1
        for p in t2_objs:
            p.losses += 1
    else:
        for p in t1_objs:
            p.losses += 1
        for p in t2_objs:
            p.wins += 1

    # OpenSkill update
    new_ratings = model.rate([t1_ratings, t2_ratings], ranks=ranks)

    old_t1_ord = sum(p.mu - (1.5 * p.sigma) for p in t1_objs) / len(t1_objs)

    for idx, p in enumerate(t1_objs):
        d_mu = (new_ratings[0][idx].mu - t1_ratings[idx].mu) * margin_weight
        d_sig = new_ratings[0][idx].sigma - t1_ratings[idx].sigma
        p.mu += d_mu * SCALE
        p.sigma += d_sig * SCALE

    for idx, p in enumerate(t2_objs):
        d_mu = (new_ratings[1][idx].mu - t2_ratings[idx].mu) * margin_weight
        d_sig = new_ratings[1][idx].sigma - t2_ratings[idx].sigma
        p.mu += d_mu * SCALE
        p.sigma += d_sig * SCALE

    new_t1_ord = sum(p.mu - (1.5 * p.sigma) for p in t1_objs) / len(t1_objs)
    match.mmr_change = round(abs(new_t1_ord - old_t1_ord), 1)


def record_match(db: Session, match_data: schemas.MatchCreate):
    db_match = database.Match(
        team1_players=", ".join(match_data.team1_players),
        team2_players=", ".join(match_data.team2_players),
        team1_score=match_data.team1_score,
        team2_score=match_data.team2_score,
    )
    db.add(db_match)
    db.commit()

    recalculate_all_stats(db)
    db.refresh(db_match)
    return db_match


def update_match(db: Session, match_id: int, match_data: schemas.MatchUpdate):
    db_match = db.query(database.Match).filter(database.Match.id == match_id).first()
    if not db_match:
        return None

    db_match.team1_players = ", ".join(match_data.team1_players)
    db_match.team2_players = ", ".join(match_data.team2_players)
    db_match.team1_score = match_data.team1_score
    db_match.team2_score = match_data.team2_score

    db.commit()
    recalculate_all_stats(db)
    db.refresh(db_match)
    return db_match


def delete_match(db: Session, match_id: int):
    db_match = db.query(database.Match).filter(database.Match.id == match_id).first()
    if not db_match:
        return False
    db.delete(db_match)
    db.commit()
    recalculate_all_stats(db)
    return True