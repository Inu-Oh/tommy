from tommy.models import Phrase, Translation

from django.shortcuts import render
from django.views.generic import ListView, View

class Home(View):
    template_name = 'tommy/home.html'

class Glossary(ListView):
    template_name = 'tommy/glossary.html'

    def get(self, request, language):
        phrases = Phrase.objects.filter(language=language)
        
        context = {
            'phrases': phrases,
        }
        return render(request, self.template_name, context)