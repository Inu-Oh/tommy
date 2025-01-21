from tommy.models import Word, WordTranslation, Phrase, PhraseTranslation

from django.shortcuts import render
from django.views.generic import ListView, View

class Home(View):
    template_name = 'tommy/home.html'

class Dictionary(ListView):
    template_name = 'tommy/dictionary.html'

    def get(self, request, language='English'):
        words = Word.objects.filter(language=language)
        
        context = {
            'words': words,
        }
        return render(request, self.template_name, context)