from itertools import combinations
from openskill.models import PlackettLuce

model = PlackettLuce()

def find_best_matchup(players):
    """
    Given a list of 6 OpenSkill Rating objects,
    returns the two teams of 3 that yield the closest match to 50/50.
    """
    best_team_a = None
    best_team_b = None
    best_balance = float('inf')  # Track the smallest difference from 0.50 win probability

    # 1. Get all possible 3-player combinations from the list of 6 players
    all_3_player_combos = list(combinations(players, 3))

    # We only need to check the first half (10 combos) to avoid checking mirror matches
    for team_a in all_3_player_combos[:10]:
        # team_b is remaining players not in team_a
        team_b = [p for p in players if p not in team_a]

        # 2. Use model.predict_win([list(team_a), team_b])
        win_probs = model.predict_win([list(team_a), team_b])
        
        win_prob_a = win_probs[0]
        # Win probability for team_a is the first element of the returned list
        # win_probs = ...
        # win_prob_a = win_probs[0]

        # 3. Calculate distance from 0.50 (e.g., abs(win_prob_a - 0.50))
        # balance_diff = ...
        balance_diff = abs(win_prob_a - 0.50)
        
        # 4. If this combination is closer to 0.50 than our best_balance so far:
        # update best_balance, best_team_a, and best_team_b!
        if balance_diff < best_balance:
            best_balance = balance_diff
            best_team_a = list(team_a)
            best_team_b = team_b

    return best_team_a, best_team_b, best_balance


# --- TEST YOUR FUNCTION ---
# Create 6 players with varying ratings to test balancing
p1 = model.rating(mu=30.0, sigma=2.0, name="Noah")    # Pro player
p2 = model.rating(mu=25.0, sigma=3.0, name="Parker")  # Avg player
p3 = model.rating(mu=20.0, sigma=3.0, name="Joe")     # Beginner
p4 = model.rating(mu=29.0, sigma=2.0, name="Matt")    # Pro player
p5 = model.rating(mu=24.0, sigma=3.0, name="Akos")    # Avg player
p6 = model.rating(mu=21.0, sigma=3.0, name="Johnny")  # Beginner

all_players = [p1, p2, p3, p4, p5, p6]

team_a, team_b, diff = find_best_matchup(all_players)

print("Best Team A:", [p.name for p in team_a])
print("Best Team B:", [p.name for p in team_b])