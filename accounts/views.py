from django.http.response import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import UserCreateForm


class RegisterView(CreateView):
    template_name = 'registration/register.html'

    def get(self, request):
        form = UserCreateForm()
        
        context = {'form': form}
        return render(request, self.template_name, context)
    
    def post(self, request):
        form = UserCreateForm(request.POST)
        if not form.is_valid():
            context = {'form': form}
            return render(request, self.template_name, context)
        
        form.save()
        success_url = reverse_lazy('tommy:home')
        return redirect(success_url)