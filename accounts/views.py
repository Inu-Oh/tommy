from django.http.response import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import UserCreateForm


class RegisterView(CreateView):
    template_name = 'registration/register.html'

    def get(self, request):
        user_form = UserCreateForm()
        context = {'user_form': user_form}
        return render(request, self.template_name, context)
    
    def post(self, request):
        user_form = UserCreateForm(request.POST)
        if not user_form.is_valid():
            context = {'user_form': user_form}
            return render(request, self.template_name, context)
        
        user_form.save() #Check for security issuse from DJ4E
        success_url = reverse_lazy('tommy:home')
        return redirect(success_url)