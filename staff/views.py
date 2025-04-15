from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import UpdateView, CreateView, ListView

from tommy.models import Module, Phrase, Translation, Profile
from tommy.forms import PhraseStrengthForm

from .forms import ModuleForm, CreatePhraseForm, CreateTranslationForm
    

# Menu for admins to navigate adding and editing content
# Reserve deleting content for superusers in admin section
# TODO apply PermissionRequiredMixin
# TODO figure out how to access pks for each optional object updated
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
class CreateModuleView(LoginRequiredMixin, CreateView):
    model = Module
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


class CreatePhraseView(LoginRequiredMixin, CreateView):
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


class CreateTranslationView(LoginRequiredMixin, CreateView):
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
class UpdateModuleView(LoginRequiredMixin, UpdateView):
    template_name = 'staff/edit_module.html'
    
    def get(self, request, pk):
        if not request.user.is_staff:
            non_staff_url = 'tommy:home'
            return redirect(non_staff_url)

        return render(request, self.template_name)


class UpdatePhraseView(LoginRequiredMixin, UpdateView):
    template_name = 'staff/edit_phrase.html'
    
    def get(self, request, pk):
        if not request.user.is_staff:
            non_staff_url = 'tommy:home'
            return redirect(non_staff_url)

        return render(request, self.template_name)


class UpdateTranslationView(LoginRequiredMixin, UpdateView):
    template_name = 'staff/edit_translation.html'
    
    def get(self, request, pk):
        if not request.user.is_staff:
            non_staff_url = 'tommy:home'
            return redirect(non_staff_url)

        return render(request, self.template_name)