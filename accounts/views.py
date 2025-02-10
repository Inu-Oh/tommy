from django.http.response import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import UserCreateForm, ProfileForm


class RegisterView(CreateView):
    template_name = 'registration/register.html'

    def get(self, request):
        user_form = UserCreateForm()
        profile_form = ProfileForm()
        
        context = {
            'user_form': user_form,
            'profile_form': profile_form,
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        user_form = UserCreateForm(request.POST)
        profile_form = ProfileForm(request.POST)
        if not user_form.is_valid() or not profile_form.is_valid():
            context = {
                'user_form': user_form,
                'profile_form': profile_form,
            }
            return render(request, self.template_name, context)
        
        user_form.save() #Check for security issuse from DJ4E
        profile_form.user = user_form.instance
        profile_form.save()
        success_url = reverse_lazy('tommy:home')
        return redirect(success_url)