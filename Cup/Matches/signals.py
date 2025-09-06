from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Registration
from .utils import generate_bracket

@receiver(post_save, sender=Registration)
def regenerate_bracket_on_save(sender, instance, **kwargs):
    generate_bracket()


