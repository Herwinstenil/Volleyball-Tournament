from django import forms
from django.forms import modelformset_factory
from .models import Registration, Player

class RegistrationForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = ["team_name", "captain_name", "email", "phone"]
        widgets = {
            "team_name": forms.TextInput(attrs={"placeholder": "Team Name"}),
            "captain_name": forms.TextInput(attrs={"placeholder": "Captain Name"}),
            "email": forms.EmailInput(attrs={"placeholder": "Email"}),
            "phone": forms.TextInput(attrs={"placeholder": "Phone"}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "")
        phone = phone.lstrip("0").lstrip("+91")
        return f"+91{phone}"


class PlayerForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = ["name", "id_card"]

# Create a formset for exactly 12 players
PlayerFormSet = modelformset_factory(Player, form=PlayerForm, extra=11, max_num=11)
