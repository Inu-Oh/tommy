from django import forms

from tommy.models import Module, Phrase, Translation


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


class UpdatePhraseForm(forms.ModelForm):

    class Meta:
        model = Phrase
        fields = ['module', 'language', 'phrase']


class UpdateTranslationForm(forms.ModelForm):

    class Meta:
        model = Translation
        fields = ['phrase', 'language', 'translation']