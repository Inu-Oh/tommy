from django import forms

from tommy.models import Module, Phrase, Translation


class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = '__all__'


class CreatePhraseForm(forms.ModelForm):
    class Meta:
        model = Phrase
        fields = ['phrase', 'language']


class CreateTranslationForm(forms.ModelForm):
    class Meta:
        model = Translation
        fields = ['translation', 'language']


class UpdatePhraseForm(forms.ModelForm):
    class Meta:
        model = Phrase
        fields = ['phrase', 'module', 'language']


class UpdateTranslationForm(forms.ModelForm):
    class Meta:
        model = Translation
        fields = ['translation', 'phrase', 'language']