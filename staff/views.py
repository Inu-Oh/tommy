from csv import reader, DictWriter
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

        # TODO can I remove phrase_strength_form.save(commit=False) ?
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
        row, non_ints, wrong_ids = 1, "", ""
        for item in data_list:
            row += 1
            if phrase_id := item["phrase_id"]:
                if not isinstance(phrase_id, int):
                    if not non_ints:
                        non_ints += "Phrase IDs at these rows should be an intager number: "
                    non_ints += f"{row}, "
                if not phrases.get(id=phrase_id):
                    if not wrong_ids:
                        wrong_ids += "Phrase IDs at the following rows don't exist in the database."
                        wrong_ids += "Delete if the it's a new phrase or "
                        worng_ids += "correct if the phrase is already in the database: "
                    wrong_ids += f"ID {phrase_id} at row {row}, "
        if non_ints or wrong_ids:
            message += "Errors with data entry for phrase ID column. " 
            if non_ints:
                message += non_ints + "\b\b. "
            if wrong_ids:
                message += wrong_ids+ "\b\b. "
            message += "Correct all phrase IDs before running the test again. "
            context = {
                'profile': profile,
                'test_form': test_form,
                'message': message,
            }
            return render(request, self.template_name, context)

        # Verify that module name is entered for each phrase and not longer than 24 chars
        row = 1
        for item in data_list:
            row += 1
            if not item["module_name"]:
                message += f"blank at row {row}, "
            elif len(item["module_name"]) > 24:
                message += f"name too long at row {row}, "
        if message:
            message += "Module names not provided or too long for phrases at rows: " + message
            message += "\b\b. Provide module names for each phrase."
            context = {
                'profile': profile,
                'test_form': test_form,
                'message': message,
            }
            return render(request, self.template_name, context)
        
        # Check that phrases ware entered and only contain alphabetic characters
        row, missing_phrases, non_alphas = 1, "", ""
        for item in data_list:
            row += 1
            if not item["phrase"]:
                if not missing_phrases:
                    missing_phrases += "Phrase cells are blank at the following rows: "
                missing_phrases += f"{row}, "
            elif match(r'[a-zA-Z ]$', item["phrase"]):
                if not non_alphas:
                    non_alphas += "The following phrases include non-alpha characters: "
                non_alphas += f'"{item["phrase"]}" at row {row}, '
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

        # Check that new phrases are unique
        phrase_list, duplicates, row = [phrase.phrase for phrase in phrases], [], 1
        for item in data_list:
            if not item["id"]:
                if phrase := item["phrase"] in phrase_list:
                    duplicates.append({'phrase': phrase, 'row': row})
                else:
                    phrase_list.append(phrase)
            row += 1
        if duplicates:
            message += "The CSV file includes phrases that are duplicates: "
            for phrase, row in duplicates:
                message += f'"{phrase}" at row {row}, '
            message += "\b\b. Make sure there are no duplicates before testing again."
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

        # Verify that all row have well formatted translations that include only alphabetic characters
        row, non_lists, non_alphas, missing_translations = 1, "", "", ""
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
                    if match(r'[a-zA-Z ]$', translation):
                        if not non_alphas:
                            non_alphas += "Translations in the following rows include non-alphabetic characters: "
                        non_alphas += f"{row}, "
            else: # if list is empty
                if not missing_translations:
                    missing_translations += "Translations are missing for phrases in rows: "
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
            if phrase.id not in csv_phrase_ids:
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
        submit_form = CsvSubmitForm(request.POST)
        if not submit_form.is_valid():
            message = "The update failed due to an invalid form. Contact IT for support."
            context = {
                'profile': profile,
                'message': message,
            }
            return render(request, self.template_name, context)
        
        # Read the CSV file and create list of dicts to track data
        data_list, val_error = [], ""
        try:
            with open('data.csv') as csvfile:
                data_reader = reader(csvfile)
                next(data_reader)
                row_count = 1
                for row in data_reader:
                    dict_obj = {
                        'row': row_count,
                        'phrase_id': row[0],
                        'module': row[1],
                        'phrase': row[2],
                        'phr_lang': row[3],
                        'translations': loads(row[4])
                    }
                    if not dict_obj['module_name'] or not dict_obj['phrase'] or not dict_obj['phrase_lang'] or not dict_obj['translations']:
                        val_error += f"There is blank data at row {dict_obj['row']}. "
                        raise ValueError
                    data_list.append(dict_obj)
                    row_count += 1
        # If an error occurs give feedback
        except Exception as e:
            message = "There was an error reading the file. "
            message += val_error
            message += "Review the CSV and return to test form before running update. "
            context = {
                'profile': profile,
                'message': message,
                'details': e
            }
            return render(request, self.template_name, context)


        """The next six loops run same varfications as CsvToDbTestView, but abbreviated."""
        # Check that phrase id is entered correctly
        row = 1
        for item in data_list:
            row += 1
            if phrase_id := item["phrase_id"]:
                if not isinstance(phrase_id, int) or not phrases.get(id=phrase_id):
                    message = "Errors with data entry in the phrase ID column. "
                    message += "Review the data before continuing." 
                    context = { 'profile': profile, 'message': message }
                    return render(request, self.template_name, context)

        # Verify that module name is entered for each phrase
        row = 1
        for item in data_list:
            row += 1
            if not item["module_name"]:
                message = "Module names are missing. Provide module names for each phrase before continuing."
                context = { 'profile': profile, 'message': message }
                return render(request, self.template_name, context)
        
        # Check that phrases ware entered and only contain alphabetic characters
        row = 1
        for item in data_list:
            row += 1
            if not item["phrase"] or match(r'[a-zA-Z ]$', item["phrase"]):
                message = "Some phrases are too long or include non-alphabetic characters. "
                message += "Add missing phrases and replace non alphabetic characters before continuing."
                context = { 'profile': profile, 'message': message }
                return render(request, self.template_name, context)

        # Check that new phrases are unique
        phrase_list, row = [phrase.phrase for phrase in phrases], 1
        for item in data_list:
            row += 1
            if not item["id"]:
                if phrase := item["phrase"] in phrase_list:
                    message = "The CSV file includes duplicate phrases. Remove them before continuing."
                    context = { 'profile': profile, 'message': message }
                    return render(request, self.template_name, context)                    
                else:
                    phrase_list.append(phrase)

        # Verify either English or French for language options
        row = 1
        for item in data_list:
            row += 1
            if item["phrase_lang"] not in ["French", "English"]:
                message = "Some rows list an invalid phrase language. Review all rows and ensure that "
                message += "phrases have either French or English language before continuing."
                context = { 'profile': profile, 'message': message }
            return render(request, self.template_name, context)

        # Verify that all phrases have translations and those include only alphabetic characters
        row, non_lists, non_alphas, missing_translations = 1, False, False, False
        for item in data_list:
            row += 1
            if translations := item["translations"]:
                if type(translations) is not list:
                    non_lists = True
                    break
                for translation in translations:
                    if match(r'[a-zA-Z ]$', translation):
                        non_alphas = True
                        break
            else: # if list is empty
                missing_translations = True
                break
        if missing_translations or non_alphas or non_lists:
            message = "Errors with data entry for translation column. Add translations for phrases with the "
            message += "format [\"Translation one\", \"Two and\", \"Three\"]. Correct all rows before continuing."
            context = {
                'profile': profile,
                'message': message,
            }
            return render(request, self.template_name, context)


        """The below code populates and updates the database."""
        # Data to track changes
        module_names, added_modules = [module.name for module in modules], 0
        added_phrases, updated_phrases, added_strength_objs  = 0, 0, 0
        deleted_translations, added_translations = 0, 0

        # TODO Put this in a try except block - check best practices
        # If id is blank set phrase as new. Otherwise, set it as old.
        row = 1
        for dict_obj in data_list:
            row += 1
            # If the phrase's module doesn't exists create it
            if module_name := dict_obj["module"] not in module_names:
                module = ModuleForm()
                module.name = module_name
                module.save()
                module_names.append(module_name)
                added_modules += 1
            else:
                module = modules.get(name=dict_obj["module"])
            
            # Create new phrase or update it if phrase id was listed
            trans_lang = "English" if str(dict_obj["phr_lang"]) == "French" else "French"
            if phrase_id := dict_obj["phrase_id"] != "":
                phrase = phrases.get(id=phrase_id)
                phrase.language = dict_obj["phr_lang"]
                phrase.phrase = dict_obj["pharse"]
                phrase.module = module
                phrase.save()
                updated_phrases += 1
                # Delete old translations rather than comparing for changes
                old_translations = translations.filter(phrase=phrase.phrase)
                for translation in old_translations:
                    translation.delete()
                    deleted_translations += 1
            else:
                phrase = CreatePhraseForm()
                phrase.language = dict_obj["phr_lang"]
                phrase.phrase = dict_obj["phrase"]
                phrase.module = module
                phrase.save()
                added_phrases += 1
                # Create phrase strength objects for each user for new phrases only
                User = get_user_model()
                users = User.objects.all()
                for user in users:
                    phrase_strength = PhraseStrengthForm()
                    phrase_strength.phrase = phrase
                    phrase_strength.user = user
                    phrase_strength.learned = False
                    phrase_strength.strength = 0
                    phrase_strength.views = 0
                    phrase_strength.correct = 0
                    phrase_strength.save()
                    added_strength_objs += 1
            
            # Loop through translations and save each one for the phrase
            for translation in dict_obj["tranlations"]:
                new_translation = CreateTranslationForm()
                new_translation.language = trans_lang
                new_translation.translation = translation
                new_translation.phrase = phrase
                new_translation.save()
                added_translations += 1
               
            #   CSV update: get id after new phrase is saved and update it to the CSV file
        # if an error occurs redirect to error page 
        #     forwarding the error information to the error view
                # provide row of CSV and phrase as well as other element info
        # 
        # if successful redirect to success url with report on changes
        
        success_url = reverse_lazy('tommy:glossary')
        return redirect(success_url)