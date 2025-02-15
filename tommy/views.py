from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, View, CreateView

from .models import Language, Phrase, Profile, Translation
from .forms import ProfileForm


class Home(LoginRequiredMixin, View):
    template_name = 'tommy/home.html'

    def get(self, request):
        try:
            profile = Profile.objects.get(user = request.user)
            user_lang = str(profile.learning.language)
        except:
            profile = ''
            user_lang = ''

        context = {
            'profile': profile,
            'user_lang': user_lang,
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
        success_url = reverse_lazy('tommy:home')

        return redirect(success_url)


class GlossaryView(LoginRequiredMixin, ListView):
    template_name = 'tommy/glossary.html'

    def get(self, request):
        profile = Profile.objects.get(user = request.user)
        user_lang_obj = profile.learning
        user_lang = str(user_lang_obj)
        phrases = Phrase.objects.filter(language=user_lang_obj)
        
        context = {
            'profile': profile,
            'user_lang': user_lang,
            'phrases': phrases,
        }
        return render(request, self.template_name, context)


class LearnView(LoginRequiredMixin, ListView):
    template_name = 'tommy/learn.html'

    def get(self, request):
        profile = Profile.objects.get(user = request.user)
        user_lang_obj = profile.learning
        user_lang = str(user_lang_obj)
        phrases = Phrase.objects.filter(language=user_lang_obj)
        
        context = {
            'profile': profile,
            'user_lang': user_lang,
            'phrases': phrases,
        }
        return render(request, self.template_name, context)