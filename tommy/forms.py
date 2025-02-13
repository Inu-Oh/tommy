from django import forms

from .models import Profile


class ProfileForm(forms.ModelForm):

    class Meta:
        model = Profile
        fields = ['name', 'learning']
    
    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.fields['name'].label = "Prenom | First name "
        self.fields['learning'].label = "Formation d'anglais | Learning French "