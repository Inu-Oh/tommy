from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views.generic import CreateView


class RegisterView(CreateView):
    form = UserCreationForm()
    success_url = reverse_lazy('tommy:home')
    template_name = 'registration/register.html'