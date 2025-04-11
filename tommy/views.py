from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import TemplateView, UpdateView, View, CreateView, ListView

from datetime import datetime
from random import choice
from unidecode import unidecode

from .models import Module, Phrase, Translation, Profile, UserPhraseStrength
from .forms import ProfileForm, TestForm, PhraseStrengthForm


# Function for grading user answer comapred to actual phrase
def grade_answer(answer, phrase):
    phrase_len = len(phrase)
    answer_len = len(answer)
    if abs(phrase_len - answer_len) > 1:
        return False
    typos = 0
    for x, y in zip(answer, phrase):
        if x != y:
            typos += 1
    if phrase_len < 5:
        if typos > 0:
            return False
    if phrase_len > 10:
        if typos > 2:
            return False
    else:
        if typos > 1:
            return False
    return True


class Home(LoginRequiredMixin, TemplateView):
    template_name = 'tommy/home.html'

    def get(self, request):
        # Redirect to create profile page if the user doesn't have one
        try:
            profile = Profile.objects.get(user = request.user)
        except:
            create_profile_url = reverse_lazy('tommy:create_profile')
            return redirect(create_profile_url)
        
        # Delete session data from exercises if it exists
        try: # data from practice, review and accent views
            del request.session['test_count']
        except:
            pass
        try: # data from learn view
            del request.session['module_id']
        except:
            pass
        try: # data from practice, review, accent and learn views
            del request.session['testing_phrase']
            del request.session['user_answer']
            del request.session['testing_view']
            del request.session['respone_accuracy']
        except:
            pass
        
        # Get user phrase strength data for progress
        user_phrase_strength = UserPhraseStrength.objects.all()
        unlearned_phrase_count = user_phrase_strength.filter(
            learned=False, user=request.user).count()
        learned_phrases = user_phrase_strength.filter(
            learned=True, user=request.user)
        learned_phrase_count = learned_phrases.count()
        progress = int((learned_phrase_count * 100) / (learned_phrase_count + unlearned_phrase_count))

        context = {
            'profile': profile,
            'unlearned_phrase_count': unlearned_phrase_count,
            'learned_phrase_count': learned_phrase_count,
            'progress': progress,
        }
        return render(request, self.template_name, context)


"""Recalculates user phrase after each login based on time elapsed
 Login redirects here.
 This page then redirects to Home view after recalculating user phrase strength."""
class ResetView(LoginRequiredMixin, UpdateView):

    def get(self, request):
        learned_phrases = UserPhraseStrength.objects.filter(
            learned=True, user=request.user)

        # Recalculate phrase strength based on last time seen
        for phrase in learned_phrases:
            now = datetime.now()
            day_of_last_reset = datetime(
                day=phrase.updated_at.day,
                month=phrase.updated_at.month,
                year=phrase.updated_at.year,
                hour=phrase.updated_at.hour,
                minute=phrase.updated_at.minute,
                second=phrase.updated_at.second,
                microsecond=phrase.updated_at.microsecond)
            delta = now - day_of_last_reset
            days_since_reset = delta.days
            
            # Combine function data for review in server log
            test_log = f"\nDays since reset for phrase \"{str(phrase.phrase)}\""
            test_log += f": {days_since_reset}\n  Now                : {now}"
            test_log += f"\n  Time of last reset : {day_of_last_reset}\n"
            test_log += f"    strength before recalc : {str(phrase.strength)}"
            print(test_log)

            # Weaken strength if phrase wasn't tested for longer than a day
            if days_since_reset > 0 and phrase.strength > 25:
                phrase.strength -= days_since_reset
                phrase.save()
            
            # Complete funciton data for presentation in server log
            print(f"    strength after recalc  : {str(phrase.strength)}")
            
        success_url = 'tommy:home'
        return redirect(success_url)


# Adds a user name for the GUI and creates user testing objects for all course phrases
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
        unlearned_phrase_count = phrase_strength_set.filter(
            learned=False, user=request.user).count()
        learned_phrase_count = phrase_strength_set.filter(
            learned=True, user=request.user).count()
        progress = int((learned_phrase_count * 100) / (learned_phrase_count + unlearned_phrase_count))

        # Searches
        search_phrases = request.GET.get("search_phrases", False)
        if search_phrases:
            phrases = phrases.filter(Q(phrase__icontains=search_phrases)).select_related().distinct()
        search_translations = request.GET.get("search_translations", False)
        if search_translations:
            translations = translations.filter(Q(translation__icontains=search_translations)).select_related().distinct()

        context = {
            'profile': profile,
            'phrases': phrases,
            'translations': translations,
            'phrase_strength_set': phrase_strength_set,
            'progress': progress,
            'search_phrases': search_phrases,
            'search_translations': search_translations,
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
            # Get all phrases in module to compare with learned and unlearned phrases
            phrase_set = phrases.filter(module=module)
            # If module includes unlearned phrases add to open modules list...
            for phrase in phrase_set:
                for unlearned_phrase in unlearned_phrase_set:
                    if unlearned_phrase.phrase == phrase:
                        if not module in open_modules:
                            open_modules.append(module)
        # ...else add to closed modules list
        for module in modules:
            if not module in open_modules:
                closed_modules.append(module)

        context = {
            'profile': profile,
            'unlearned_phrase_count': unlearned_phrase_count,
            'learned_phrase_count': learned_phrase_count,
            'progress': progress,
            'modules': modules,
            'open_modules': open_modules,
            'closed_modules': closed_modules,
        }
        return render(request, self.template_name, context)


# Selects unlearned phrases for testing / accent not tested
class LearnView(LoginRequiredMixin, View):
    template_name = 'tommy/learn.html'

    def get(self, request, pk):
        profile = Profile.objects.get(user=request.user)
        form = TestForm()
        module = Module.objects.get(id=pk)
        try:
            phrases = Phrase.objects.filter(module=module)
            unlearned_phrases = UserPhraseStrength.objects.filter(
                learned=False,
                user=request.user
            )
            # Get an unlearned phrase for testing and its translations
            for unlearned in unlearned_phrases:
                if unlearned.phrase in phrases:
                    testing_phrase = unlearned.phrase
                    break
            translations = Translation.objects.filter(phrase=testing_phrase)
            phrase = Phrase.objects.get(phrase=testing_phrase.phrase)

            context = {
                'profile': profile,
                'form': form,
                'module': module,
                'phrase': phrase,
                'testing_phrase': testing_phrase, # Phrase strength object
                'translations': translations,

            }
            return render(request, self.template_name, context)
        except: # If no unlearned phrase is found, redirect to home page
            finished_learning_url = reverse_lazy('tommy:home')
            return redirect(finished_learning_url)
    
    def post(self, request, pk):
        profile = Profile.objects.get(user=request.user)
        form = TestForm(request.POST)
        module = Module.objects.get(id=pk)
        # Change the code below to get the testing phrase without repeating the search
        phrases = Phrase.objects.filter(module=module)
        unlearned_phrases = UserPhraseStrength.objects.filter(
            learned=False,
            user=request.user
        )
        # Get an unlearned phrase for testing and its translations
        for unlearned in unlearned_phrases:
            if unlearned.phrase in phrases:
                testing_phrase = unlearned
                break
        translations = Translation.objects.filter(phrase=testing_phrase.phrase)
        phrase = Phrase.objects.get(phrase=testing_phrase.phrase)

        context = {
            'profile': profile,
            'form': form,
            'module': module,
            'phrase': phrase,
            'testing_phrase': testing_phrase, # Phrase strength object
            'translations': translations,
        }
        if not form.is_valid():
            # REVISE: Add error message if form is not valid
            return render(request, self.template_name, context)

        # Prepare user's answer and don't grade accent before testing
        user_answer = form.cleaned_data['answer'].strip()

        # Set phrase to learned. Calculate and set user phrase strength data
        testing_phrase.learned = True
        testing_phrase.views = 1
        respone_accuracy = False
        for translation in translations:
            cleaned_answer = unidecode(user_answer.lower())
            cleaned_test_phrase = unidecode(translation.translation.lower())
            if grade_answer(cleaned_answer, cleaned_test_phrase):
                testing_phrase.correct = 1
                testing_phrase.strength = 100
                # Add XP points to user profile
                profile.xp += 5
                profile.save()
                respone_accuracy = True
        testing_phrase.save()

        # Prepare data for feedback view
        success_url = reverse_lazy('tommy:feedback')
        request.session['testing_phrase'] = testing_phrase.phrase.phrase
        request.session['user_answer'] = form.cleaned_data['answer'].strip()
        request.session['respone_accuracy'] = respone_accuracy
        request.session['testing_view'] = 'tommy:learn'
        request.session['module_id'] = pk
        return redirect(success_url)


# Selects weakest strength phrases for testing / accent not tested
class PracticeView(LoginRequiredMixin, View):
    template_name = 'tommy/practice.html'

    def get(self, request):
       # Get and pass current test count to the request session
        try: # to get test count for current excercise session
            test_count = request.session.get('test_count')
            if test_count >= 12: # reset test count to zero for next session
                request.session['test_count'] = 0
                # end current exercise session and redirect to home page
                finished_exercise_url = reverse_lazy('tommy:home')
                return redirect(finished_exercise_url)
        except: # if test count doesn't exist initiate it
            request.session['test_count'] = 0

        profile = Profile.objects.get(user=request.user)
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
            }
            # Iterate test count for each phrase test before passing to session
            request.session['test_count'] += 1

            return render(request, self.template_name, context)
        except:
            start_learning_url = reverse_lazy('tommy:modules')
            return redirect(start_learning_url)
    
    def post(self, request):
        profile = Profile.objects.get(user=request.user)
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
        }
        if not form.is_valid():
            return render(request, self.template_name, context)

        # Prepare user's answer before testing and don't grade accent
        user_answer = form.cleaned_data['answer'].strip()

        # Calculate and set user phrase strength data
        testing_phrase.views += 1
        respone_accuracy = False
        for translation in translations:
            cleaned_answer = unidecode(user_answer.lower())
            cleaned_test_phrase = unidecode(translation.translation.lower())
            if grade_answer(cleaned_answer, cleaned_test_phrase):
                testing_phrase.correct += 1
                # Add XP points to user profile
                profile.xp += 5
                profile.save()
                respone_accuracy = True
        testing_phrase.strength = ((testing_phrase.views - (testing_phrase.views - testing_phrase.correct)) * 100) / testing_phrase.views
        testing_phrase.save()

        # Prepare data for feedback view
        success_url = reverse_lazy('tommy:feedback')
        request.session['testing_phrase'] = testing_phrase.phrase.phrase
        request.session['user_answer'] = form.cleaned_data['answer'].strip()
        request.session['respone_accuracy'] = respone_accuracy
        request.session['testing_view'] = 'tommy:practice'
        return redirect(success_url)


# Selects phrases not seen for longest time for testing / accent not tested
class ReviewView(LoginRequiredMixin, View):
    template_name = 'tommy/review.html'

    def get(self, request):
       # Get and pass current test count to the request session
        try: # to get test count for current excercise session
            test_count = request.session.get('test_count')
            if test_count >= 15: # reset test count to zero for next session
                request.session['test_count'] = 0
                # end current exercise session and redirect to home page
                finished_exercise_url = reverse_lazy('tommy:home')
                return redirect(finished_exercise_url)
        except: # if test count doesn't exist initiate it
            request.session['test_count'] = 0

        profile = Profile.objects.get(user=request.user)
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
            }
            # Iterate test count for each phrase test before passing to session
            request.session['test_count'] += 1

            return render(request, self.template_name, context)
        except:
            start_learning_url = reverse_lazy('tommy:modules')
            return redirect(start_learning_url)
    
    def post(self, request):
        profile = Profile.objects.get(user=request.user)
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
        }
        if not form.is_valid():
            return render(request, self.template_name, context)

        # Prepare user's answer before testing and don't grade accent
        user_answer = unidecode(form.cleaned_data['answer'].strip())

        # Calculate and set user phrase strength data
        testing_phrase.views += 1
        respone_accuracy = False
        for translation in translations:
            cleaned_answer = unidecode(user_answer.lower())
            cleaned_test_phrase = unidecode(translation.translation.lower())
            if grade_answer(cleaned_answer, cleaned_test_phrase):
                testing_phrase.correct += 1
                # Add XP points to user profile
                profile.xp += 5
                profile.save()
                respone_accuracy = True
        testing_phrase.strength = ((testing_phrase.views - (testing_phrase.views - testing_phrase.correct)) * 100) / testing_phrase.views
        testing_phrase.save()

        # Prepare data for feedback view
        success_url = reverse_lazy('tommy:feedback')
        request.session['testing_phrase'] = testing_phrase.phrase.phrase
        request.session['user_answer'] = form.cleaned_data['answer'].strip()
        request.session['respone_accuracy'] = respone_accuracy
        request.session['testing_view'] = 'tommy:review'
        return redirect(success_url)


# Test correct accent on phrases not seen for longest time
class AccentView(LoginRequiredMixin, View):
    template_name = 'tommy/accent.html'

    def get(self, request):
        # Get and pass current test count to the request session
        try: # to get test count for current excercise session
            test_count = request.session.get('test_count')
            if test_count >= 12: # reset test count to zero for next session
                request.session['test_count'] = 0
                # end current exercise session and redirect to home page
                finished_exercise_url = reverse_lazy('tommy:home')
                return redirect(finished_exercise_url)
        except: # if test count doesn't exist initiate it
            request.session['test_count'] = 0

        profile = Profile.objects.get(user=request.user)
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
            }
            # Iterate test count for each phrase test before passing to session
            request.session['test_count'] += 1

            return render(request, self.template_name, context)
        except:
            start_learning_url = reverse_lazy('tommy:modules')
            return redirect(start_learning_url)
    
    def post(self, request):
        profile = Profile.objects.get(user=request.user)
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
        }
        if not form.is_valid():
            return render(request, self.template_name, context)

        # Clean up data for user's answer before testing and don't test for correct accent
        user_answer = form.cleaned_data['answer'].strip()

        # Calculate and set user phrase strength data
        testing_phrase.views += 1
        respone_accuracy = False
        for translation in translations:
            if user_answer.lower() == translation.translation.lower():
                testing_phrase.correct += 1
                # Add XP points to user profile
                profile.xp += 5
                profile.save()
                respone_accuracy = True
        testing_phrase.strength = ((testing_phrase.views - (testing_phrase.views - testing_phrase.correct)) * 100) / testing_phrase.views
        testing_phrase.save()

        # Prepare data for feedback view
        success_url = reverse_lazy('tommy:feedback')
        request.session['testing_phrase'] = testing_phrase.phrase.phrase
        request.session['user_answer'] = user_answer
        request.session['respone_accuracy'] = respone_accuracy
        request.session['testing_view'] = 'tommy:accent'
        return redirect(success_url)


# Feedback page for test results
class FeedbackView(LoginRequiredMixin, View):
    template_name = 'tommy/feedback.html'

    def get(self, request):
        profile = Profile.objects.get(user=request.user)
        testing_phrase = request.session.get('testing_phrase')
        phrase = Phrase.objects.get(phrase=testing_phrase)
        testing_phrase = UserPhraseStrength.objects.get(
            phrase=phrase,
            user=request.user)
        user_answer = request.session.get('user_answer')
        response_accuracy = request.session.get('respone_accuracy')
        translations = Translation.objects.filter(phrase=phrase)
        testing_view = request.session.get('testing_view')

        if response_accuracy:
            correct = [
                "Amazing", "Awesome", "Great", "Yes!", "You got it", "Wow",
                "You're good at this", "You're great!", "You're awesome"
                ]
            result = choice(correct)
        else:
            wrong = [
                "Better luck next time", "Keep practicing", "Keep at it",
                "You'll get it next time", "It'll stick eventually"
                ]
            result = choice(wrong)
        try:
            module_id = request.session.get('module_id')
        except:
            module_id = None

        context = {
            'profile': profile,
            'user_answer': user_answer,
            'response_accuracy': response_accuracy,
            'testing_phrase': testing_phrase,
            'translations': translations,
            'testing_view': testing_view,
            'result': result,
            'module_id': module_id,
        }
        # Retrieve and pass on test count for the current exercise session
        return render(request, self.template_name, context)
    

# For admins to add modules, phrases and translations
# TODO apply PermissionRequiredMixin
class CreateMenuView(LoginRequiredMixin, ListView):
    template_name = 'tommy/creator.html'
    
    def get(self, request):
        if not request.user.is_staff:
            impostor_url = 'tommy:home'
            return redirect(impostor_url)
        
        profile = Profile.objects.get(user=request.user)
        modules = Module.objects.all().order_by('name')
        phrases = Phrase.objects.all().order_by('phrase')

        context = {
            'profile': profile,
            'modules': modules,
            'phrases': phrases,
        }
        
        return render(request, self.template_name, context)


class CreateModuleView(LoginRequiredMixin, CreateView):
    template_name = 'tommy/add_module.html'
    
    def get(self, request):

        return render(request, self.template_name)


class CreatePhraseView(LoginRequiredMixin, CreateView):
    template_name = 'tommy/add_phrase.html'
    
    def get(self, request, pk):

        return render(request, self.template_name)


class CreateTranslationView(LoginRequiredMixin, CreateView):
    template_name = 'tommy/add_translation.html'
    
    def get(self, request):

        return render(request, self.template_name)


# For admins to edit modules, phrases and translations
# TODO apply PermissionRequiredMixin
# TODO figure out how to access pks for each optional object updated
class EditMenuView(LoginRequiredMixin, ListView):
    template_name = 'tommy/editor.html'
    
    def get(self, request):
        if not request.user.is_staff:
            non_staff_url = 'tommy:home'
            return redirect(non_staff_url)
        
        profile = Profile.objects.get(user=request.user)
        modules = Module.objects.all()
        phrases = Phrase.objects.all()
        translations = Translation.objects.all()

        context = {
            'profile': profile,
            'modules': modules,
            'phrases': phrases,
            'translations': translations,
        }
        
        return render(request, self.template_name, context)