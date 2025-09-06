from django.contrib import admin
from django.utils.html import format_html
from .models import MediaItem, Registration, Player, Matches, GalleryItem


@admin.register(MediaItem)
class MediaItemAdmin(admin.ModelAdmin):
    list_display = ("title", "media_type", "uploaded_at", "preview")
    ordering = ['-uploaded_at']

    def preview(self, obj):
        if obj.is_image():
            return format_html('<img src="{}" width="100" />', obj.file.url)
        elif obj.is_video():
            return format_html('<video width="150" controls><source src="{}" type="video/mp4"></video>', obj.file.url)
        return "-"
    preview.short_description = "Preview"


class PlayerInline(admin.TabularInline):
    model = Player
    extra = 0
    max_num = 11
    fields = ("name", "id_card")


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("team_number", "team_name", "captain_name", "email", "phone", "created_at")
    search_fields = ("team_name", "captain_name", "email", "phone")
    inlines = [PlayerInline]
    ordering = ['team_number']


@admin.register(Matches)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("team1", "team2", "score1", "score2", "round_name", "round_number", "start_time", "court", "winner", "status")
    list_filter = ("status", "round_name")
    search_fields = ("team1__team_name", "team2__team_name", "court", "round_name")

@admin.register(GalleryItem)
class GalleryItemAdmin(admin.ModelAdmin):
    list_display = ("title", "uploaded_at")
    search_fields = ("title",)
