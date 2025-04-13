from django import forms

from .models import Profile, UserPhraseStrength, Module, Phrase, Translation


class ProfileForm(forms.ModelForm):

    class Meta:
        model = Profile
        fields = ['name']
    
    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.fields['name'].label = "First name "


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
        label='',
        widget=forms.TextInput(
            attrs={
                'autofocus': True,
                'autocomplete': 'off',
                'placeholder': ' ...',
                'style': 'height: 5vh; font-size: x-large;'
        }))


class ModuleForm(forms.ModelForm):

    class Meta:
        model = Module
        fields = '__all__'


class CreatePhraseForm(forms.ModelForm):

    class Meta:
        model = Phrase
        fields = ['language', 'phrase']


class CreateTranslationForm(forms.ModelForm):

    class Meta:
        model = Translation
        fields = ['language', 'translation']