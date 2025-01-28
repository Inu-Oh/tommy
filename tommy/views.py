from tommy.models import Language, Phrase, Profile, Translation

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import ListView, View

class Home(View, LoginRequiredMixin):
    template_name = 'tommy/home.html'

    def get(self, request):
        profile = Profile.objects.get(user=request.user)

        context = {
            'profile': profile,
        }
        return render(request, self.template_name, context)


class Glossary(ListView, LoginRequiredMixin):
    template_name = 'tommy/glossary.html'

    def get(self, request, language):
        phrases = Phrase.objects.filter(language=language)
        
        context = {
            'phrases': phrases,
        }
        return render(request, self.template_name, context)