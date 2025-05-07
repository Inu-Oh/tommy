from csv import reader, writer
from json import loads
from re import match

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import UpdateView, CreateView, ListView, View

from tommy.models import Module, Phrase, Translation, Profile, UserPhraseStrength
from tommy.forms import PhraseStrengthForm

from .forms import ModuleForm, CreatePhraseForm, CreateTranslationForm, UpdatePhraseForm, UpdateTranslationForm, CsvTestForm, CsvSubmitForm
    

# Menu for admins to navigate adding and editing content
# Reserve deleting content for superusers in django admin section
class StaffMenuView(LoginRequiredMixin, ListView):
    template_name = 'staff/manage_content.html'
    
    def get(self, request):
        if not request.user.is_staff:
            non_staff_url = 'tommy:home'
            return redirect(non_staff_url)
        
        profile = Profile.objects.get(user=request.user)
        modules = Module.objects.all().order_by('name')
        phrases = Phrase.objects.all().order_by('phrase')
        translations = Translation.objects.all().order_by('translation')

        context = {
            'profile': profile,
            'modules': modules,
            'phrases': phrases,
            'translations': translations,
        }
        
        return render(request, self.template_name, context)


# Views for adding new content: modules, phrases and translations
class CreateModuleView(PermissionRequiredMixin, CreateView):
    permission_required = 'tommy.add_module'
    template_name = 'staff/add_module.html'
    
    def get(self, request):
        if not request.user.is_staff:
            non_staff_url = 'tommy:home'
            return redirect(non_staff_url)
        
        form = ModuleForm()
        context = {'form': form}
        return render(request, self.template_name, context)

    def post(self, request):
        if not request.user.is_staff:
            non_staff_url = 'tommy:home'
            return redirect(non_staff_url)
        
        form = ModuleForm(request.POST)

        if not form.is_valid():
            context = {'form': form}
            return render(request, self.template_name, context)
        
        # Save new module and redirect to add phrases to this module
        module = form.save()
        success_url = reverse_lazy('staff:add_phrase', kwargs={'pk': module.id})
        return redirect(success_url)


class CreatePhraseView(PermissionRequiredMixin, CreateView):
    permission_required = 'tommy.add_phrase'
    template_name = 'staff/add_phrase.html'
    
    def get(self, request, pk):
        if not request.user.is_staff:
            non_staff_url = 'tommy:home'
            return redirect(non_staff_url)

        module = Module.objects.get(id=pk)
        phrases = Phrase.objects.filter(module=module)
        form = CreatePhraseForm()
        context = {'form': form, 'module': module, 'phrases': phrases}
        return render(request, self.template_name, context)

    def post(self, request, pk):
        if not request.user.is_staff:
            non_staff_url = 'tommy:home'
            return redirect(non_staff_url)
        
        form = CreatePhraseForm(request.POST)
        module = Module.objects.get(id=pk)

        if not form.is_valid():
            context = {'form': form, 'module': module}
            return render(request, self.template_name, context)
        
        # Save new phrase after setting its module
        phrase = form.save(commit=False)
        phrase.module = module
        phrase.save()

        # Create a phrase strength object for the new phrase for every user 
        User = get_user_model()
        users = User.objects.all()
        for user in users:
            phrase_strength_form = PhraseStrengthForm()
            phrase_strength = phrase_strength_form.save(commit=False)
            phrase_strength.phrase = phrase
            phrase_strength.user = user
            phrase_strength.learned = False
            phrase_strength.strength = 0
            phrase_strength.views = 0
            phrase_strength.correct = 0
            phrase_strength.save()
            
        success_url = reverse_lazy('staff:add_phrase', kwargs={'pk': pk})
        return redirect(success_url)


class CreateTranslationView(PermissionRequiredMixin, CreateView):
    permission_required = 'tommy.add_translation'
    template_name = 'staff/add_translation.html'
    
    def get(self, request, pk1, pk2):
        if not request.user.is_staff:
            non_staff_url = 'tommy:home'
            return redirect(non_staff_url)
        
        module = Module.objects.get(id=pk1)
        phrase_set = Phrase.objects.filter(module=module)
        current_phrase = Phrase.objects.get(id=pk2)
        translations = Translation.objects.filter(phrase=current_phrase)
        form = CreateTranslationForm()
        context = {
            'form': form,
            'module': module,
            'current_phrase': current_phrase,
            'phrase_set': phrase_set,
            'translations': translations
        }
        return render(request, self.template_name, context)
    
    def post(self, request, pk1, pk2):
        if not request.user.is_staff:
            non_staff_url = 'tommy:home'
            return redirect(non_staff_url)
        
        form = CreateTranslationForm(request.POST)
        phrase = Phrase.objects.get(id=pk2)

        if not form.is_valid():
            module = Module.objects.get(id=pk1)
            phrase_set = Phrase.objects.filter(module=module)
            translations = Translation.objects.filter(phrase=phrase)
            
            context = {
                'form': form,
                'module': module,
                'current_phrase': phrase,
                'phrase_set': phrase_set,
                'translations': translations
            }
            return render(request, self.template_name, context)

        translation = form.save(commit=False)
        translation.phrase = phrase
        translation.save()

        success_url = reverse_lazy(
            'staff:add_translation', kwargs={'pk1': pk1, 'pk2': pk2}
        )
        return redirect(success_url)


# Views for editing modules, phrases and translations
class UpdateModuleView(PermissionRequiredMixin, UpdateView):
    permission_required = 'tommy.change_module'
    template_name = 'staff/edit_module.html'
    
    def get(self, request, pk):
        if not request.user.is_staff:
            non_staff_url = 'tommy:home'
            return redirect(non_staff_url)
        
        module = Module.objects.get(id=pk)
        form = ModuleForm(instance=module)
        context = {'module': module, 'form': form}
        return render(request, self.template_name, context)
    
    def post(self, request, pk):
        if not request.user.is_staff:
            non_staff_url = 'tommy:home'
            return redirect(non_staff_url)
        
        module = get_object_or_404(Module, id=pk)
        form = ModuleForm(request.POST, instance=module)

        if not form.is_valid():
            context = {'module': module, 'form': form}
            return render(request, self.template_name, context)

        form.save()
        success_url = reverse_lazy('staff:manage_content')
        return redirect(success_url)


class UpdatePhraseView(PermissionRequiredMixin, UpdateView):
    permission_required = 'tommy.change_phrase'
    template_name = 'staff/edit_phrase.html'
    
    def get(self, request, pk):
        if not request.user.is_staff:
            non_staff_url = 'tommy:home'
            return redirect(non_staff_url)
        
        phrase = Phrase.objects.get(id=pk)
        form = UpdatePhraseForm(instance=phrase)
        module = Module.objects.get(name=phrase.module)
        context = {'form': form, 'module': module, 'phrase': phrase}
        return render(request, self.template_name, context)
    
    def post(self, request, pk):
        if not request.user.is_staff:
            non_staff_url = 'tommy:home'
            return redirect(non_staff_url)
        
        phrase = get_object_or_404(Phrase, id=pk)
        form = UpdatePhraseForm(request.POST, instance=phrase)

        if not form.is_valid():
            module = Module.objects.get(name=phrase.module)
            context = {'form': form, 'module': module, 'phrase': phrase}
            return render(request, self.template_name, context)

        form.save()
        success_url = reverse_lazy('staff:manage_content')
        return redirect(success_url)


class UpdateTranslationView(PermissionRequiredMixin, UpdateView):
    permission_required = 'tommy.change_translation'
    template_name = 'staff/edit_translation.html'
    
    def get(self, request, pk):
        if not request.user.is_staff:
            non_staff_url = 'tommy:home'
            return redirect(non_staff_url)
    
        translation = Translation.objects.get(id=pk)
        form = UpdateTranslationForm(instance=translation)
        phrase = Phrase.objects.get(phrase=translation.phrase)
        module = Module.objects.get(name=phrase.module)
        context = {
            'form': form,
            'module': module,
            'phrase': phrase,
            'translation': translation
        }
        return render(request, self.template_name, context)

    def post(self, request, pk):
        if not request.user.is_staff:
            non_staff_url = 'tommy:home'
            return redirect(non_staff_url)
        
        translation = get_object_or_404(Translation, id=pk)
        form = UpdateTranslationForm(request.POST, instance=translation)
        if not form.is_valid():
            phrase = Phrase.objects.get(phrase=translation.phrase)
            module = Module.objects.get(name=phrase.module)
            context = {
                'form': form,
                'module': module,
                'phrase': phrase,
                'translation': translation
            }
            return render(request, self.template_name, context)

        form.save()
        success_url = reverse_lazy('staff:manage_content')
        return redirect(success_url)


# Views for mass database update of modules, phrases and translations
class CsvToDbTestView(PermissionRequiredMixin, View):
    permission_required = [
        'tommy.add_module',
        'tommy.add_phrase',
        'tommy.add_translation',
        'tommy.change_module',
        'tommy.change_phrase',
        'tommy.change_translation',
    ]
    template_name = 'staff/csv_db_test.html'

    def get(self, request):
        if not request.user.is_superuser:
            non_staff_url = 'tommy:home'
            return redirect(non_staff_url)
        profile = Profile.objects.get(user=request.user)
        test_form = CsvTestForm()

        context = {
            'profile': profile,
            'test_form': test_form,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        if not request.user.is_superuser:
            non_staff_url = 'tommy:home'
            return redirect(non_staff_url)
        profile = Profile.objects.get(user=request.user)
        test_form = CsvTestForm(request.POST)
        if not test_form.is_valid():
            context = {
                'profile': profile,
                'test_form': test_form,
            }
            return render(request, self.template_name, context)

        # Try to create from CSV file a list of dictionaries to verify SQL data
        data_list = []
        message = "" # for building error messages throughout the various checks below.
        try:
            with open('data.csv') as csvfile:
                data_reader = reader(csvfile)
                next(data_reader)
                row_count = 1
                for row in data_reader:
                    row_count += 1
                    dict_obj = {
                        'phrase_id': row[0],
                        'module_name': row[1],
                        'phrase': row[2],
                        'phrase_lang': row[3],
                        'translations': loads(row[4])
                    }
                    data_list.append(dict_obj)
        # If an error occurs give feedback
        except Exception as e:
            message += f"There was an error reading the file at row {row_count}. "
            message += "Correct this in the CSV before proceeding. "
            message += str(row)
            if hasattr(e, 'message'):
                e += e.message
            context = {
                'profile': profile,
                'test_form': test_form,
                'message': message,
                'details': e
            }
            return render(request, self.template_name, context)

        # Check that phrase id is entered correctly
        phrases = Phrase.objects.all()
        row = 1
        for item in data_list:
            row += 1
            if phrase_id := item["phrase_id"]:
                if not isinstance(phrase_id, int):
                    if not not_ints:
                        not_ints = "Phrase IDs at these rows should be an intager number: "
                    not_ints += f"{row}, "
                if not phrases.get(id=phrase_id):
                    if not wrong_ids:
                        wrong_ids = "Phrase IDs at the following rows don't exist in the database."
                        wrong_ids += "Delete if the it's a new phrase or "
                        worng_ids += "correct if the phrase is already in the database: "
                    wrong_ids += f"ID {phrase_id} at row {row}, "
        if not_ints or wrong_ids:
            message += "Errors with data entry for phrase ID column. " 
            if not_ints:
                message += not_ints + "\b\b. "
            if wrong_ids:
                message += wrong_ids+ "\b\b. "
            message += "Correct all phrase IDs before running the test again. "
            context = {
                'profile': profile,
                'test_form': test_form,
                'message': message,
            }
            return render(request, self.template_name, context)
        
        # Verify that module name is entered for each phrase
        row = 1
        for item in data_list:
            row += 1
            if not item["module_name"]:
                message += f"{row}, "
        if message:
            message += "Module names were not provided for phrases at rows: " + message
            message += "\b\b. Provide module names for each phrase."
            context = {
                'profile': profile,
                'test_form': test_form,
                'message': message,
            }
            return render(request, self.template_name, context)
        
        # Check that phrases ware entered and only contain alphabetic characters
        row = 1
        for item in data_list:
            row += 1
            if not item["phrase"]:
                if not missing_phrases:
                    missing_phrases = "Phrase cells are blank at the following rows: "
                missing_phrases += f"{row}, "
            elif not match('^[\w-]+$', item["phrase"]):
                if not non_alphas:
                    non_alphas = "Phrase at these rows include non-alpha characters: "
                non_alphas += f"{row}, "
        if missing_phrases or non_alphas:
            message += "Errors with data entry for phrase column. "
            if missing_phrases:
                message += missing_phrases + "\b\b. "
            if non_alphas:
                message += non_alphas + "\b\b. "
            message += "Add all missing phrases and replace non alphabetic characters."
            context = {
                'profile': profile,
                'test_form': test_form,
                'message': message,
            }
            return render(request, self.template_name, context)

        # Verify either English or French for language options
        row, lang_errors = 1, []
        for item in data_list:
            row += 1
            if item["phrase_lang"] not in ["French", "English"]:
                lang_errors.append(row)
        if lang_errors:
            message = """Phrase langauge was entered wrong in some rows. 
                Use either French or English, capatialized, to indicate the phrase language.
                Correct this in the CSV before proceeding. Affected rows: """
            for err in lang_errors:
                message += str(err) + ", "
            message += "\b\b."
            context = {
                'profile': profile,
                'test_form': test_form,
                'message': message,
            }
            return render(request, self.template_name, context)

        # Verify that all phrases have translation and include only alphabetic characters
        row = 1
        for item in data_list:
            row += 1
            if translations := item["translations"]:
                if type(translations) is not list:
                    if not non_lists:
                        non_lists += "Translations in the following rows are not formatted correctly. "
                        non_lists += "Enter all translations in double quotation marks in square brackets. "
                        non_lists += "Example: [\"Translation one\", \"Two and\", \"Three\"]. Correct rows: "
                    non_lists += f"{row}, "
                for translation in translations:
                    if not match('^[\w-]+$', translation):
                        if not non_alphas:
                            "Translations in the following rows include non-alphabetic characters: "
                        non_alphas += f"{row}, "
            else: # if list is empty
                if not missing_translations:
                    missing_translations = "Translations are missing for phrases in rows: "
                missing_translations += f"{row}, "
        if missing_translations or non_alphas or non_lists:
            message += "Errors with data entry for translation column. "
            if missing_translations:
                message += missing_translations
            if non_alphas:
                message += non_alphas
            if non_lists:
                message += non_lists
            message += "Correct all errors before proceeding with the test."
            context = {
                'profile': profile,
                'test_form': test_form,
                'message': message,
            }
            return render(request, self.template_name, context)

        # TODO add approval from test to save in session that will be used in update view

        # If successful redirect to submit page
        success_url = reverse_lazy('staff:csv_db_update') 
        return redirect(success_url)


class CsvToDbUpdateView(PermissionRequiredMixin, ListView):
    permission_required = [
        'tommy.add_module',
        'tommy.add_phrase',
        'tommy.add_translation',
        'tommy.change_module',
        'tommy.change_phrase',
        'tommy.change_translation',
    ]
    template_name = 'staff/csv_db_update.html'

    def get(self, request):
        if not request.user.is_superuser:
            non_staff_url = 'tommy:home'
            return redirect(non_staff_url)
        profile = Profile.objects.get(user=request.user)
        modules = Module.objects.all()
        phrases = Phrase.objects.all()
        translations = Translation.objects.all()
        submit_form = CsvSubmitForm() 

        # Try to create from CSV file a list of dictionaries to verify SQL data
        data_list = []
        try:
            with open('data.csv') as csvfile:
                data_reader = reader(csvfile)
                next(data_reader)
                row_count = 1
                for row in data_reader:
                    row_count += 1
                    dict_obj = {
                        'phrase_id': row[0],
                        'module_name': row[1],
                        'phrase': row[2],
                        'phrase_lang': row[3],
                        'translations': loads(row[4])
                    }
                    data_list.append(dict_obj)
        # If an error occurs give feedback
        except Exception as e:
            message = f"There was an error reading the file. "
            message += "Review the CSV and return to test form before running update. "
            context = {
                'profile': profile,
                'message': message,
                'details': e
            }
            return render(request, self.template_name, context)

        # Compare CSV data with database content and get stats
        current_phrase_count = phrases.count()
        new, total, changed, csv_phrase_ids = 0, 0, set(), []
        for item in data_list:
            total += 1
            if not item["phrase_id"]:
                new += 1
            else:
                csv_phrase_ids.append(item["phrase_id"])
                phrase = phrases.get(id=item["phrase_id"])
                if phrase["language"] != item["phrase_lang"]:
                    changed.add(item["phrase_id"])
                elif phrase["phrase"] != item["phrase"]:
                    changed.add(item["phrase_id"])
                elif phrase["module"] != item["module"]:
                    changed.add(item["phrase_id"])
                else:
                    phrase_translations = translations.filter(phrase=phrase)
                    a = set(phrase_translations)
                    b = set(item["translations"])
                    if len(a) != len(b) != len(a & b):
                        changed.add(item["phrase"])
        unchanged = total - new - len(changed)
        if changed:
            changed_phrases = ", ".join([f"{i}" for i in list(changed)]) + "\b\b."
        else:
            changed_phrases = ""
        for phrase in phrases:
            if phrase["id"] not in csv_phrase_ids:
                unchanged += 1

        context = {
            'profile': profile,
            'submit_form': submit_form,
            'current_phrase_count': current_phrase_count,
            'new': new,
            'changed': len(changed),
            'changed_phrases': changed_phrases,
            'unchanged': unchanged,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        if not request.user.is_superuser:
            non_staff_url = 'tommy:home'
            return redirect(non_staff_url)
        profile = Profile.objects.get(user=request.user)
        modules = Module.objects.all()
        phrases = Phrase.objects.all()
        translations = Translation.objects.all()
        user_strength_objs = UserPhraseStrength.objects.all()
        submit_form = CsvSubmitForm()
        if not submit_form.is_valid():
            context = {
                'profile': profile,
                'modules': modules,
                'phrases': phrases,
                'translations': translations,
                'submit_form': submit_form,
            }
            return render(request, self.template_name, context)
        
        # Run database test here 
        # Read the csv file 
        # Compare csv data with database content
        # Create / update / delete based on data comparison
        # 
        # if not successful redirect to error page 
        #     forwarding the error information to the error view
        # 
        # if successful redirect to submit page
        success_url = reverse_lazy('tommy:glossary')
        return redirect(success_url)