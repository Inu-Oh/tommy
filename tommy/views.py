from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, View, CreateView

from .models import Phrase, Profile
from .forms import ProfileForm, TestForm


class Home(LoginRequiredMixin, View):
    template_name = 'tommy/home.html'

    def get(self, request):
        try:
            profile = Profile.objects.get(user = request.user)
        except:
            profile = ''

        context = {
            'profile': profile,
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
        phrases = Phrase.objects.all()
        
        context = {
            'profile': profile,
            'phrases': phrases,
        }
        return render(request, self.template_name, context)


class LearnView(LoginRequiredMixin, ListView):
    template_name = 'tommy/learn.html'

    def get(self, request):
        profile = Profile.objects.get(user = request.user)
        form = TestForm()
        
        context = {
            'profile': profile,
            'form': form,
        }
        return render(request, self.template_name, context)