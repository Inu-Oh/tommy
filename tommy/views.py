from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, View, CreateView

from .models import Phrase, Translation, Profile, UserLearnedPhrase, UserPhraseStrength
from .forms import LearnedPhraseForm, ProfileForm, TestForm, PhraseStrengthForm


class Home(LoginRequiredMixin, View):
    template_name = 'tommy/home.html'

    def get(self, request):
        try:
            profile = Profile.objects.get(user = request.user)
        except:
            profile = ''

        context = {
            'profile': profile,
        }
        return render(request, self.template_name, context)


class ProfileCreateView(LoginRequiredMixin, CreateView):
    template_name = 'tommy/create_profile.html'

    def get(self, request):
        form = ProfileForm()
        context = {'form': form}
        return render(request, self.template_name, context)
    
    def post(self, request):
        form = ProfileForm(request.POST)
        if not form.is_valid():
            context = {'form': form}
            return render(request, self.template_name, context)
        
        # Add user to profile form
        profile = form.save(commit=False)
        profile.user = self.request.user
        profile.save()

        # For all phrases, set user strength to 0 and learned to false
        phrases = Phrase.objects.all()
        for phrase in phrases:
            learned_phrase = LearnedPhraseForm()
            learned_phrase.phrase = phrase
            learned_phrase.user = self.request.user
            learned_phrase.learned = False
            learned_phrase.save()
            phrase_strength = PhraseStrengthForm()
            phrase_strength.phrase = phrase
            phrase_strength.user = self.request.user
            phrase_strength.strength = 0
            phrase_strength.save()
        

        success_url = reverse_lazy('tommy:home')

        return redirect(success_url)


class GlossaryView(LoginRequiredMixin, ListView):
    template_name = 'tommy/glossary.html'

    def get(self, request):
        profile = Profile.objects.get(user = request.user)
        phrases = Phrase.objects.all()
        translations = Translation.objects.all()
        phrase_strength_set = UserPhraseStrength.objects.filter(user = request.user)
        
        context = {
            'profile': profile,
            'phrases': phrases,
            'translations': translations,
            'phrase_strength_set': phrase_strength_set,
        }
        return render(request, self.template_name, context)


class LearnView(LoginRequiredMixin, ListView):
    template_name = 'tommy/learn.html'

    def get(self, request):
        profile = Profile.objects.get(user = request.user)
        form = TestForm()
        
        context = {
            'profile': profile,
            'form': form,
        }
        return render(request, self.template_name, context)