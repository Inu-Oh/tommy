from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
# from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import TemplateView, UpdateView, View, CreateView, ListView

from datetime import datetime
from random import choice
from unidecode import unidecode
import string

from .models import Module, Phrase, Translation, Profile, UserPhraseStrength
from .forms import ProfileForm, TestForm #, PhraseStrengthForm


# Grade user answer TODO delete after replaced
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


# Evaluates a single word to support the eval_phrase() funciton
def eval_word(ans_word, phr_word):
    print("using eval_word() func")
    correct_count, error_count, ans_length, phr_length = 0, 0, len(ans_word), len(phr_word)
    length = (phr_length, 'phr') if phr_length <= ans_length else (ans_length, 'ans')
    for i in range(length[0]):
        if phr_word[i] == ans_word[i]:
            correct_count += 1
        else:
            error_count += 1
    length_difference = abs(ans_length - phr_length)
    error_count += length_difference
    accuracy = ( correct_count / ( length[0] + length_difference ) ) * 100
    return accuracy, error_count

"""# Evaluaes a single word to support the eval_phrase() funciton
def eval_word(ans_word, phr_word):
    right, wrong, dict_i, correct_count = {}, {}, 0, 0
    length = len(phr_word) if len(phr_word) >= len(ans_word) else len(ans_word)
    for i in range(length):
        if len(ans_word) >= i:
            if phr_word[i] == ans_word[i]:
                right[dict_i] = ans_word[i]
                correct_count += 1
                dict_i += 1
            else:
                wrong[dict_i] = ans_word[i]
                dict_i += 1
    accuracy = (correct_count / len(phr_word)) * 100
    success = True if 0 in right.keys() else False
    html = f'<span class="text-success">{right[0]}' if success else f'<span class="text-warning">{wrong[0]}'
    for i in range(1, dict_i-1):
        if success:
            if i in right.keys():
                html += right[i]
            else:
                html += f'</span><span class="text-warning">{wrong[i]}'
        else:
            if i in wrong.keys():
                html += wrong[i]
            else:
                html += f'</span><span class="text-success">{right[i]}'
    html += '</span>'
    return accuracy, html"""


# Grades the user answer by comparing it to translation phrase
def eval_phrase(answer, phrase):
    print("\nIn eval func:\nAnswer:", answer, "\nphrase:", phrase)
    answer_str = answer.lower().translate(str.maketrans("", "", string.punctuation))
    phrase_str = phrase.lower().translate(str.maketrans("", "", string.punctuation))
    print("answer_str:", answer_str, "\nphrase_str", phrase_str)
    answer_str, phrase_str = answer_str.replace(" ", ""), phrase_str.replace(" ", "")
    print("answer_str:", answer_str, "\nphrase_str", phrase_str)
    phrase_words, answer_words = phrase.split(), answer.split()
    print("phrase_words", phrase_words, "\nanswer_words", answer_words)
    phrase_length, answer_length = len(phrase_words), len(answer_words)
    error_count, total_score = 0, 0

    # Case: Exact same string gets full mark
    if answer_str == phrase_str:
        return 100, error_count
    
    # One word phrase is evaluated for spelling errors and additional words
    elif phrase_length == 1:
        if answer_length == 1:
            return eval_word(answer, phrase)
        else:
            print("one word in phrase but more in answer")
            factor = 1.7 / answer_length
            for word in answer_words:
                if phrase_length >= answer_length:
                    word_accuracy, word_errors = eval_word(word, phrase)
                    error_count = word_errors + ( len(answer_str) - ( len(phrase_str) - len(word) ) )
                    return word_accuracy * factor, error_count
                else:
                    return -1, len(answer_str)

    # Multiple word phrase evaluates accuracy of phrases separately
    else:
        print("multiple words in phrases")
        # If the number of words is the same compare the words
        if answer_length == phrase_length:
            print("same number of words in phrase and answer")
            for i in range(phrase_length):
                if answer_words[i] == phrase_words[i]:
                    total_score += 100
                else:
                    word_score, word_errors = eval_word(answer_words[i], phrase_words[i])
                    total_score += word_score
                    error_count += word_errors
            return (total_score / phrase_length), error_count
        # Otherwise search for the words in the full string
        else:
            print("different number of words in phrase and answer")
            if phrase_str in answer_str:
                print("phrase in answer string")
                accuracy = (len(phrase_str) - abs(len(phrase_str) - len(answer_str)) ) / len(phrase_str) * 100
                print("phrase in answer accuracy", accuracy)
                error_count += abs(len(phrase_str) - len(answer_str))
                return accuracy, error_count
            else:
                print("phrase string not found in answer string")
                factor = ((phrase_length - abs(answer_length - phrase_length)) / phrase_length)
                correct_words = 0
                for word in phrase_words:
                    if word in answer_words:
                        correct_words += 1
                    else:
                        error_count += len(word)
                for word in answer_words:
                    if word not in phrase_words:
                        error_count += len(word)
                accuracy = (correct_words / phrase_length) * factor * 100
                return accuracy, error_count


"""# Function grades the user answer and provides feedback HTML
def eval_phrase(answer, phrase):
    # TODO check that string input is valid else raise error to escape or refresh window

    
    answer_str = answer.lower().translate(str.maketrans("", "", string.punctuation))
    phrase_str = phrase.lower().translate(str.maketrans("", "", string.punctuation))
    phrase_words, answer_words = phrase.split(), answer.split()
    phrase_length, answer_length = len(phrase_words), len(answer_words)

    # Case: Exact same string gets full mark
    if answer_str == phrase_str:
        return 100, f'<span class="text-success">{answer}</span>'
    
    # One word phrase is evaluated for spelling errors and additional words
    elif phrase_length == 1:
        if answer_length == 1:
            return eval_word(answer, phrase)
        else:
            factor = 1.7 / answer_length
            for word in answer_words:
                if phrase_length >= answer_length:
                    accuracy, html = eval_word(word, phrase)
                    return accuracy * factor, html

    # Multiple word phrase evaluates accuracy of phrases separately
    else:
        total_score, html = 0, ""
        if answer_length == phrase_length:
            for i in range(phrase_length):
                if answer_words[i] == phrase_words[i]:
                    total_score += 100
                else:
                    word_score, word_html = eval_word(answer_words[i], phrase_words[i])
                    total_score += word_score
                    html += word_html
            return total_score / phrase_length, html
        else:
            if phrase_str in answer_str:
                accuracy = (len(phrase_str) - abs(len(phrase_str) - len(answer_str))) / len(phrase_str)
                if accuracy >= 0.85:
                    # TODO Figure out how to compare phrase and answer to add the wrong text
                    return accuracy, f'<span class="text-success">{answer}</span>'
                else:
                    return accuracy, f'<span class="text-warning">{answer}</span>'
            else:
                factor = (phrase_length - abs(answer_length - phrase_length)) / phrase_length
                correct_words = 0
                for word in phrase_words:
                    if word in answer_words:
                        correct_words += 1
                accuracy = (correct_words / phrase_length) * factor
                if accuracy >= 0.85:
                    # TODO Figure out how to compare phrase and answer to add the wrong text
                    return accuracy, f'<span class="text-success">{answer}</span>'
                else:
                    return accuracy, f'<span class="text-warning">{answer}</span>'"""
                

# TODO  DELETE after replace function testing complete
def eval_answer(answer, phrase):
    answer_words = answer.split()
    phrase_words = phrase.split()
    word_count = len(phrase_words) if len(phrase_words) <= len(answer_words) else len(answer_words)
    word_accuracy = 0
    for i in range(word_count):
        if answer_words[i] == phrase_words[i]:
            word_accuracy += 100
        else:
            ans_word_len, word_length = len(answer_words[i]), len(phrase_words[i])
            correct_chars = 0
            index = ans_word_len if ans_word_len <= word_length else word_length
            for j in range(index):
                if answer_words[i][j] == phrase_words[i][j]:
                    correct_chars += 1
            if (abs(ans_word_len - word_length)/word_length) > 0.2:
                correct_chars /= 2
            word_accuracy += (correct_chars / word_length) * 100
    factor = abs( len(phrase_words) - len(answer_words) ) / len(phrase_words)
    avg_accuracy = (word_accuracy / word_count) * (1 - factor)
    return avg_accuracy


def feedback(answer, phrase, errors):
    answer_str = answer.lower().translate(str.maketrans("", "", string.punctuation))
    phrase_str = phrase.lower().translate(str.maketrans("", "", string.punctuation))
    answer_words, phrase_words = answer.split(), unidecode(phrase_str).split()
    answer_str, phrase_str = answer_str.replace(" ", ""), phrase_str.replace(" ", "")
    answer_length, phrase_length = len(answer_words), len(phrase_words)
    html = '<span class="text-success">'
    if not errors:
        return f'<span class="text-success">{answer}</span>'
    elif errors > 3:
        return f'<span class="text-danger">{answer}</span>'
    elif errors == 1 and len(answer) == len(phrase):
        for i in range(len(answer)):
            if unidecode(answer[i].lower()) != unidecode(phrase[i].lower()):
                html += f'<span class="text-danger">{answer[i]}</span>'
            else:
                html += answer[i]
    else:
        if answer_length >= phrase_length:
            for word in answer_words:
                if unidecode(word.lower().translate(str.maketrans("", "", string.punctuation))) not in phrase_words:
                    html += f'<span class="text-danger">{word}</span> '
                else:
                    html += f'{word} '
        else:
            for word in phrase_words:
                for i in range(phrase_length):
                    if word != unidecode(answer_words[i].translate(str.maketrans("", "", string.punctuation))):
                        html += f'<span class="text-danger">{answer_words[i]}</span> '
                    else:
                        html += f'{answer_words[i]} '
    return html + '\b</span>'



# Generates HTML feedback for user test answer TODO replace and delete afterwards
def phrase_feedback(answer, phrase, accuracy):
    length = (len(answer), "longer answre") if len(answer) >= len(phrase) else (len(phrase), "longer phrase")
    right, wrong, dict_index = {}, {}, 0
    char_list = [char for char in answer if char not in " .?',!"]
    answer_words, phrase_words = answer.split(), phrase.split()
    index = len(answer_words) if len(answer_words) <= len(phrase_words) else len(phrase_words)
    for i in range(index):
        if len(phrase_words[i]) >= len(answer_words[i]):
            (longer, shorter, longer_word) = (len(phrase_words[i]), len(answer_words[i]), phrase_words[i]) 
        else:
            (longer, shorter, longer_word) = (len(answer_words[i]), len(phrase_words[i]), answer_words[i])
        for j in range(shorter):
            if answer_words[i][j] in ".?',!" or answer_words[i][j].lower() == phrase_words[i][j].lower():
                right[dict_index] = answer_words[i][j]
            else:
                wrong[dict_index] = answer_words[i][j]
            dict_index += 1
        for k in range(shorter, longer):
            wrong[dict_index] = longer_word[k]
        right[dict_index] = " "
        dict_index += 1
    right_chars, wrong_chars = [i for i, _ in right.items()], [i for i, _ in wrong.items()]
    html_string, invalid = '', "><][}{)(;"
    if accuracy > 50:
        for i in range(dict_index-1):
            if i in right_chars:
                html_string += f'<span class="text-success">{right[i]}</span>'
            elif i in wrong_chars:
                html_string += f'<span class="text-danger">{wrong[i]}</span>'
    elif any(char in answer for char in invalid):
        html_string = '<span class="text-danger">Invalid input, ><)(}{][;, can\'t show your answer.</span>'
    else:
        html_string = f'<span class="text-danger">{answer}</span>'
    return html_string


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
        user_phrase_strength = UserPhraseStrength.objects.filter(user=request.user)
        if user_phrase_strength.count() > 0:
            unlearned_phrase_count = user_phrase_strength.filter(learned=False).count()
            learned_phrase_count = user_phrase_strength.filter(learned=True).count()
        else:
            unlearned_phrase_count, learned_phrase_count = 1, 0
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
        learned_phrases = UserPhraseStrength.objects.filter(learned=True, user=request.user)

        # Recalculate phrase strength based on last time seen
        for phrase in learned_phrases:
            now = datetime.now()
            day_of_last_reset = datetime(
                day=phrase.updated_at.day,
                month=phrase.updated_at.month,
                year=phrase.updated_at.year,
                hour=phrase.updated_at.hour,
                minute=phrase.updated_at.minute)
            delta = now - day_of_last_reset
            days_since_reset = delta.days
            
            """# Function data for review in server log
            test_log = f"\nDays since reset for phrase \"{str(phrase.phrase)}\""
            test_log += f": {days_since_reset}\n  Now                : {now}"
            test_log += f"\n  Time of last reset : {day_of_last_reset}\n"
            test_log += f"    strength before recalc : {str(phrase.strength)}"
            print(test_log)"""

            # Weaken strength if phrase wasn't tested for longer than a day
            if days_since_reset > 0 and phrase.strength > 25:
                phrase.strength -= days_since_reset
                phrase.save()
            
            """# Function data for review in server log - part 2
            print(f"    strength after recalc  : {str(phrase.strength)}")"""
            
        success_url = 'tommy:home'
        return redirect(success_url)


# Adds a user name for the GUI and creates user testing objects for all course phrases
class ProfileCreateView(LoginRequiredMixin, CreateView):
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

        # Create list of dicts for faster data access and search
        phrase_data, total_strength, total_learned, strength_count = [], 0, 0, 0
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
        strength_data['average'] = round(strength_data['total'] / strength_data['learned'])

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
        try: # Select unlearned phrase for testing and its translations
            phrases = Phrase.objects.filter(module=module)
            unlearned_phrases = UserPhraseStrength.objects.filter(
                learned=False,
                user=request.user,
                phrase__in=phrases
            )
            testing_phrase = unlearned_phrases.first()
            translations = Translation.objects.filter(phrase=testing_phrase.phrase)
            translation_langauge = translations[0].language
            phrase_language = "French" if translation_langauge == "English" else "English"
            phrase = phrases.get(phrase=testing_phrase.phrase, language=phrase_language)
            context = {
                'profile': profile,
                'form': form,
                'phrase': phrase,
                'testing_phrase': testing_phrase, # Phrase strength object
            }
            return render(request, self.template_name, context)
        except: # If no unlearned phrase is found, redirect to home page
            finished_learning_url = reverse_lazy('tommy:home')
            return redirect(finished_learning_url)
    
    def post(self, request, pk):
        profile = Profile.objects.get(user=request.user)
        form = TestForm(request.POST)
        
        # Get an unlearned phrase for testing and its translations
        module = Module.objects.get(id=pk)
        phrases = Phrase.objects.filter(module=module)
        unlearned_phrases = UserPhraseStrength.objects.filter(
            learned=False,
            user=request.user,
            phrase__in=phrases
        )
        testing_phrase = unlearned_phrases.first()
        translations = Translation.objects.filter(phrase=testing_phrase.phrase)
        if not form.is_valid():
            context = {
                'profile': profile,
                'form': form,
                'phrase': phrase,
                'testing_phrase': testing_phrase, # Phrase strength object
            }
            # TODO Add error message if form is not valid ?
            return render(request, self.template_name, context)
        translation_langauge = translations[0].language
        phrase_language = "French" if translation_langauge == "English" else "English"
        phrase = Phrase.objects.get(phrase=testing_phrase.phrase, language=phrase_language)

        # Prepare user's answer and don't grade accent before testing
        user_answer = form.cleaned_data['answer'].strip()

        # Set phrase to learned. Calculate and set user phrase strength data. Generate feedback.
        testing_phrase.learned = True
        testing_phrase.views = 1
        response_accuracy = False
        response_score = -1
        feedback_html = ""
        cleaned_answer = unidecode(user_answer.lower())
        print("\nUser answer:", user_answer, "Cleanded:", cleaned_answer)
        for translation in translations:
            cleaned_test_phrase = unidecode(translation.translation.lower())
            print("Phrase:", translation.translation, "Cleaned:", cleaned_test_phrase)
            translation_score, error_count = eval_phrase(cleaned_answer, cleaned_test_phrase)
            print("\nAnswer:", user_answer, "\nPhrase:", translation.translation, "\nErrors:", error_count, "Score:", translation_score)
            if translation_score > response_score:
                response_score = translation_score
                # TODO replace phrase feedback to add error count for better feedback string
                feedback_html = feedback(user_answer, translation.translation, error_count)
        print("\nFinal test data:\nAnswer:", user_answer, "\nPhrase:", translation.translation, "\nErrors:", error_count, "Score:", translation_score)
        # print(feedback_html)
        translation_length = len(cleaned_test_phrase.replace(" ", "").translate(str.maketrans("", "", string.punctuation)))
        print("Translation length:", translation_length)
        if ((translation_length < 10) and (response_score >= 85)) or response_score > 90:
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
        translation_language = "English" if phrase.language == "French" else "French"
        translations = Translation.objects.filter(phrase=phrase, language=translation_language)

        context = {
            'profile': profile,
            'form': form,
            'testing_phrase': testing_phrase, # Phrase strength object
            'phrase': phrase,
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
                break
        testing_phrase.strength = ((testing_phrase.views - (testing_phrase.views - testing_phrase.correct)) * 100) / testing_phrase.views
        testing_phrase.save()

        # Prepare data for feedback view
        success_url = reverse_lazy('tommy:feedback')
        request.session['testing_phrase'] = testing_phrase.phrase.phrase
        request.session['user_answer'] = form.cleaned_data['answer'].strip()
        request.session['respone_accuracy'] = respone_accuracy
        request.session['testing_view'] = 'tommy:practice'
        request.session['phrase_language'] = phrase.language
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
        translation_language = "English" if phrase.language == "French" else "French"
        translations = Translation.objects.filter(phrase=phrase, language=translation_language)

        context = {
            'profile': profile,
            'form': form,
            'testing_phrase': testing_phrase, # Phrase strength object
            'phrase': phrase,
        }
        if not form.is_valid():
            return render(request, self.template_name, context)

        # Prepare user's answer before testing and don't grade accent
        user_answer = unidecode(form.cleaned_data['answer'].strip())

        # Calculate and set user phrase strength data
        testing_phrase.views += 1
        response_accuracy = False
        for translation in translations:
            cleaned_answer = unidecode(user_answer.lower())
            cleaned_test_phrase = unidecode(translation.translation.lower())
            if grade_answer(cleaned_answer, cleaned_test_phrase):
                testing_phrase.correct += 1
                # Add XP points to user profile
                profile.xp += 5
                profile.save()
                response_accuracy = True
                break
        testing_phrase.strength = ((testing_phrase.views - (testing_phrase.views - testing_phrase.correct)) * 100) / testing_phrase.views
        testing_phrase.save()

        # Prepare data for feedback view
        success_url = reverse_lazy('tommy:feedback')
        request.session['testing_phrase'] = testing_phrase.phrase.phrase
        request.session['user_answer'] = form.cleaned_data['answer'].strip()
        request.session['response_accuracy'] = response_accuracy
        request.session['testing_view'] = 'tommy:review'
        request.session['phrase_language'] = phrase.language
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
        translation_language = "English" if phrase.language == "French" else "French"
        translations = Translation.objects.filter(phrase=phrase, language=translation_language)

        context = {
            'profile': profile,
            'form': form,
            'testing_phrase': testing_phrase, # Phrase strength object
            'phrase': phrase,
        }
        if not form.is_valid():
            return render(request, self.template_name, context)

        # Clean up data for user's answer before testing and don't test for correct accent
        user_answer = form.cleaned_data['answer'].strip()

        # Calculate and set user phrase strength data
        testing_phrase.views += 1
        response_accuracy = False
        for translation in translations:
            if user_answer.lower() == translation.translation.lower():
                testing_phrase.correct += 1
                # Add XP points to user profile
                profile.xp += 5
                profile.save()
                response_accuracy = True
                break
        testing_phrase.strength = ((testing_phrase.views - (testing_phrase.views - testing_phrase.correct)) * 100) / testing_phrase.views
        testing_phrase.save()

        # Prepare data for feedback view
        success_url = reverse_lazy('tommy:feedback')
        request.session['testing_phrase'] = testing_phrase.phrase.phrase
        request.session['user_answer'] = user_answer
        request.session['response_accuracy'] = response_accuracy
        request.session['testing_view'] = 'tommy:accent'
        request.session['phrase_language'] = phrase.language
        return redirect(success_url)


# Feedback page for test results
class FeedbackView(LoginRequiredMixin, View):
    template_name = 'tommy/feedback.html'

    def get(self, request):
        profile = Profile.objects.get(user=request.user)
        testing_phrase = request.session.get('testing_phrase')
        phrase = Phrase.objects.get(
            phrase=testing_phrase,
            language=request.session.get('phrase_language')
        )
        testing_phrase = UserPhraseStrength.objects.get(phrase=phrase, user=request.user)
        user_answer = request.session.get('user_answer') # remove ?
        response_accuracy = request.session.get('response_accuracy')
        translations = Translation.objects.filter(phrase=phrase)
        testing_view = request.session.get('testing_view')
        feedback_html = request.session.get('feedback_html')

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
            'feedback_html': feedback_html
        }
        # Retrieve and pass on test count for the current exercise session
        return render(request, self.template_name, context)