from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import TemplateView, UpdateView, View, CreateView, ListView

from datetime import datetime
import html
from random import choice
from unidecode import unidecode
import string

from .models import Module, Phrase, Translation, Profile, UserPhraseStrength
from .forms import ProfileForm, TestForm

# Constants for setting user phrase view counts, evaluating accuracy and errors in testing views.
INITIATE_COUNT, UNASSESSED_ACCURACY, UNASSESSED_SCORE, MAX_ERRORS = 1, False, -1, 100


def eval_word(user_answer_word, correct_word):
    """
    Evaluates the test score for a word entered by the user in comparison to correct
    answer. Supports eval_tranlation function to evaluate translation accuracy.
    """
    # Variables to help evaluate word score
    correct_count, error_count = 0, 0
    answer_length, actual_length = len(user_answer_word), len(correct_word)

    # Case: user answer word is one char shorter than correct word
    if answer_length == actual_length - 1:
        words = []
        for i in range(actual_length):
            word = ""
            for j in range(actual_length):
                if i == j:
                    continue
                else:
                    word += correct_word[j]
            words.append(word)
        if user_answer_word in words:
            accuracy = ( ( actual_length - 1 ) / actual_length ) * 100
            return accuracy, 1
        
    # Case: user answer word is one char longer than correct word
    elif answer_length - 1 == actual_length:
        words = []
        for i in range(answer_length):
            word = ""
            for j in range(answer_length):
                if i == j:
                    continue
                else:
                    word += user_answer_word[j]
            words.append(word)
        if correct_word in words:
            accuracy = ( ( actual_length - 1 ) / actual_length ) * 100
            return accuracy, 1
    
    # Case: same length or more than one char longer or shorter
    shorter_word_length = min(actual_length, answer_length)
    for i in range(shorter_word_length):
        if correct_word[i] == user_answer_word[i]:
            correct_count += 1
        else:
            error_count += 1

    # Calculate score based on length difference and accuracy
    length_difference = abs(answer_length - actual_length)
    error_count += length_difference
    accuracy = ( correct_count / ( shorter_word_length + length_difference ) ) * 100
    return accuracy, error_count


def eval_tranlation(user_answer, correct_translation):
    """
    Evaluates the test score for a translation entered by the user
    in comparison to correct translation.
    """
    # Set variables to help evaluate accuracty of translation
    answer_str = user_answer.lower().translate(str.maketrans("", "", string.punctuation))
    correct_str = correct_translation.lower().translate(str.maketrans("", "", string.punctuation))
    answer_words, correct_words = answer_str.split(), correct_str.split()
    answer_str, correct_str = answer_str.replace(" ", ""), correct_str.replace(" ", "")
    actual_word_count, answer_word_count = len(correct_words), len(answer_words)
    actual_str_len, answer_str_len = len(correct_str), len(answer_str)
    error_count, total_score, FULL_SCORE, FAIL = 0, 0, 100, 0

    # Case: Exact same string gets fullscore
    if answer_str == correct_str:
        return FULL_SCORE, error_count
    
    # One word translation is evaluated for spelling errors and superfluous words
    elif actual_word_count == 1:
        if answer_word_count == 1:
            return eval_word(user_answer, correct_translation)
        else:
            factor = 1.7 / answer_word_count
            for word in answer_words:
                word_accuracy, word_errors = eval_word(word, correct_translation)
                if word_accuracy == FULL_SCORE:
                    error_count = word_errors + ( answer_str_len - ( actual_str_len - len(word) ) )
                    return word_accuracy * factor, error_count
            return FAIL, answer_str_len

    # Multiple word translation evaluates accuracy of words separately
    else:
        # If the number of words is the same compare the words one by one
        if answer_word_count == actual_word_count:
            for i in range(actual_word_count):
                if answer_words[i] == correct_words[i]:
                    total_score += FULL_SCORE
                else:
                    word_score, word_errors = eval_word(answer_words[i], correct_words[i])
                    total_score += word_score
                    error_count += word_errors
            return (total_score / actual_word_count), error_count
        # Otherwise search for the words in the full string
        else:
            if correct_str in answer_str or answer_str in correct_str:
                accuracy = ( ( actual_str_len - abs( actual_str_len - answer_str_len ) )
                            / actual_str_len * FULL_SCORE )
                accuracy = accuracy if accuracy > FAIL else FAIL
                error_count += abs(actual_str_len - answer_str_len)
                return accuracy, error_count
            else:
                factor = ( ( actual_word_count - abs( answer_word_count - actual_word_count ) )
                          / actual_word_count )
                correct_word_count = 0
                # TODO - This error count is not ideal and can be improved
                for word in correct_words:
                    if word in answer_words:
                        correct_word_count += 1
                    else:
                        error_count += int(len(word) / 2)
                for word in answer_words:
                    if word not in correct_words:
                        error_count += int(len(word) / 2)
                accuracy = (correct_word_count / actual_word_count) * factor * FULL_SCORE
                return accuracy, error_count


def feedback(user_answer, correct_translation, errors, score):
    """
    Generates HTML style tags to provide better feedback on translation accuracy.
    Used for learn, practice and review exercise view classes.
    """
    error_limit = len(correct_translation) / 8

    # Case: no errors
    if not errors or score == 100:
        return f'<span class="text-success">{user_answer}</span>'

    # Case: too many errors
    elif errors > error_limit or score < 70:
        return f'<span class="text-danger">{user_answer}</span>'
    
    # Set variables that help identify errors to mark for feedback
    else:
        actual_str = correct_translation.lower().translate(str.maketrans("", "", string.punctuation))
        answer_words, actual_words = user_answer.split(), unidecode(actual_str).split()
        answer_word_count, actual_word_count = len(answer_words), len(actual_words)
        user_answer_len = len(user_answer)
        html = '<span class="text-success">'
    
        # Case: one error and user answer same length as correct answer
        if errors == 1 and user_answer_len == len(correct_translation):
            for i in range(user_answer_len):
                if unidecode(user_answer[i].lower()) != unidecode(correct_translation[i].lower()):
                    html += f'<span class="text-danger">{user_answer[i]}</span>'
                else:
                    html += user_answer[i]
        else:
            # Case: user answer is longer than correct answer
            if answer_word_count >= actual_word_count:
                for word in answer_words:
                    check_word = unidecode(
                        word.lower().translate(str.maketrans("", "", string.punctuation))
                    )
                    if check_word not in actual_words:
                        html += f'<span class="text-danger">{word}</span> '
                    else:
                        html += f'{word} '
                        actual_words.remove(check_word)
            # Case user answer is short or equal in lengh to correct answer
            else:
                for i in range(answer_word_count):
                    if actual_words[i] != unidecode(
                        answer_words[i].translate(str.maketrans("", "", string.punctuation))
                    ):
                        html += f'<span class="text-danger">{answer_words[i]}</span> '
                    else:
                        html += f'{answer_words[i]} '
        return html + '\b</span>'


def accent_feedback(user_answer, correct_translation, errors, score):
    """
    Generates HTML style tags to provide better feedback on translation
    accuracy. Used in the accent testing extreme difficulty excercise view.
    """
    # Set variables to help identify errors to mark for feedback
    answer_str = user_answer.translate(str.maketrans("", "", string.punctuation))
    actual_str = correct_translation.translate(str.maketrans("", "", string.punctuation))
    error_limit = len(correct_translation) / 8

    # Case: user answer is exact same as correct answer
    if (not errors or score == 100) and answer_str == actual_str:
        return f'<span class="text-success">{user_answer}</span>'
    
    # Case: too many errors
    elif errors > error_limit or score < 70:
        return f'<span class="text-danger">{user_answer}</span>'

    # Remaining variables for checking errors to help generate feedback
    else:
        answer_words, actual_words = answer_str.split(), actual_str.split()
        ans_feedback, html = user_answer.split(), '<span class="text-success">'
        answer_words = [answer_words] if isinstance(answer_words, str) else answer_words
        actual_words = [actual_words] if isinstance(actual_words, str) else actual_words
        answer_word_count, actual_word_count = len(answer_words), len(actual_words)

        # Case: one or no errors and user answer and correct answer are same length
        if errors <= 1 and len(user_answer) == len(correct_translation):
            for i in range(len(user_answer)):
                if user_answer[i].lower() != correct_translation[i].lower():
                    html += f'<span class="text-danger">{user_answer[i]}</span>'
                else:
                    html += user_answer[i]
        else:
            # Case: user answer is longer than correct answer
            if answer_word_count >= actual_word_count:
                index = 0
                for word in answer_words:
                    if word not in actual_words:
                        html += f'<span class="text-danger">{ans_feedback[index]}</span> '
                    else:
                        html += f'{ans_feedback[index]} '
                    index += 1
            # Case user answer is short or equal in lengh to correct answer
            else:
                for i in range(answer_word_count):
                    if actual_words[i] != answer_words[i]:
                        html += f'<span class="text-danger">{ans_feedback[i]}</span> '
                    else:
                        html += f'{ans_feedback[i]} '
        return html + '\b</span>'


class Home(LoginRequiredMixin, TemplateView):
    """Displays the app home page menu with exercises for users and nav bar"""

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
        if request.session.get('phrase'):
            try:
                del request.session['phrase']
                del request.session['user_answer']
                del request.session['response_accuracy']
                del request.session['phrase_language']
                del request.session['feedback_html']
            except:
                pass
        
        # Get user phrase strength data for progress
        user_phrase_strength_set = UserPhraseStrength.objects.filter(user=request.user)
        if user_phrase_strength_set.count() > 0:
            unlearned_phrase_count = user_phrase_strength_set.filter(learned=False).count()
            learned_phrase_count = user_phrase_strength_set.filter(learned=True).count()
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


class ResetView(LoginRequiredMixin, UpdateView):
    """Resets the user's strength for all phrases after each login and redirects home."""
    # Recalculates user phrase after each login based on time elapsed. Login redirects
    # here. The form autosubmits, post updates all user scores then redirects home.
    template_name = 'tommy/reset.html'

    # Login redirects to get and hidden form in template redirects to post.
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
    """
    Searches and list all phrases in the database along with their translations.
    Displays summary of user progress
    """
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

        # Create list of dicts for faster data access and search response on web page load
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
    """Displays all available and completed modules as button links to learning exercises"""

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

        if msg := request.session.get('module_complete_msg'):
            module_complete_msg = msg
            del request.session['module_complete_msg']
        else:
            module_complete_msg = ""

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
            'module_complete_msg': module_complete_msg,
        }
        return render(request, self.template_name, context)


class LearnView(LoginRequiredMixin, View):
    """
    Test form. Prompts user to translate phrases from a learning module. Chooses
    random phrase one at a time. (Does not test accent and punctuation.)
    """
    template_name = 'tommy/learn.html'

    def get(self, request, pk):
        # Delete session data for previous testing phrase if it exists
        if request.session.get('phrase'):
            try:
                del request.session['phrase']
                del request.session['user_phrase_strength_id']
                del request.session['user_answer']
                del request.session['response_accuracy']
                del request.session['phrase_language']
                del request.session['feedback_html']
            except:
                pass

        profile = Profile.objects.get(user=request.user)
        form = TestForm()
        module = Module.objects.get(id=pk)
        phrases = module.phrases_in_module.all()
        try: # Select random unlearned phrase for testing and save it to session for access in POST
            user_unlearned_phrase_objects = UserPhraseStrength.objects.filter(
                learned=False,
                user=request.user,
                phrase__in=phrases
            )
            user_phrase_strength = choice(user_unlearned_phrase_objects)
            phrase = phrases.get(id=user_phrase_strength.phrase_id)
            request.session['user_phrase_strength_id'] = user_phrase_strength.id

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
                'user_phrase_strength': user_phrase_strength, # Phrase strength object
                'module_progress': module_progress,
                'module_name': module.name
            }
            return render(request, self.template_name, context)
        except: # If no unlearned phrase is found, redirect to home page
            msg = f'Congrats! You finished the "{module.name}" module.'
            request.session['module_complete_msg'] = msg
            finished_learning_url = reverse_lazy('tommy:modules')
            return redirect(finished_learning_url)
    
    def post(self, request, pk):
        profile = Profile.objects.get(user=request.user)
        form = TestForm(request.POST)
        
        # Get an unlearned phrase for testing and its translations
        user_phrase_strength = UserPhraseStrength.objects.get(
                    id=request.session.get('user_phrase_strength_id')
                )
        phrase = Phrase.objects.get(id=user_phrase_strength.phrase_id)
        translations = phrase.phrase_translations.all()
 
        if not form.is_valid():
            context = {
                'profile': profile,
                'form': form,
                'phrase': phrase,
                'user_phrase_strength': user_phrase_strength, # Phrase strength object
            }
            return render(request, self.template_name, context)
        translation_langauge = translations[0].language
        phrase_language = "French" if translation_langauge == "English" else "English"

        # Clean user's answer and escape any html entities before testing
        user_answer = html.escape(form.cleaned_data['answer'].strip())

        # Track the phrase as learned by the user and initiate view count.
        user_phrase_strength.learned = True
        user_phrase_strength.views = INITIATE_COUNT

        # Set variables to evaluate score and prepare feedback.
        response_score = UNASSESSED_SCORE
        errors = MAX_ERRORS
        matched_translation = ""
        feedback_html = ""
        cleaned_answer = unidecode(user_answer.lower())

        # Find a translation that best matches the user's answer and evaluate score and errors
        for translation in translations:
            cleaned_test_phrase = unidecode(translation.translation.lower())
            translation_score, error_count = eval_tranlation(cleaned_answer, cleaned_test_phrase)
            if translation_score > response_score:
                response_score = translation_score
                errors = error_count
                matched_translation = cleaned_test_phrase
        if not matched_translation: # Use a dummy translation if user's answer has no match
            matched_translation = translations[0].translation

        # Generate feedback to display to user
        feedback_html = feedback(user_answer, matched_translation, errors, response_score)

        # If evaluation passes mark, add points to user profile and raise user phrase strength
        translation_len = len(
            matched_translation.replace(" ", "").translate(str.maketrans("", "", string.punctuation))
        )
        if ((translation_len < 10) and (response_score >= 85)) or response_score >= 90:
            user_phrase_strength.correct += 1
            user_phrase_strength.strength = round(response_score)
            profile.xp += 5
            profile.save()
            response_accuracy = True
        else:
            response_accuracy = False
        
        # Save the user's phrase score
        user_phrase_strength.save()

        # Prepare data for feedback view
        success_url = reverse_lazy('tommy:feedback')
        request.session['phrase'] = user_phrase_strength.phrase.phrase
        request.session['user_answer'] = user_answer # Backup in csae of error with HTML
        request.session['response_accuracy'] = response_accuracy
        request.session['testing_view'] = 'tommy:learn'
        request.session['module_id'] = pk
        request.session['phrase_language'] = phrase_language
        request.session['feedback_html'] = feedback_html
        return redirect(success_url)


class PracticeView(LoginRequiredMixin, View):
    """
    Test form. Prompts user to translate phrases one at a time. Selects user's
    weakest phrase each time. (Does not test accent and punctuation.)
    """

    template_name = 'tommy/practice.html'

    def get(self, request):
        # Set or reset the exercise session test count. End exerice after count 15.
        try:
            test_count = request.session.get('test_count')
            if test_count >= 12:
                request.session['test_count'] = 0
                finished_exercise_url = reverse_lazy('tommy:home')
                return redirect(finished_exercise_url)
        except:
            request.session['test_count'] = 0

        # Delete session data for previous testing phrase if it exists
        if request.session.get('phrase'):
            try:
                del request.session['phrase']
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
            user_phrase_strength = phrase_strength_set.earliest('strength')
            phrase = Phrase.objects.get(id=user_phrase_strength.phrase_id)

            # Debug info for server log TODO - remove later
            phr_str = user_phrase_strength
            print("\nBefore testing:", end=" ")
            print(phr_str, "updated at:", phr_str.updated_at, "\nviews:", phr_str.views, end=" ")
            print("correctly answered:", phr_str.correct, "strength:", phr_str.strength)

            context = {
                'profile': profile,
                'form': form,
                'user_phrase_strength': user_phrase_strength, # Phrase strength object
                'phrase': phrase,
            }
            # Increment test count for each phrase test before passing to session
            request.session['test_count'] += 1

            return render(request, self.template_name, context)
        except:
            start_learning_url = reverse_lazy('tommy:modules')
            return redirect(start_learning_url)
    
    def post(self, request):
        profile = Profile.objects.get(user=request.user)
        form = TestForm(request.POST)
        phrase_strength_set = UserPhraseStrength.objects.filter(learned=True, user=request.user)
        user_phrase_strength = phrase_strength_set.earliest('strength')
        phrase = Phrase.objects.get(id=user_phrase_strength.phrase_id)
        module = Module.objects.get(name=phrase.module)
        translations = phrase.phrase_translations.all()

        if not form.is_valid():
            context = {
                'profile': profile,
                'form': form,
                'user_phrase_strength': user_phrase_strength, # Phrase strength object
                'phrase': phrase,
            }
            return render(request, self.template_name, context)

        # Clean user's answer and escape any html entities before testing
        user_answer = html.escape(form.cleaned_data['answer'].strip())

        # Increment user view of current phrase
        user_phrase_strength.views += 1

        # Set variables to evaluate user's translation of current prhase
        response_score = UNASSESSED_SCORE
        errors = MAX_ERRORS
        matched_translation = ""
        feedback_html = ""
        cleaned_answer = unidecode(user_answer.lower())

        # Find a translation that best matches the user's answer and evaluate score and errors
        for translation in translations:
            cleaned_test_phrase = unidecode(translation.translation.lower())
            translation_score, error_count = eval_tranlation(cleaned_answer, cleaned_test_phrase)
            if translation_score > response_score:
                response_score = translation_score
                errors = error_count
                matched_translation = cleaned_test_phrase
        if not matched_translation: # Use a dummy translation if user's answer has no match
            matched_translation =  translations[0].translation
        
        # Generate feedback to display to user
        feedback_html = feedback(user_answer, matched_translation, errors, response_score)

        # If evaluation passes mark, add points to user profile and raise user phrase strength
        translation_len = len(
            matched_translation.replace(" ", "").translate(str.maketrans("", "", string.punctuation))
        )
        if (translation_len < 10 and response_score >= 85) or response_score >= 90:
            user_phrase_strength.correct += 1
            response_accuracy = True
            profile.xp += 5
            profile.save()
        else:
            response_accuracy = False
        user_phrase_strength.strength = ((
            user_phrase_strength.views - (user_phrase_strength.views - user_phrase_strength.correct))
                * 100) / user_phrase_strength.views
        
        # Save the user's phrase score
        user_phrase_strength.save()

        # Prepare data for feedback view
        success_url = reverse_lazy('tommy:feedback')
        request.session['phrase'] = user_phrase_strength.phrase.phrase
        request.session['module_id'] = module.id
        request.session['user_answer'] = user_answer # Used as backup in case of error with HTML
        request.session['response_accuracy'] = response_accuracy
        request.session['testing_view'] = 'tommy:practice'
        request.session['phrase_language'] = phrase.language
        request.session['feedback_html'] = feedback_html
        return redirect(success_url)


class ReviewView(LoginRequiredMixin, View):
    """
    Test form. Prompts user to translate phrases one at a time. Selects phrase not 
    seen by user in longest time. (Does not test accent and punctuation.)
    """
    template_name = 'tommy/review.html'

    def get(self, request):
        # Set or reset the exercise session test count. End exerice after count 15.
        try:
            test_count = request.session.get('test_count')
            if test_count >= 15:
                request.session['test_count'] = 0
                finished_exercise_url = reverse_lazy('tommy:home')
                return redirect(finished_exercise_url)
        except:
            request.session['test_count'] = 0
            
        # Delete session data for previous testing phrase if it exists
        if request.session.get('phrase'):
            try:
                del request.session['phrase']
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
            user_phrase_strength = phrase_strength_set.earliest('updated_at')
            phrase = Phrase.objects.get(id=user_phrase_strength.phrase_id)

            context = {
                'profile': profile,
                'form': form,
                'user_phrase_strength': user_phrase_strength,
                'phrase': phrase,
            }
            # Increment test count for each phrase test before passing to session
            request.session['test_count'] += 1

            return render(request, self.template_name, context)
        except:
            start_learning_url = reverse_lazy('tommy:modules')
            return redirect(start_learning_url)
    
    def post(self, request):
        profile = Profile.objects.get(user=request.user)
        form = TestForm(request.POST)
        phrase_strength_set = UserPhraseStrength.objects.filter(learned=True, user=request.user)
        user_phrase_strength = phrase_strength_set.earliest('updated_at')
        phrase = Phrase.objects.get(id=user_phrase_strength.phrase_id)
        module = Module.objects.get(name=phrase.module)
        translations = phrase.phrase_translations.all()

        if not form.is_valid():
            context = {
                'profile': profile,
                'form': form,
                'user_phrase_strength': user_phrase_strength, # Phrase strength object
                'phrase': phrase,
            }
            return render(request, self.template_name, context)

        # Clean user's answer and escape any html entities before testing
        user_answer = html.escape(form.cleaned_data['answer'].strip())
        
        # Increment user view of current phrase
        user_phrase_strength.views += 1

        # Set variables to evaluate score and prepare feedback.
        response_score = UNASSESSED_SCORE
        errors = MAX_ERRORS
        matched_translation = ""
        feedback_html = ""
        cleaned_answer = unidecode(user_answer.lower())

        # Find a translation that best matches the user's answer and evaluate score and errors
        for translation in translations:
            cleaned_test_phrase = unidecode(translation.translation.lower())
            translation_score, error_count = eval_tranlation(cleaned_answer, cleaned_test_phrase)
            if translation_score > response_score:
                response_score = translation_score
                errors = error_count
                matched_translation = cleaned_test_phrase
        if not matched_translation:
            matched_translation =  translations[0].translation
        
        # Generate feedback to display to user
        feedback_html = feedback(user_answer, matched_translation, errors, response_score)

        # If evaluation passes mark, add points to user profile and raise user phrase strength
        translation_length = len(
            matched_translation.replace(" ", "").translate(str.maketrans("", "", string.punctuation))
        )
        if ((translation_length < 10) and (response_score >= 85)) or response_score >= 90:
            user_phrase_strength.correct += 1
            profile.xp += 5
            profile.save()
            response_accuracy = True
        else:
            response_accuracy = False
        user_phrase_strength.strength = ((
            user_phrase_strength.views - (user_phrase_strength.views - user_phrase_strength.correct)) 
            * 100) / user_phrase_strength.views
        user_phrase_strength.save()

        # Prepare data for feedback view
        success_url = reverse_lazy('tommy:feedback')
        request.session['phrase'] = user_phrase_strength.phrase.phrase
        request.session['module_id'] = module.id
        request.session['user_answer'] = user_answer # Used as backup in csae of error with HTML
        request.session['response_accuracy'] = response_accuracy
        request.session['testing_view'] = 'tommy:review'
        request.session['phrase_language'] = phrase.language
        request.session['feedback_html'] = feedback_html
        return redirect(success_url)


class AccentView(LoginRequiredMixin, View):
    """
    Difficult test form. Prompts user to translate phrases one at a time. Selects
    phrase randomly. Tests accent and punctuation.
    """
    template_name = 'tommy/accent.html'

    def get(self, request):
        # Set or reset the exercise session test count. End exerice after count 15.
        try:
            test_count = request.session.get('test_count')
            if test_count >= 12:
                request.session['test_count'] = 0
                finished_exercise_url = reverse_lazy('tommy:home')
                return redirect(finished_exercise_url)
        except:
            request.session['test_count'] = 0
        # Delete session data for previous testing phrase if it exists
        if request.session.get('phrase'):
            try:
                del request.session['phrase']
                del request.session['user_phrase_strength_id']
                del request.session['user_answer']
                del request.session['response_accuracy']
                del request.session['phrase_language']
                del request.session['feedback_html']
            except:
                pass

        profile = Profile.objects.get(user=request.user)
        form = TestForm()

        # Select random unlearned phrase for testing and get its translationstry:
        try: 
            phrase_strength_set = UserPhraseStrength.objects.filter(learned=True, user=request.user)
            user_phrase_strength = choice(phrase_strength_set)
            phrase = Phrase.objects.get(id=user_phrase_strength.phrase_id)

            # Save phrase data to session to be access in POST
            request.session['user_phrase_strength_id'] = user_phrase_strength.id

            context = {
                'profile': profile,
                'form': form,
                'user_phrase_strength': user_phrase_strength, # Phrase strength object
                'phrase': phrase,
            }
            # Increment test count for each phrase test before passing to session
            request.session['test_count'] += 1
            

            return render(request, self.template_name, context)
        except:
            start_learning_url = reverse_lazy('tommy:modules')
            return redirect(start_learning_url)
    
    def post(self, request):
        profile = Profile.objects.get(user=request.user)
        form = TestForm(request.POST)
        user_phrase_strength = UserPhraseStrength.objects.get(
                    id=request.session.get('user_phrase_strength_id')
                )
        phrase = Phrase.objects.get(id=user_phrase_strength.phrase_id)
        module = Module.objects.get(name=phrase.module)
        translations = phrase.phrase_translations.all()

        if not form.is_valid():
            context = {
                'profile': profile,
                'form': form,
                'user_phrase_strength': user_phrase_strength, # Phrase strength object
                'phrase': phrase,
            }
            return render(request, self.template_name, context)

        # Clean user's answer and escape any html entities before testing
        user_answer = html.escape(form.cleaned_data['answer'].strip())

        # Increment user view of current phrase
        user_phrase_strength.views += 1

        # Set variable to help choose best translation for feedback
        highest_score = UNASSESSED_SCORE
        
        # Find a translation that exactly matches the user's answer. If yes, add points. Generate feedback.
        for translation in translations:
            test_user_ans = user_answer.translate(str.maketrans("", "", string.punctuation))
            test_translation = translation.translation.translate(str.maketrans("", "", string.punctuation))
            response_score, error_count = eval_tranlation(test_user_ans.lower(), test_translation.lower())
            if test_user_ans == test_translation:
                user_phrase_strength.correct += 1
                profile.xp += 5
                profile.save()
                response_accuracy = True
                feedback_html = accent_feedback(
                    user_answer, translation.translation, error_count, response_score
                )
                break
            elif response_score > highest_score:
                feedback_html = accent_feedback(
                    user_answer, translation.translation, error_count, response_score
                )
                response_accuracy = False
        
        # Update the user phrase strength score.
        user_phrase_strength.strength = ((
            user_phrase_strength.views - (user_phrase_strength.views - user_phrase_strength.correct))
                * 100) / user_phrase_strength.views
        user_phrase_strength.save()

        # Prepare data for feedback view
        success_url = reverse_lazy('tommy:feedback')
        request.session['phrase'] = user_phrase_strength.phrase.phrase
        request.session['user_answer'] = user_answer  # Used as backup in csae of error with HTML
        request.session['response_accuracy'] = response_accuracy
        request.session['module_id'] = module.id
        request.session['testing_view'] = 'tommy:accent'
        request.session['phrase_language'] = phrase.language
        request.session['feedback_html'] = feedback_html
        return redirect(success_url)


class FeedbackView(LoginRequiredMixin, View):
    """Displays feedback on user translation accuracy and points earned."""

    template_name = 'tommy/feedback.html'

    def get(self, request):
        profile = Profile.objects.get(user=request.user)
        phrase_str = request.session.get('phrase')
        module = Module.objects.get(id=request.session.get('module_id'))
        phrase = Phrase.objects.get(
            phrase=phrase_str,
            language=request.session.get('phrase_language'),
            module=module
        )
        
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

        # Feedback phrases
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
            'user_answer': user_answer, # Used as backup in csae of error with HTML
            'response_accuracy': response_accuracy,
            'phrase': phrase,
            'translations': translations,
            'testing_view': testing_view,
            'result': result,
            'module_id': module_id,
            'feedback_html': feedback_html,
            'module_progress': module_progress,
            'module_name': module.name
        }
        # Retrieve and pass on test count for the current exercise session
        return render(request, self.template_name, context)