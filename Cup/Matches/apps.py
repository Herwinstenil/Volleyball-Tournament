from django.apps import AppConfig

class MatchesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Matches'

    def ready(self):
        from . import signals  # noqa
