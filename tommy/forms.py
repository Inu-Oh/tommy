from django import forms

from .models import Profile, UserLearnedPhrase, UserPhraseStrength


class ProfileForm(forms.ModelForm):

    class Meta:
        model = Profile
        fields = ['name']
    
    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.fields['name'].label = "First name "


class LearnedPhraseForm(forms.ModelForm):

    class Meta:
        model = UserLearnedPhrase
        fields = []


class PhraseStrengthForm(forms.ModelForm):
    
    class Meta:
        model = UserPhraseStrength
        fields = []


class TestForm(forms.Form):
    answer = forms.CharField(
        required=True,
        max_length=248,
        min_length=1,
        strip=True,
        label=''
    )