from django.urls import path
from . import views

app_name = 'tommy'
urlpatterns = [
    # Home page
    path('', views.Home.as_view(), name='home'),

    # Profile creation and edit views
    path('create_profile', views.ProfileCreateView.as_view(), name='create_profile'),

    # Dictionary view
    path('glossary', views.GlossaryView.as_view(), name='glossary'),

    # Learn view
    path('learn', views.LearnView.as_view(), name='learn'),
]
