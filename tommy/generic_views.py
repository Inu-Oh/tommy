from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import View

from .models import Module, Phrase, Translation, Profile, UserPhraseStrength
from .forms import TestForm


class PhraseQuizView(LoginRequiredMixin, View):
    template_name = 'tommy:placeholder'

    def get(self, request):
        # Get and pass current test count to the request session
        # Try to get the test count if it already exists. Initiate it if it does not.
        try: 
            test_count = request.session.get('test_count')

            # If it is 15 or more, reset the test count to 0 and end current exercise
            if test_count >= 15:
                del request.session['test_count']
                exercise_completed_url = reverse_lazy('tommy:home')
                return redirect(exercise_completed_url)
        except:
            request.session['test_count'], test_count = 0, 0
        
        # Delete session data from previously tested phrase if it exists
        if test_count > 0:
            try:
                del request.session['user_phrase_strength']
                del request.session['user_answer']
                del request.session['response_accuracy']
                del request.session['phrase_language']
                del request.session['feedback_html']
            except:
                pass
            # The testing phrase id is only used in LearnView
            try:
                del request.session['user_phrase_strength_id']
            except:
                pass

        # Data for template view
        profile = Profile.objects.get(user=request.user)
        form = TestForm()

        context = { 'profile': profile, 'form': form }
        # In view.py get generic context with: context = super().get_context_data(**kwargs)
        # Then add context with: context['extra_data'] = 'This is extra context'
        return render(request, self.template_name, context)

    def post(self, request):
        # Data for template view
        profile = Profile.objects.get(user=request.user)
        form = TestForm(request.POST)

        # Verify the form data before proceeding or request new input
        user_answer = form.cleaned_data['answer'].strip()
        invalid_chars = []
        for val in ["]", "[", "}", "{", ")", "(", "$", "@", ">", "<", '"', ":", ";", "\\",
                    "=", "+", ".", "onerror", "onclick", "onload", "onmouseover"]:
            if val in user_answer:
                invalid_chars.append(val)
        if invalid_chars or not form.is_valid():
            if not form.is_valid():
                msg = "Please try again"
            else:
                msg = "Only letters, commas and apostrophes allowed"

            context = { 'profile': profile, 'form': form, 'message': msg }
            return render(request, self.template_name, context)

        # If post is successful and view is not learn update count and redirect to feedback view
        if self.template_name != 'tommy/learn.html':
            request.session['test_count'] += 1
        success_url = reverse_lazy('tommy:feedback')
        return redirect(success_url)


