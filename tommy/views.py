from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import ListView, View

from tommy.models import Language, Phrase, Profile, Translation


class Home(LoginRequiredMixin, View):
    template_name = 'tommy/home.html'

    def get(self, request):
        try:
            profile = Profile.objects.get(user = request.user)
            user_lang = str(profile.learning.language)
        except:
            profile = ''
            user_lang = ''

        context = {
            'profile': profile,
            'user_lang': user_lang,
        }
        return render(request, self.template_name, context)


class Glossary(LoginRequiredMixin, ListView):
    template_name = 'tommy/glossary.html'

    def get(self, request):
        try:
            profile = Profile.objects.get(user = request.user)
            user_lang_obj = profile.learning
            user_lang = str(user_lang_obj)
        except:
            profile = ''
            user_lang = ''
        phrases = Phrase.objects.filter(language=user_lang_obj)
        
        context = {
            'phrases': phrases,
            'user_lang': user_lang,
        }
        return render(request, self.template_name, context)