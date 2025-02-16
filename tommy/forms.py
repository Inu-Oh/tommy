from django import forms

from .models import Profile, Phrase


class ProfileForm(forms.ModelForm):

    class Meta:
        model = Profile
        fields = ['name', 'learning']
    
    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.fields['name'].label = "Prenom | First name "
        self.fields['learning'].label = "Formation d'anglais | Learning French "


class TestForm(forms.Form):
    answer = forms.CharField(
        required=True,
        max_length=248,
        min_length=1,
        strip=True,
        label=''
    )