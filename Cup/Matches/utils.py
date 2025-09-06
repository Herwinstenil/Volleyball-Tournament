from django.utils import timezone
from datetime import timedelta
import math

def generate_bracket():
    from .models import Registration, Matches
    
    # Clear existing matches
    Matches.objects.all().delete()
    
    # Get all registered teams
    teams = list(Registration.objects.order_by('team_number'))
    total_teams = len(teams)
    
    if total_teams < 2:
        return  # need at least 2 teams to start
    
    # Calculate the next power of 2 for tournament bracket
    bracket_size = 2 ** math.ceil(math.log2(total_teams))
    
    # Create tournament structure based on actual registered teams
    extended_teams = teams.copy()
    
    # Add None (TBD) slots only if needed to reach next power of 2
    while len(extended_teams) < bracket_size:
        extended_teams.append(None)  # Use None instead of "TBD" string
    
    # Set match start time - tournament starts Aug 30, 2025
    base_time = timezone.now().replace(year=2025, month=8, day=30, hour=9, minute=0, second=0, microsecond=0)
    current_time = base_time
    
    # Calculate number of rounds
    num_rounds = int(math.log2(bracket_size))
    
    # Store matches for each round to link them
    all_matches = {}
    
    # Generate matches round by round
    for round_num in range(1, num_rounds + 1):
        round_matches = []
        
        if round_num == 1:
            # First round - pair up teams
            matches_in_round = bracket_size // 2
            
            for i in range(matches_in_round):
                team1 = extended_teams[i*2]
                team2 = extended_teams[i*2 + 1]
                
                # Skip matches where both teams are None
                if team1 is None and team2 is None:
                    continue
                
                # Determine round name
                if bracket_size == 4:
                    round_name = f"Semifinal {i+1}"
                elif bracket_size == 8:
                    round_name = f"Quarterfinal {i+1}"
                elif bracket_size == 16:
                    round_name = f"Round of 16 - Match {i+1}"
                else:
                    round_name = f"Round {round_num} - Match {i+1}"
                
                match = Matches.objects.create(
                    team1=team1,
                    team2=team2,
                    round_number=round_num,
                    round_name=round_name,
                    start_time=current_time,
                    court=f"Court {(i % 4) + 1}",
                    status="upcoming"
                )
                
                # Auto-advance if one team is None (bye)
                if team1 and not team2:
                    match.winner = team1
                    match.status = "finished"
                    match.score1 = 2
                    match.score2 = 0
                    match.save()
                elif team2 and not team1:
                    match.winner = team2
                    match.status = "finished" 
                    match.score1 = 0
                    match.score2 = 2
                    match.save()
                
                round_matches.append(match)
                current_time += timedelta(hours=1)
                
        else:
            # Subsequent rounds
            matches_in_round = bracket_size // (2 ** round_num)
            
            # Set time for next day
            if round_num == 2:
                current_time = base_time + timedelta(days=1)
            elif round_num >= 3:
                current_time = base_time + timedelta(days=round_num-1)
            
            for i in range(matches_in_round):
                # Determine round name
                if round_num == num_rounds:
                    round_name = "Final"
                elif round_num == num_rounds - 1:
                    round_name = f"Semifinal {i+1}"
                elif round_num == num_rounds - 2:
                    round_name = f"Quarterfinal {i+1}"
                else:
                    round_name = f"Round {round_num} - Match {i+1}"
                
                match = Matches.objects.create(
                    team1=None,  # Will be filled by winners from previous round
                    team2=None,
                    round_number=round_num,
                    round_name=round_name,
                    start_time=current_time,
                    court="Main Court" if round_num >= num_rounds - 1 else f"Court {(i % 2) + 1}",
                    status="upcoming"
                )
                round_matches.append(match)
                current_time += timedelta(hours=1, minutes=30)
        
        all_matches[round_num] = round_matches
    
    # Link matches between rounds
    for round_num in range(1, num_rounds):
        current_round_matches = all_matches.get(round_num, [])
        next_round_matches = all_matches.get(round_num + 1, [])
        
        for i, next_match in enumerate(next_round_matches):
            # Link two matches from current round to one match in next round
            if i*2 < len(current_round_matches):
                current_round_matches[i*2].next_match = next_match
                current_round_matches[i*2].save()
            if i*2 + 1 < len(current_round_matches):
                current_round_matches[i*2 + 1].next_match = next_match
                current_round_matches[i*2 + 1].save()
    
    print(f"Generated {bracket_size}-team bracket with {total_teams} registered teams:")
    for round_num, matches in all_matches.items():
        round_name = "Finals" if round_num == num_rounds else f"Round {round_num}"
        print(f"- {round_name}: {len(matches)} matches")