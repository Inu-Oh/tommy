from csv import reader, writer
from json import loads

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
        if not request.user.is_staff:
            non_staff_url = 'tommy:home'
            return redirect(non_staff_url)
        test_form = CsvTestForm()

        context = {
            'test_form': test_form,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        if not request.user.is_staff:
            non_staff_url = 'tommy:home'
            return redirect(non_staff_url)
        test_form = CsvTestForm(request.POST)
        if not test_form.is_valid():
            context = {
                'test_form': test_form,
            }
            return render(request, self.template_name, context)
        
        # SQL data to be compared wotj CSV 
        modules = Module.objects.all()
        phrases = Phrase.objects.all()
        translations = Translation.objects.all()
        # (strength objects should only be created or deleted)
        user_strength_objs = UserPhraseStrength.objects.all()

        # Create from CSV file a list of dictionaries to be used to update SQL data
        data_list = []
        with open('data.csv') as csvfile:
            datareader = reader(csvfile)
            for row in datareader:
                dict_obj = {
                    'phrase_id': row[0],
                    'module_name': row[1],
                    'phrase': row[2],
                    'phrase_lang': row[3],
                    'translations': loads(row[4]) # Convert string to JSON then to list
                }
                data_list.append(dict_obj)


        # Run database test here 
        # Compare csv data with database content
        # check for errors in the csv input
        # 
        # if not successful redirect to error page 
        #     forwarding the error information to the error view
        # 
        # if successful redirect to submit page
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
        if not request.user.is_staff:
            non_staff_url = 'tommy:home'
            return redirect(non_staff_url)
        modules = Module.objects.all()
        phrases = Phrase.objects.all()
        translations = Translation.objects.all()
        submit_form = CsvSubmitForm() 
        context = {
            'modules': modules,
            'phrases': phrases,
            'translations': translations,
            'submit_form': submit_form,
        }
        return render(request, self.template_name, context)
        
    def post(self, request):
        if not request.user.is_staff:
            non_staff_url = 'tommy:home'
            return redirect(non_staff_url)
        modules = Module.objects.all()
        phrases = Phrase.objects.all()
        translations = Translation.objects.all()
        user_strength_objs = UserPhraseStrength.objects.all()
        submit_form = CsvSubmitForm()
        if not submit_form.is_valid():
            context = {
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