from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import TemplateView, UpdateView, View, CreateView, ListView

from datetime import datetime
from random import choice
from unidecode import unidecode
import string

from .models import Module, Phrase, Translation, Profile, UserPhraseStrength
from .forms import ProfileForm, TestForm


# Evaluates a single word to support the eval_phrase funciton
def eval_word(ans_word, phr_word):
    # Variables to help evaluate word score
    correct_count, error_count, ans_length, phr_length = 0, 0, len(ans_word), len(phr_word)
    length = phr_length if phr_length <= ans_length else ans_length

    # Case: user word is one char shorter than correct answer
    if ans_length == phr_length - 1:
        words = []
        for i in range(phr_length):
            word = ""
            for j in range(phr_length):
                if i == j:
                    continue
                else:
                    word += phr_word[j]
            words.append(word)
        if ans_word in words:
            accuracy = ( ( phr_length - 1 ) / phr_length ) * 100
            return accuracy, 1
        
    # Case: user word is one char longer than correct answer
    elif ans_length - 1 == phr_length:
        words = []
        for i in range(ans_length):
            word = ""
            for j in range(ans_length):
                if i == j:
                    continue
                else:
                    word += ans_word[j]
            words.append(word)
        if phr_word in words:
            accuracy = ( ( phr_length - 1 ) / phr_length ) * 100
            return accuracy, 1
    
    # Case: same length or more than one char longer or shorter
    for i in range(length):
        if phr_word[i] == ans_word[i]:
            correct_count += 1
        else:
            error_count += 1

    # Calculate score based on length difference and accuracy
    length_difference = abs(ans_length - phr_length)
    error_count += length_difference
    accuracy = ( correct_count / ( length + length_difference ) ) * 100
    return accuracy, error_count


# Grades the user answer by comparing it to translation phrase
def eval_phrase(answer, phrase):
    # Set variables to help evaluate phrase score
    answer_str = answer.lower().translate(str.maketrans("", "", string.punctuation))
    phrase_str = phrase.lower().translate(str.maketrans("", "", string.punctuation))
    answer_words, phrase_words = answer_str.split(), phrase_str.split()
    answer_str, phrase_str = answer_str.replace(" ", ""), phrase_str.replace(" ", "")
    phrase_length, answer_length = len(phrase_words), len(answer_words)
    phr_len, ans_len = len(phrase_str), len(answer_str)
    error_count, total_score, FULL_SCORE, FAIL = 0, 0, 100, 0

    # Case: Exact same string gets fullscore
    if answer_str == phrase_str:
        return FULL_SCORE, error_count
    
    # One word phrase is evaluated for spelling errors and additional words
    elif phrase_length == 1:
        if answer_length == 1:
            return eval_word(answer, phrase)
        else:
            factor = 1.7 / answer_length
            for word in answer_words:
                word_accuracy, word_errors = eval_word(word, phrase)
                if word_accuracy == FULL_SCORE:
                    error_count = word_errors + ( ans_len - ( phr_len - len(word) ) )
                    return word_accuracy * factor, error_count
            return FAIL, ans_len

    # Multiple word phrase evaluates accuracy of phrases separately
    else:
        # If the number of words is the same compare the words
        if answer_length == phrase_length:
            for i in range(phrase_length):
                if answer_words[i] == phrase_words[i]:
                    total_score += FULL_SCORE
                else:
                    word_score, word_errors = eval_word(answer_words[i], phrase_words[i])
                    total_score += word_score
                    error_count += word_errors
            return (total_score / phrase_length), error_count
        # Otherwise search for the words in the full string
        else:
            if phrase_str in answer_str or answer_str in phrase_str:
                # May result in negative score - OK but can be imporved TODO
                accuracy = ( phr_len - abs( phr_len - ans_len ) ) / phr_len * 100
                error_count += abs(phr_len - ans_len)
                return accuracy, error_count
            else:
                factor = ( ( phrase_length - abs( answer_length - phrase_length ) ) / phrase_length )
                correct_words = 0
                # Counts too many errors - consider revision
                for word in phrase_words:
                    if word in answer_words:
                        correct_words += 1
                    else:
                        error_count += len(word)
                for word in answer_words:
                    if word not in phrase_words:
                        error_count += len(word)
                accuracy = (correct_words / phrase_length) * factor * 100
                return accuracy, error_count / 2


# Styles the feedback HTML to show letters or words with errors
def feedback(answer, phrase, errors, score):
    error_limit = len(phrase) / 8

    # Case: no errors
    if not errors or score == 100:
        return f'<span class="text-success">{answer}</span>'

    # Case: too many errors
    elif errors > error_limit or score < 70:
        return f'<span class="text-danger">{answer}</span>'
    
    # Set variables that help identify errors to mark for feedback
    else:
        answer_str = answer.lower().translate(str.maketrans("", "", string.punctuation))
        phrase_str = phrase.lower().translate(str.maketrans("", "", string.punctuation))
        answer_words, phrase_words = answer.split(), unidecode(phrase_str).split()
        answer_str, phrase_str = answer_str.replace(" ", ""), phrase_str.replace(" ", "")
        answer_length, phrase_length = len(answer_words), len(phrase_words)
        html = '<span class="text-success">'
    
        # Case: one error and user answer same length as correct answer
        if errors == 1 and len(answer) == len(phrase):
            for i in range(len(answer)):
                if unidecode(answer[i].lower()) != unidecode(phrase[i].lower()):
                    html += f'<span class="text-danger">{answer[i]}</span>'
                else:
                    html += answer[i]
        else:
            # Case: user answer is longer than correct answer
            if answer_length >= phrase_length:
                for word in answer_words:
                    check_word = unidecode(word.lower().translate(str.maketrans("", "", string.punctuation)))
                    if check_word not in phrase_words:
                        html += f'<span class="text-danger">{word}</span> '
                    else:
                        html += f'{word} '
                        phrase_words.remove(check_word)
            # Case user answer is short or equal in lengh to correct answer
            else:
                for i in range(answer_length):
                    if phrase_words[i] != unidecode(answer_words[i].translate(str.maketrans("", "", string.punctuation))):
                        html += f'<span class="text-danger">{answer_words[i]}</span> '
                    else:
                        html += f'{answer_words[i]} '
        return html + '\b</span>'


# Styles the feedback HTML for the AccentView class
def accent_feedback(answer, phrase, errors, score):

    # Set variables to help identify errors to mark for feedback
    answer_str = answer.translate(str.maketrans("", "", string.punctuation))
    phrase_str = phrase.translate(str.maketrans("", "", string.punctuation))
    error_limit = len(phrase) / 8

    # Case: user answer is exact same as correct answer
    if (not errors or score == 100) and answer_str == phrase_str:
        return f'<span class="text-success">{answer}</span>'
    
    # Case: too many errors
    elif errors > error_limit or score < 70:
        return f'<span class="text-danger">{answer}</span>'

    # Remaining variables for checking errors to help generate feedback
    else:
        answer_words, phrase_words = answer_str.split(), phrase_str.split()
        ans_feedback, html = answer.split(), '<span class="text-success">'
        answer_words = [answer_words] if isinstance(answer_words, str) else answer_words
        phrase_words = [phrase_words] if isinstance(phrase_words, str) else phrase_words
        answer_length, phrase_length = len(answer_words), len(phrase_words)

        # Case: one or no errors and user answer and correct answer are same length
        if errors <= 1 and len(answer) == len(phrase):
            for i in range(len(answer)):
                if answer[i].lower() != phrase[i].lower():
                    html += f'<span class="text-danger">{answer[i]}</span>'
                else:
                    html += answer[i]
        else:
            # Case: user answer is longer than correct answer
            if answer_length >= phrase_length:
                index = 0
                for word in answer_words:
                    if word not in phrase_words:
                        html += f'<span class="text-danger">{ans_feedback[index]}</span> '
                    else:
                        html += f'{ans_feedback[index]} '
                    index += 1
            # Case user answer is short or equal in lengh to correct answer
            else:
                for i in range(answer_length):
                    if phrase_words[i] != answer_words[i]:
                        html += f'<span class="text-danger">{ans_feedback[i]}</span> '
                    else:
                        html += f'{ans_feedback[i]} '
        return html + '\b</span>'


class Home(LoginRequiredMixin, TemplateView):
    """Displays the app home page menu"""
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
        if request.session.get('testing_phrase'):
            try:
                del request.session['testing_phrase']
                del request.session['user_answer']
                del request.session['response_accuracy']
                del request.session['phrase_language']
                del request.session['feedback_html']
            except:
                pass
        
        # Get user phrase strength data for progress
        user_phrase_strength = UserPhraseStrength.objects.filter(user=request.user)
        if user_phrase_strength.count() > 0:
            unlearned_phrase_count = user_phrase_strength.filter(learned=False).count()
            learned_phrase_count = user_phrase_strength.filter(learned=True).count()
            progress = int((learned_phrase_count * 100) / (learned_phrase_count + unlearned_phrase_count))
        else:
            progress = 0
        

        context = {
            'profile': profile,
            'unlearned_phrase_count': unlearned_phrase_count,
            'learned_phrase_count': learned_phrase_count,
            'progress': progress,
        }
        return render(request, self.template_name, context)


# Recalculates user phrase after each login based on time elapsed
# Login redirects here.
# This page then redirects to Home view after recalculating user phrase strength.
class ResetView(LoginRequiredMixin, UpdateView):
    """Resets the user's strength for each phrase after every login"""
    template_name = 'tommy/reset.html'

    # Login redirects here and hidden form in template redirects to post.
    def get(self, request):
        return render(request, self.template_name)

    # Post view updates user phrase strenght objecs.
    def post(self, request):
        learned_phrases = UserPhraseStrength.objects.filter(learned=True, user=request.user)

        # Recalculate phrase strength based on last time seen by user
        for phrase in learned_phrases:
            now = datetime.now()
            day_of_last_reset = datetime(
                day=phrase.updated_at.day,
                month=phrase.updated_at.month,
                year=phrase.updated_at.year,
                hour=phrase.updated_at.hour,
                minute=phrase.updated_at.minute
            )
            delta = now - day_of_last_reset
            days_since_reset = delta.days
            
            # Function data for review in server log
            # test_log = f"\nDays since reset for phrase \"{str(phrase.phrase)}\""
            # test_log += f": {days_since_reset}\n  Now                : {now}"
            # test_log += f"\n  Time of last reset : {day_of_last_reset}\n"
            # test_log += f"    strength before recalc : {str(phrase.strength)}"
            # print(test_log)

            # Weaken strength if phrase wasn't tested for longer than a day
            if days_since_reset > 0 and phrase.strength > 25:
                phrase.strength -= days_since_reset
                phrase.save()
            
            # Function data for review in server log - part 2
            # print(f"    strength after recalc  : {str(phrase.strength)}")
            
        success_url = 'tommy:home'
        return redirect(success_url)


# Adds a user name for the GUI and creates user testing objects for all course phrases
class ProfileCreateView(LoginRequiredMixin, CreateView):
    """
    Adds a profile name to greet the user
    Creates objects to track the user's skill with all phrases in the database
    """
    model = Profile
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
            UserPhraseStrength.objects.create(
                phrase = phrase,
                user = self.request.user,
                learned = False,
                strength = 0,
                views = 0,
                correct = 0
            )

        success_url = reverse_lazy('tommy:home')
        return redirect(success_url)


class GlossaryView(LoginRequiredMixin, ListView):
    template_name = 'tommy/glossary.html'

    def get(self, request):
        profile = Profile.objects.get(user=request.user)
        phrases = Phrase.objects.all().order_by('phrase')
        phrase_count = phrases.count()
        modules = Module.objects.all()
        translations = Translation.objects.all()
        phrase_strength_set = UserPhraseStrength.objects.filter(user=request.user)
        if phrase_strength_set.count() > 0:
            unlearned_phrase_count = phrase_strength_set.filter(learned=False).count()
            learned_phrase_count = phrase_strength_set.filter(learned=True).count()
        else:
            unlearned_phrase_count, learned_phrase_count = 1, 0
        progress = int((learned_phrase_count * 100) / (learned_phrase_count + unlearned_phrase_count))

        # Create list of dicts for faster data access and search on web page
        phrase_data = []
        strength_data = { 'learned': 0, 'total': 0 }
        for phrase in phrases:
            item = {}
            item["phrase"] = phrase.phrase
            item["id"] = phrase.id
            item["language"] = phrase.language
            item["module"] = phrase.module
            module = modules.get(name=phrase.module)
            item["module_id"] = module.id
            item_translations = translations.filter(phrase=phrase)
            item["translations"] = []
            for item_translation in item_translations:
                item["translations"].append(item_translation.translation)
            user_strength = phrase_strength_set.get(phrase=phrase)
            item["learned"] = user_strength.learned
            item["strength"] = user_strength.strength
            phrase_data.append(item)

            # Calculate overall average user strength
            if user_strength.learned:
                strength_data['learned'] += 1
                strength_data['total'] += user_strength.strength
        if learned_phrase_count > 0:
            strength_data['average'] = round(strength_data['total'] / strength_data['learned'])
        else:
            strength_data['average'] = None

        # Search result implemention for search bar
        search = request.GET.get("search", False)
        if search:
            phrase_data = [d for d in phrase_data if search.lower() in d["phrase"].lower() or search in " ".join(d["translations"]).lower()]

        context = {
            'phrase_data': phrase_data,
            'profile': profile,
            'progress': progress,
            'search': search,
            'phrase_count': phrase_count,
            'strength_data': strength_data,
        }
        return render(request, self.template_name, context)


class ModulesView(LoginRequiredMixin, ListView):
    template_name = 'tommy/modules.html'

    def get(self, request):
        profile = Profile.objects.get(user = request.user)
        phrases = Phrase.objects.all()
        user_phrase_data = UserPhraseStrength.objects.filter(user=request.user)
        if user_phrase_data.count() > 0:
            unlearned_phrase_set = user_phrase_data.filter(learned=False)
            unlearned_phrase_count = unlearned_phrase_set.count()
            learned_phrase_set= user_phrase_data.filter(learned=True)
            learned_phrase_count = learned_phrase_set.count()
        else:
            unlearned_phrase_count, learned_phrase_count = 1, 0
        progress = int((learned_phrase_count * 100) / (learned_phrase_count + unlearned_phrase_count))
        modules = Module.objects.all()

        # Create lists of modules the user has and has not completed
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
        # Delete session data for previous testing phrase if it exists
        if request.session.get('testing_phrase'):
            try:
                del request.session['testing_phrase']
                del request.session['testing_phrase_id']
                del request.session['user_answer']
                del request.session['response_accuracy']
                del request.session['phrase_language']
                del request.session['feedback_html']
            except:
                pass

        profile = Profile.objects.get(user=request.user)
        form = TestForm()
        module = Module.objects.get(id=pk)
        try: # Select random unlearned phrase for testing and get its translations
            phrases = Phrase.objects.filter(module=module)
            unlearned_phrases = UserPhraseStrength.objects.filter(
                learned=False,
                user=request.user,
                phrase__in=phrases
            )
            testing_phrase = choice(unlearned_phrases)
            phrase = phrases.get(id=testing_phrase.phrase_id)

            # Save phrase data to session to be access in POST
            request.session['testing_phrase_id'] = testing_phrase.id

            # Module progress
            module_phrase_count = phrases.count()
            learned_count = UserPhraseStrength.objects.filter(
                learned=True,
                user=request.user,
                phrase__in=phrases
            ).count()
            module_progress = round( (learned_count / module_phrase_count) * 100 )

            context = {
                'profile': profile,
                'form': form,
                'phrase': phrase,
                'testing_phrase': testing_phrase, # Phrase strength object
                'module_progress': module_progress
            }
            return render(request, self.template_name, context)
        except: # If no unlearned phrase is found, redirect to home page
            finished_learning_url = reverse_lazy('tommy:home')
            return redirect(finished_learning_url)
    
    def post(self, request, pk):
        profile = Profile.objects.get(user=request.user)
        form = TestForm(request.POST)
        
        # Get an unlearned phrase for testing and its translations
        testing_phrase = UserPhraseStrength.objects.get(id=request.session.get('testing_phrase_id'))
        translations = Translation.objects.filter(phrase=testing_phrase.phrase)
        phrase = Phrase.objects.get(id=testing_phrase.phrase_id)
        if not form.is_valid():
            context = {
                'profile': profile,
                'form': form,
                'phrase': phrase,
                'testing_phrase': testing_phrase, # Phrase strength object
            }
            return render(request, self.template_name, context)
        translation_langauge = translations[0].language
        phrase_language = "French" if translation_langauge == "English" else "English"

        # Validate and clean user's answer - TODO or refresh page with Invalid input message
        user_answer = form.cleaned_data['answer'].strip()
        invalid_input = False
        for char in "][}{)($@:":
            if char in user_answer:
                invalid_input = True
        if invalid_input:
            context = {
                'profile': profile,
                'form': form,
                'phrase': phrase,
                'testing_phrase': testing_phrase, # Phrase strength object
                'message': "Invalid input"
            }
            # TODO Add error message to template
            return render(request, self.template_name, context)

        # Set phrase to learned. Calculate and set user phrase strength data. Generate feedback.
        MAX_ERRORS = 100

        testing_phrase.learned = True
        testing_phrase.views = 1
        response_accuracy = False
        response_score, errors = -1, MAX_ERRORS
        matched_translation, feedback_html = "", ""
        cleaned_answer = unidecode(user_answer.lower())
        # print("\nUser answer:", user_answer, "Cleanded:", cleaned_answer)
        for translation in translations:
            cleaned_test_phrase = unidecode(translation.translation.lower())
            # print("Phrase:", translation.translation, "Cleaned:", cleaned_test_phrase)
            translation_score, error_count = eval_phrase(cleaned_answer, cleaned_test_phrase)
            if translation_score > response_score:
                response_score, errors = translation_score, error_count
                matched_translation = cleaned_test_phrase
        if not matched_translation:
            matched_translation =  translations[0].translation
        feedback_html = feedback(user_answer, matched_translation, errors, response_score)
        translation_length = len(
            matched_translation.replace(" ", "").translate(str.maketrans("", "", string.punctuation))
        )
        if ((translation_length < 10) and (response_score >= 85)) or response_score >= 90:
            testing_phrase.correct = 1
            testing_phrase.strength = round(response_score)
            # Add XP points to user profile
            profile.xp += 5
            profile.save()
            response_accuracy = True
        testing_phrase.save()

        # Prepare data for feedback view
        success_url = reverse_lazy('tommy:feedback')
        request.session['testing_phrase'] = testing_phrase.phrase.phrase
        request.session['user_answer'] = form.cleaned_data['answer'].strip() # remove ?
        request.session['response_accuracy'] = response_accuracy
        request.session['testing_view'] = 'tommy:learn'
        request.session['module_id'] = pk
        request.session['phrase_language'] = phrase_language
        request.session['feedback_html'] = feedback_html
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
        # Delete session data for previous testing phrase if it exists
        if request.session.get('testing_phrase'):
            try:
                del request.session['testing_phrase']
                del request.session['user_answer']
                del request.session['response_accuracy']
                del request.session['phrase_language']
                del request.session['feedback_html']
            except:
                pass

        profile = Profile.objects.get(user=request.user)
        form = TestForm()
        try:
            phrase_strength_set = UserPhraseStrength.objects.filter(learned=True, user=request.user)
            testing_phrase = phrase_strength_set.earliest('strength')
            phrase = Phrase.objects.get(id=testing_phrase.phrase_id)

            context = {
                'profile': profile,
                'form': form,
                'testing_phrase': testing_phrase, # Phrase strength object
                'phrase': phrase,
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
        phrase = Phrase.objects.get(id=testing_phrase.phrase_id)
        module = Module.objects.get(name=phrase.module)
        translation_language = "English" if phrase.language == "French" else "French"
        translations = Translation.objects.filter(phrase=phrase, language=translation_language)

        if not form.is_valid():
            context = {
                'profile': profile,
                'form': form,
                'testing_phrase': testing_phrase, # Phrase strength object
                'phrase': phrase,
            }
            return render(request, self.template_name, context)

        # Validate and clean user's answer before testing - or refresh with Invalid input message
        user_answer = form.cleaned_data['answer'].strip()
        invalid_input = False
        for char in "][}{)($@:": # TODO review this 
            if char in user_answer:
                invalid_input = True
        if invalid_input:
            context = {
                'profile': profile,
                'form': form,
                'phrase': phrase,
                'testing_phrase': testing_phrase, # Phrase strength object
                'message': "Invalid input"
            }
            # TODO Add error message to template
            return render(request, self.template_name, context)

        # Calculate and set user phrase strength data
        MAX_ERRORS = 100

        testing_phrase.views += 1
        response_score, errors = -1, MAX_ERRORS
        matched_translation, feedback_html = "", ""
        cleaned_answer = unidecode(user_answer.lower())

        for translation in translations:
            cleaned_test_phrase = unidecode(translation.translation.lower())
            translation_score, error_count = eval_phrase(cleaned_answer, cleaned_test_phrase)
            if translation_score > response_score:
                response_score, errors = translation_score, error_count
                matched_translation = cleaned_test_phrase
        if not matched_translation:
            matched_translation =  translations[0].translation
        feedback_html = feedback(user_answer, matched_translation, errors, response_score)
        translation_length = len(
            matched_translation.replace(" ", "").translate(str.maketrans("", "", string.punctuation))
        )
        if (translation_length < 10 and response_score >= 85) or response_score >= 90:
            testing_phrase.correct += 1
            response_accuracy = True
            # Add XP points to user profile
            profile.xp += 5
            profile.save()
        else:
            response_accuracy = False
        testing_phrase.strength = ((testing_phrase.views - (testing_phrase.views - testing_phrase.correct)) * 100) / testing_phrase.views
        testing_phrase.save()

        # Prepare data for feedback view
        success_url = reverse_lazy('tommy:feedback')
        request.session['testing_phrase'] = testing_phrase.phrase.phrase
        request.session['module_id'] = module.id
        request.session['user_answer'] = form.cleaned_data['answer'].strip()
        request.session['response_accuracy'] = response_accuracy
        request.session['testing_view'] = 'tommy:practice'
        request.session['phrase_language'] = phrase.language
        request.session['feedback_html'] = feedback_html
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
        # Delete session data for previous testing phrase if it exists
        if request.session.get('testing_phrase'):
            try:
                del request.session['testing_phrase']
                del request.session['user_answer']
                del request.session['response_accuracy']
                del request.session['phrase_language']
                del request.session['feedback_html']
            except:
                pass

        profile = Profile.objects.get(user=request.user)
        form = TestForm()
        try:
            phrase_strength_set = UserPhraseStrength.objects.filter(learned=True, user=request.user)
            testing_phrase = phrase_strength_set.earliest('updated_at')
            phrase = Phrase.objects.get(id=testing_phrase.phrase_id)

            context = {
                'profile': profile,
                'form': form,
                'testing_phrase': testing_phrase, # Phrase strength object
                'phrase': phrase,
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
        phrase = Phrase.objects.get(id=testing_phrase.phrase_id)
        module = Module.objects.get(name=phrase.module)
        translation_language = "English" if phrase.language == "French" else "French"
        translations = Translation.objects.filter(phrase=phrase, language=translation_language)

        if not form.is_valid():
            context = {
                'profile': profile,
                'form': form,
                'testing_phrase': testing_phrase, # Phrase strength object
                'phrase': phrase,
            }
            return render(request, self.template_name, context)

        # Validate and clean user's answer before testing - or refresh with Invalid input message
        user_answer = form.cleaned_data['answer'].strip()
        invalid_input = False
        for char in "][}{)($@:":
            if char in user_answer:
                invalid_input = True
        if invalid_input:
            context = {
                'profile': profile,
                'form': form,
                'phrase': phrase,
                'testing_phrase': testing_phrase, # Phrase strength object
                'message': "Invalid input"
            }
            # TODO Add error message to template
            return render(request, self.template_name, context)
        
        # Calculate and set user phrase strength data
        MAX_ERRORS = 100

        testing_phrase.views += 1
        response_accuracy = False
        response_score, errors = -1, MAX_ERRORS
        matched_translation, feedback_html = "", ""
        cleaned_answer = unidecode(user_answer.lower())
        for translation in translations:
            cleaned_test_phrase = unidecode(translation.translation.lower())
            translation_score, error_count = eval_phrase(cleaned_answer, cleaned_test_phrase)
            if translation_score > response_score:
                response_score, errors = translation_score, error_count
                matched_translation = cleaned_test_phrase
        if not matched_translation:
            matched_translation =  translations[0].translation
        feedback_html = feedback(user_answer, matched_translation, errors, response_score)
        translation_length = len(
            matched_translation.replace(" ", "").translate(str.maketrans("", "", string.punctuation))
        )
        if ((translation_length < 10) and (response_score >= 85)) or response_score >= 90:
            testing_phrase.correct += 1
            # Add XP points to user profile
            profile.xp += 5
            profile.save()
            response_accuracy = True
        testing_phrase.strength = ((testing_phrase.views - (testing_phrase.views - testing_phrase.correct)) * 100) / testing_phrase.views
        testing_phrase.save()

        # Prepare data for feedback view
        success_url = reverse_lazy('tommy:feedback')
        request.session['testing_phrase'] = testing_phrase.phrase.phrase
        request.session['module_id'] = module.id
        request.session['user_answer'] = form.cleaned_data['answer'].strip()
        request.session['response_accuracy'] = response_accuracy
        request.session['testing_view'] = 'tommy:review'
        request.session['phrase_language'] = phrase.language
        request.session['feedback_html'] = feedback_html
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
        # Delete session data for previous testing phrase if it exists
        if request.session.get('testing_phrase'):
            try:
                del request.session['testing_phrase']
                del request.session['testing_phrase_id']
                del request.session['user_answer']
                del request.session['response_accuracy']
                del request.session['phrase_language']
                del request.session['feedback_html']
            except:
                pass

        profile = Profile.objects.get(user=request.user)
        form = TestForm()
        try: # Select random unlearned phrase for testing and get its translationstry:
            phrase_strength_set = UserPhraseStrength.objects.filter(learned=True, user=request.user)
            testing_phrase = choice(phrase_strength_set)
            phrase = Phrase.objects.get(id=testing_phrase.phrase_id)

            # Save phrase data to session to be access in POST
            request.session['testing_phrase_id'] = testing_phrase.id

            context = {
                'profile': profile,
                'form': form,
                'testing_phrase': testing_phrase, # Phrase strength object
                'phrase': phrase,
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
        testing_phrase = UserPhraseStrength.objects.get(id=request.session.get('testing_phrase_id'))
        phrase = Phrase.objects.get(id=testing_phrase.phrase_id)
        module = Module.objects.get(name=phrase.module)
        translation_language = "English" if phrase.language == "French" else "French"
        translations = Translation.objects.filter(phrase=phrase, language=translation_language)

        if not form.is_valid():
            context = {
                'profile': profile,
                'form': form,
                'testing_phrase': testing_phrase, # Phrase strength object
                'phrase': phrase,
            }
            return render(request, self.template_name, context)

        # Validate and clean user's answer before testing - or refresh with Invalid input message
        user_answer = form.cleaned_data['answer'].strip()
        invalid_input = False
        for char in "][}{)($@:":
            if char in user_answer:
                invalid_input = True
        if invalid_input:
            context = {
                'profile': profile,
                'form': form,
                'phrase': phrase,
                'testing_phrase': testing_phrase, # Phrase strength object
                'message': "Invalid input"
            }
            # TODO Add error message to template
            return render(request, self.template_name, context)

        # Calculate and set user phrase strength data
        testing_phrase.views += 1
        response_accuracy = False
        feedback_html, highest_score = "", 0
        for translation in translations:
            test_user_ans = user_answer.translate(str.maketrans("", "", string.punctuation))
            test_translation = translation.translation.translate(str.maketrans("", "", string.punctuation))
            response_score, error_count = eval_phrase(test_user_ans.lower(), test_translation.lower())
            if test_user_ans == test_translation:
                testing_phrase.correct += 1
                # Add XP points to user profile
                profile.xp += 5
                profile.save()
                response_accuracy = True
                feedback_html = accent_feedback(user_answer, translation.translation, error_count, response_score)
                break
            elif response_score > highest_score:
                feedback_html = accent_feedback(user_answer, translation.translation, error_count, response_score)
        testing_phrase.strength = ((testing_phrase.views - (testing_phrase.views - testing_phrase.correct)) * 100) / testing_phrase.views
        testing_phrase.save()

        # Prepare data for feedback view
        success_url = reverse_lazy('tommy:feedback')
        request.session['testing_phrase'] = testing_phrase.phrase.phrase
        request.session['user_answer'] = user_answer
        request.session['response_accuracy'] = response_accuracy
        request.session['module_id'] = module.id
        request.session['testing_view'] = 'tommy:accent'
        request.session['phrase_language'] = phrase.language
        request.session['feedback_html'] = feedback_html
        return redirect(success_url)


# Feedback page for test results
class FeedbackView(LoginRequiredMixin, View):
    template_name = 'tommy/feedback.html'

    def get(self, request):
        profile = Profile.objects.get(user=request.user)
        testing_phrase = request.session.get('testing_phrase')
        module = Module.objects.get(id=request.session.get('module_id'))
        phrase = Phrase.objects.get(
            phrase=testing_phrase,
            language=request.session.get('phrase_language'),
            module=module
        )
        testing_phrase = UserPhraseStrength.objects.get(phrase=phrase, user=request.user)
        user_answer = request.session.get('user_answer') # remove ?
        response_accuracy = request.session.get('response_accuracy')
        translations = Translation.objects.filter(phrase=phrase)
        testing_view = request.session.get('testing_view')
        feedback_html = request.session.get('feedback_html')

        # Module progress - for LearnView only
        if testing_view == "tommy:learn":
            module_phrases = Phrase.objects.filter(module=module)
            module_phrase_count = module_phrases.count()
            user_learned_count = UserPhraseStrength.objects.filter(
                learned=True,
                user=request.user,
                phrase__in=module_phrases
            ).count()
            module_progress = round( (user_learned_count / module_phrase_count) * 100 )
        else:
            module_progress = None

        # Feedback langauge
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
            'user_answer': user_answer, # remove ?
            'response_accuracy': response_accuracy,
            'testing_phrase': testing_phrase,
            'translations': translations,
            'testing_view': testing_view,
            'result': result,
            'module_id': module_id,
            'feedback_html': feedback_html,
            'module_progress': module_progress
        }
        # Retrieve and pass on test count for the current exercise session
        return render(request, self.template_name, context)