from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, View, CreateView

from .models import Module, Phrase, Translation, Profile, UserPhraseStrength
from .forms import ProfileForm, TestForm, PhraseStrengthForm


class Home(LoginRequiredMixin, View):
    template_name = 'tommy/home.html'

    def get(self, request):
        try:
            profile = Profile.objects.get(user = request.user)
        except:
            create_profile_url = reverse_lazy('tommy:create_profile')
            return redirect(create_profile_url)
        
        unlearned_phrase_count = UserPhraseStrength.objects.filter(
            learned=False, user=request.user).count()
        learned_phrase_count = UserPhraseStrength.objects.filter(
            learned=True, user=request.user).count()
        progress = int((learned_phrase_count * 100) / (learned_phrase_count + unlearned_phrase_count))
 
        context = {
            'profile': profile,
            'unlearned_phrase_count': unlearned_phrase_count,
            'learned_phrase_count': learned_phrase_count,
            'progress': progress,
        }
        return render(request, self.template_name, context)


# Adds a GUI name and creates user testing objects for all course phrases
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
            phrase_strength_form = PhraseStrengthForm()
            phrase_strength = phrase_strength_form.save(commit=False)
            phrase_strength.phrase = phrase
            phrase_strength.user = self.request.user
            phrase_strength.learned = False
            phrase_strength.strength = 0
            phrase_strength.views = 0
            phrase_strength.correct = 0
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
        
        context = {
            'profile': profile,
            'phrases': phrases,
            'translations': translations,
            'phrase_strength_set': phrase_strength_set,
        }
        return render(request, self.template_name, context)


class ModulesView(LoginRequiredMixin, ListView):
    template_name = 'tommy/modules.html'

    def get(self, request):
        profile = Profile.objects.get(user = request.user)
        phrases = Phrase.objects.all()
        user_phrase_data = UserPhraseStrength.objects.filter(user = request.user)
        unlearned_phrase_set = user_phrase_data.filter(
            learned=False, user=request.user)
        unlearned_phrase_count = unlearned_phrase_set.count()
        learned_phrase_set= user_phrase_data.filter(
            learned=True, user=request.user)
        learned_phrase_count = learned_phrase_set.count()
        progress = int((learned_phrase_count * 100) / (learned_phrase_count + unlearned_phrase_count))
        modules = Module.objects.all()

        # Create a list of modules the user has not completed
        open_modules = []
        closed_modules = []
        for module in modules:
            # Get all phrases in module
            phrase_set = phrases.filter(module=module)
            # If module includes unlearned phrases add to open modules list
            for phrase in phrase_set:
                for unlearned_phrase in unlearned_phrase_set:
                    if unlearned_phrase.phrase == phrase:
                        if not module in open_modules:
                            open_modules.append(module)
                for learned_phrase in learned_phrase_set:
                    if learned_phrase.phrase == phrase:
                        if not module in closed_modules:
                            closed_modules.append(module)

        context = {
            'profile': profile,
            'unlearned_phrase_count': unlearned_phrase_count,
            'learned_phrase_count': learned_phrase_count,
            'progress': progress,
            'modules': modules,
            'open_modules': open_modules,
        }
        return render(request, self.template_name, context)

# Selects unlearned phrases for testing
class LearnView(LoginRequiredMixin, View):
    template_name = 'tommy/learn.html'

    def get(self, request, pk):
        profile = Profile.objects.get(user=request.user)
        xp = profile.xp
        form = TestForm()
        module = Module.objects.get(id=pk)
        try:
            phrase = Phrase.objects.filter(module=module)
            phrase_strength_set = UserPhraseStrength.objects.filter(
                learned=False,
                user=request.user,
                phrase=phrase
            )
            testing_phrase = phrase_strength_set.first()
            translations = Translation.objects.filter(phrase=phrase)

            context = {
                'profile': profile,
                'form': form,
                'testing_phrase': testing_phrase, # Phrase strength object
                'phrase': phrase,
                'translations': translations,
                'xp': xp,
            }
            return render(request, self.template_name, context)
        except:
            finished_learning_url = reverse_lazy('tommy:home')
            return redirect(finished_learning_url)
    
    def post(self, request, pk):
        profile = Profile.objects.get(user=request.user)
        xp = profile.xp
        form = TestForm(request.POST)
        module = Module.objects.get(id=pk)
        phrase = Phrase.objects.filter(module=module)
        phrase_strength_set = UserPhraseStrength.objects.filter(
            learned=False,
            user=request.user,
            phrase=phrase
        )
        testing_phrase = phrase_strength_set.first()
        translations = Translation.objects.filter(phrase=phrase)

        context = {
            'profile': profile,
            'form': form,
            'testing_phrase': testing_phrase, # Phrase strength object
            'phrase': phrase,
            'translations': translations,
            'xp': xp,
        }
        if not form.is_valid():
            return render(request, self.template_name, context)
        
        # Set phrase to learned for the user
        testing_phrase.learned = True
        testing_phrase.save()

        # Clean up data for user's answer before testing
        user_answer = form.cleaned_data['answer'].strip()

        # Calculate and set user phrase strength data
        testing_phrase.views = 1
        for translation in translations:
            if user_answer == translation.translation:
                testing_phrase.correct = 1
                testing_phrase.strength = 100
        testing_phrase.save()

        # Add XP points to user profile
        profile.xp += 5
        profile.save()

        success_url = reverse_lazy('tommy:learn', kwargs={'pk': pk})
        return redirect(success_url)


# Selects weakest strength phrases for testing
class PracticeView(LoginRequiredMixin, View):
    template_name = 'tommy/practice.html'

    def get(self, request):
        profile = Profile.objects.get(user=request.user)
        xp = profile.xp
        form = TestForm()
        try:
            phrase_strength_set = UserPhraseStrength.objects.filter(learned=True, user=request.user)
            testing_phrase = phrase_strength_set.earliest('strength')
            phrase = Phrase.objects.get(phrase=testing_phrase.phrase)
            translations = Translation.objects.filter(phrase=phrase)

            context = {
                'profile': profile,
                'form': form,
                'testing_phrase': testing_phrase, # Phrase strength object
                'phrase': phrase,
                'translations': translations,
                'xp': xp,
            }
            return render(request, self.template_name, context)
        except:
            start_learning_url = reverse_lazy('tommy:learn')
            return redirect(start_learning_url)
    
    def post(self, request):
        profile = Profile.objects.get(user=request.user)
        xp = profile.xp
        form = TestForm(request.POST)
        phrase_strength_set = UserPhraseStrength.objects.filter(learned=True, user=request.user)
        testing_phrase = phrase_strength_set.earliest('strength')
        phrase = Phrase.objects.get(phrase=testing_phrase.phrase)
        translations = Translation.objects.filter(phrase=phrase)

        context = {
            'profile': profile,
            'form': form,
            'testing_phrase': testing_phrase, # Phrase strength object
            'phrase': phrase,
            'translations': translations,
            'xp': xp,
        }
        if not form.is_valid():
            return render(request, self.template_name, context)

        # Clean up data for user's answer before testing
        user_answer = form.cleaned_data['answer'].strip()

        # Calculate and set user phrase strength data
        testing_phrase.views += 1
        for translation in translations:
            if user_answer == translation.translation:
                testing_phrase.correct += 1
        testing_phrase.strength = ((testing_phrase.views - (testing_phrase.views - testing_phrase.correct)) * 100) / testing_phrase.views
        testing_phrase.save()

        # Add XP points to user profile
        profile.xp += 5
        profile.save()

        success_url = reverse_lazy('tommy:practice')
        return redirect(success_url)


# Selects phrases not seen for longest time for testing
class ReviewView(LoginRequiredMixin, View):
    template_name = 'tommy/review.html'

    def get(self, request):
        profile = Profile.objects.get(user=request.user)
        xp = profile.xp
        form = TestForm()
        try:
            phrase_strength_set = UserPhraseStrength.objects.filter(learned=True, user=request.user)
            testing_phrase = phrase_strength_set.earliest('updated_at')
            phrase = Phrase.objects.get(phrase=testing_phrase.phrase)
            translations = Translation.objects.filter(phrase=phrase)

            context = {
                'profile': profile,
                'form': form,
                'testing_phrase': testing_phrase, # Phrase strength object
                'phrase': phrase,
                'translations': translations,
                'xp': xp,
            }
            return render(request, self.template_name, context)
        except:
            start_learning_url = reverse_lazy('tommy:learn')
            return redirect(start_learning_url)
    
    def post(self, request):
        profile = Profile.objects.get(user=request.user)
        xp = profile.xp
        form = TestForm(request.POST)
        phrase_strength_set = UserPhraseStrength.objects.filter(learned=True, user=request.user)
        testing_phrase = phrase_strength_set.earliest('updated_at')
        phrase = Phrase.objects.get(phrase=testing_phrase.phrase)
        translations = Translation.objects.filter(phrase=phrase)

        context = {
            'profile': profile,
            'form': form,
            'testing_phrase': testing_phrase, # Phrase strength object
            'phrase': phrase,
            'translations': translations,
            'xp': xp,
        }
        if not form.is_valid():
            return render(request, self.template_name, context)

        # Clean up data for user's answer before testing
        user_answer = form.cleaned_data['answer'].strip()

        # Calculate and set user phrase strength data
        testing_phrase.views += 1
        for translation in translations:
            if user_answer == translation.translation:
                testing_phrase.correct += 1
        testing_phrase.strength = ((testing_phrase.views - (testing_phrase.views - testing_phrase.correct)) * 100) / testing_phrase.views
        testing_phrase.save()

        # Add XP points to user profile
        profile.xp += 5
        profile.save()

        success_url = reverse_lazy('tommy:review')
        return redirect(success_url)
