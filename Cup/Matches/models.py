from django.db import models, transaction
from django.utils import timezone
from .utils import generate_bracket
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

class MediaItem(models.Model):
    MEDIA_TYPE_CHOICES = [
        ("image", "Image"),
        ("video", "Video"),
    ]

    title = models.CharField(max_length=200, blank=True)
    media_type = models.CharField(max_length=5, choices=MEDIA_TYPE_CHOICES, default="image")
    file = models.FileField(upload_to="media_files/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or f"Media {self.id}"

    def is_image(self):
        return self.media_type == "image"

    def is_video(self):
        return self.media_type == "video"


class Registration(models.Model):
    team_number = models.PositiveIntegerField(unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    team_name = models.CharField(max_length=120)
    captain_name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30)

    def save(self, *args, **kwargs):
        if not self.team_number:
            with transaction.atomic():
                last_team = Registration.objects.select_for_update().order_by('-team_number').first()
                self.team_number = last_team.team_number + 1 if last_team else 1
                super().save(*args, **kwargs)
                generate_bracket()
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.team_name} (Team {self.team_number})"


class Player(models.Model):
    registration = models.ForeignKey(Registration, related_name="players", on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    id_card = models.ImageField(upload_to="id_cards/")

    def __str__(self):
        return f"{self.name} (Team {self.registration.team_number})"


class Matches(models.Model):
    STATUS_CHOICES = [
        ("upcoming", "Upcoming"),
        ("live", "Live"),
        ("finished", "Finished"),
    ]

    start_time = models.DateTimeField(default=timezone.now)
    team1 = models.ForeignKey('Registration', related_name="home_matches", on_delete=models.SET_NULL, null=True, blank=True)
    team2 = models.ForeignKey('Registration', related_name="away_matches", on_delete=models.SET_NULL, null=True, blank=True)
    score1 = models.PositiveIntegerField(default=0)
    score2 = models.PositiveIntegerField(default=0)
    court = models.CharField(max_length=50, blank=True)
    round_name = models.CharField(max_length=80, blank=True)
    round_number = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="upcoming")

    winner = models.ForeignKey('Registration', related_name="won_matches", on_delete=models.SET_NULL, blank=True, null=True, editable=False)
    next_match = models.ForeignKey('self', related_name="previous_matches", on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        ordering = ["round_number", "start_time"]

    def save(self, *args, **kwargs):
        # winner calculation
        if self.status == "finished":
            if self.score1 > self.score2:
                self.winner = self.team1
            elif self.score2 > self.score1:
                self.winner = self.team2
            else:
                self.winner = None
        else:
            self.winner = None

        super().save(*args, **kwargs)

        # auto-assign to next match
        if self.winner and self.next_match:
            if not self.next_match.team1:
                self.next_match.team1 = self.winner
            elif not self.next_match.team2:
                self.next_match.team2 = self.winner
            self.next_match.save()

        # broadcast live scores
        channel_layer = get_channel_layer()
        matches = Matches.objects.filter(status="live")
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

        async_to_sync(channel_layer.group_send)(
            "scores",
            {
                "type": "scores_update",
                "payload": {"matches": data},
            }
        )

    def __str__(self):
        t1 = self.team1.team_name if self.team1 else "TBD"
        t2 = self.team2.team_name if self.team2 else "TBD"
        return f"{t1} vs {t2} ({self.round_name or self.status})"
    

class GalleryItem(models.Model):
    title = models.CharField(max_length=200, blank=True)
    image = models.ImageField(upload_to="gallery_images/", blank=True, null=True)
    video = models.FileField(upload_to="gallery_videos/", blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or f"Gallery Item {self.id}"