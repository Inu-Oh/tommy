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
            create_profile_url = reverse_lazy('tommy:create_profile')
            return redirect(create_profile_url)
        
        unlearned_phrase_count = UserLearnedPhrase.objects.filter(
            learned=False, user=request.user).count()
        learned_phrase_count = UserLearnedPhrase.objects.filter(
            learned=True, user=request.user).count()

        context = {
            'profile': profile,
            'unlearned_phrase_count': unlearned_phrase_count,
            'learned_phrase_count': learned_phrase_count,
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
            learned_phrase_form = LearnedPhraseForm()
            learned_phrase = learned_phrase_form.save(commit=False)
            learned_phrase.phrase = phrase
            learned_phrase.user = self.request.user
            learned_phrase.learned = False
            learned_phrase.save()
            phrase_strength_form = PhraseStrengthForm()
            phrase_strength = phrase_strength_form.save(commit=False)
            phrase_strength.phrase = phrase
            phrase_strength.user = self.request.user
            phrase_strength.strength = 0
            phrase_strength.views = 0
            phrase_strength.save()

        success_url = reverse_lazy('tommy:home')
        return redirect(success_url)


class GlossaryView(LoginRequiredMixin, ListView):
    template_name = 'tommy/glossary.html'

    def get(self, request):
        profile = Profile.objects.get(user = request.user)
        phrases = Phrase.objects.all()
        translations = Translation.objects.all()
        phrase_strength_set = UserPhraseStrength.objects.filter(user=request.user)
        learned_phrase_set = UserLearnedPhrase.objects.filter(user=request.user)
        
        context = {
            'profile': profile,
            'phrases': phrases,
            'translations': translations,
            'phrase_strength_set': phrase_strength_set,
            'learned_phrase_set': learned_phrase_set,
        }
        return render(request, self.template_name, context)


class LearnView(LoginRequiredMixin, ListView):
    template_name = 'tommy/learn.html'

    def get(self, request):
        profile = Profile.objects.get(user=request.user)
        form = TestForm()
        try:
            unlearned_phrases = UserLearnedPhrase.objects.filter(learned=False, user=request.user)
            testing_phrase = unlearned_phrases.first()
            phrase = Phrase.objects.get(phrase=testing_phrase.phrase)
            phrase_strength = UserPhraseStrength.objects.get(phrase=phrase, user=request.user)
            translations = Translation.objects.filter(phrase=phrase)

            context = {
                'profile': profile,
                'form': form,
                'testing_phrase': testing_phrase,
                'phrase': phrase,
                'phrase_strength': phrase_strength,
                'translations': translations,
            }
            return render(request, self.template_name, context)
        except:
            finished_learning_url = reverse_lazy('tommy:home')
            return redirect(finished_learning_url)
    
    def post(self, request):
        profile = Profile.objects.get(user=request.user)
        form = TestForm(request.POST)
        unlearned_phrases = UserLearnedPhrase.objects.filter(learned=False, user=request.user)
        testing_phrase = unlearned_phrases.first()
        phrase = Phrase.objects.get(phrase=testing_phrase.phrase)
        phrase_strength = UserPhraseStrength.objects.get(phrase=phrase, user=request.user)
        translations = Translation.objects.filter(phrase=phrase)

        context = {
            'profile': profile,
            'form': form,
            'testing_phrase': testing_phrase,
            'phrase': phrase,
            'phrase_strength': phrase_strength,
            'translations': translations,
        }
        if not form.is_valid():
            return render(request, self.template_name, context)
        
        # Set phrase to learned for the user
        testing_phrase.learned = True
        testing_phrase.save()

        # Update user phrase views
        if phrase_strength.views:
            phrase_strength.views += 1
        else:
            phrase_strength.views = 1

        # Calculate and set user phrase strength
        score = -10
        for translation in translations:
            if form.cleaned_data['answer'] == translation.translation:
                score = 10
        phrase_strength.strength = (phrase_strength.strength * phrase_strength.views + score) / phrase_strength.views
        phrase_strength.save()

        success_url = reverse_lazy('tommy:learn')
        return redirect(success_url)


class ReviewView(LoginRequiredMixin, ListView):
    template_name = 'tommy/review.html'

    def get(self, request):
        profile = Profile.objects.get(user=request.user)
        form = TestForm()
        try:
            phrase_strength_set = UserPhraseStrength.objects.filter(user=request.user)
            testing_phrase = phrase_strength_set.earliest('strength')
            phrase = Phrase.objects.get(phrase=testing_phrase.phrase)
            translations = Translation.objects.filter(phrase=phrase)

            context = {
                'profile': profile,
                'form': form,
                'phrase': phrase,
                'testing_phrase': testing_phrase,
                'translations': translations,
            }
            return render(request, self.template_name, context)
        except:
            start_learning_url = reverse_lazy('tommy:learn')
            return redirect(start_learning_url)
    
    def post(self, request):
        profile = Profile.objects.get(user=request.user)
        form = TestForm(request.POST)
        phrase_strength_set = UserPhraseStrength.objects.filter(user=request.user)
        testing_phrase = phrase_strength_set.earliest('strength')
        phrase = Phrase.objects.get(phrase=testing_phrase.phrase)
        translations = Translation.objects.filter(phrase=phrase)

        context = {
            'profile': profile,
            'form': form,
            'phrase': phrase,
            'testing_phrase': testing_phrase,
            'translations': translations,
        }
        if not form.is_valid():
            return render(request, self.template_name, context)

        print(form.cleaned_data['answer'], testing_phrase)
        # Calculate and set user phrase strength data
        testing_phrase.views += 1
        score = -10
        for translation in translations:
            if form.cleaned_data['answer'] == translation.translation:
                score = 10
        testing_phrase.strength += score
        if testing_phrase.strength > 100:
            testing_phrase.strength = 100
        elif testing_phrase.strength < 0:
            testing_phrase.strength = 0
        testing_phrase.save()

        success_url = reverse_lazy('tommy:review')
        return redirect(success_url)