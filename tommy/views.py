from tommy.models import Language, Phrase, Profile, Translation

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import ListView, View

class Home(View, LoginRequiredMixin):
    template_name = 'tommy/home.html'

    def get(self, request):
        try:
            profile = Profile.objects.get(user = request.user)
            user_lang = str(profile.learning.language)
        except:
            profile = ''
            user_lang = ''
        languages = Language.objects.all()

        context = {
            'profile': profile,
            'languages': languages,
            'user_lang': user_lang,
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