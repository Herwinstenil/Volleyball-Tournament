from django.shortcuts import render
from django.http import JsonResponse
from .models import MediaItem, Registration, Player, Matches, GalleryItem
from .forms import RegistrationForm, PlayerFormSet


TOURNAMENT_INFO = {
    "name": "Roriri Volleyball Championship 2025",
    "dates": "Aug 30 - 31, 2025",
    "location": "Company Sports Arena",
    "tagline": "Play hard. Play fair. Play together.",
}


def home(request):
    images = MediaItem.objects.filter(media_type="image").order_by('-uploaded_at')
    return render(request, "home.html", {
        "info": TOURNAMENT_INFO,
        "images": images,
    })


def register(request):    
    if request.method == "POST":
        reg_form = RegistrationForm(request.POST)
        player_formset = PlayerFormSet(request.POST, request.FILES)
        
        if reg_form.is_valid() and player_formset.is_valid():
            try:
                # Save registration
                registration = reg_form.save()
                
                # Save players
                for player_form in player_formset:
                    if player_form.cleaned_data.get("name") and player_form.cleaned_data.get("id_card"):
                        player = player_form.save(commit=False)
                        player.registration = registration
                        player.save()
                
                # Redirect to success page with team data
                return render(request, "register_success.html", {"team": registration})
                
            except Exception as e:
                # Handle any errors during save
                print(f"Error saving registration: {e}")
                
    else:
        reg_form = RegistrationForm()
        player_formset = PlayerFormSet()

    return render(request, "register.html", {
        "reg_form": reg_form,
        "player_formset": player_formset
    })


def schedule_view(request):
    matches = Matches.objects.all().order_by('round_number', 'start_time')
    live = Matches.objects.filter(status='live').order_by('start_time')
    upcoming = Matches.objects.filter(status='upcoming').order_by('start_time')

    rounds = {}
    for match in matches:
        rounds.setdefault(match.round_number, []).append(match)

    return render(request, "schedule.html", {
        "matches": matches,
        "live": live,
        "upcoming": upcoming,
        "rounds": rounds
    })


def livescores_page(request):
    return render(request, "score.html")


def live_scores_api(request):
    matches = Matches.objects.all()
    data = []
    for m in matches:
        data.append({
            "id": m.id,
            "team1": m.team1.team_name if m.team1 else "TBD",
            "team2": m.team2.team_name if m.team2 else "TBD",
            "score1": m.score1,
            "score2": m.score2,
            "status": m.status,
        })
    return JsonResponse({"matches": data})


def gallery(request):
    items = GalleryItem.objects.all().order_by('-uploaded_at')
    return render(request, "gallery.html", {"items": items})