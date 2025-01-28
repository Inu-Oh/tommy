from tommy.models import Language, Phrase, Translation

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import ListView, View

class Home(View, LoginRequiredMixin):
    template_name = 'tommy/home.html'

    def get(self, request):
        languages = Language.objects.all()

        context = {
            'languages': languages,
        }


class Glossary(ListView):
    template_name = 'tommy/glossary.html'

    def get(self, request, language):
        phrases = Phrase.objects.filter(language=language)
        
        context = {
            'phrases': phrases,
        }
        return render(request, self.template_name, context)