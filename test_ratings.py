from openskill.models import PlackettLuce

model = PlackettLuce()

player1 = model.rating(name='noah')
player2 = model.rating(name='parker')
player3 = model.rating(name='joe')

player4 = model.rating(name='matt')
player5 = model.rating(name='akos')
player6 = model.rating(name='johnny')

team1 = [player1, player2, player3]
team2 = [player4, player5, player6]

print(f"BEFORE: Noah's mu={player1.mu:.2f}, sigma={player1.sigma:.2f}")

# Process match and re-assign updated team lists
[updated_team1, updated_team2] = model.rate([team1, team2], ranks=[0, 1])

# Extract Noah's updated rating from the returned list (he is at index 0)
noah_updated = updated_team1[0]

print(f"AFTER:  Noah's mu={noah_updated.mu:.2f}, sigma={noah_updated.sigma:.2f}")
print(f"Noah's Ordinal MMR: {noah_updated.ordinal():.2f}")