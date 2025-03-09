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

    # Modules view
    path('modules', views.ModulesView.as_view(), name='modules'),

    # Learn new phrases
    path('learn/<int:pk>', views.LearnView.as_view(), name='learn'),

    # Practice weakest phrases
    path('practice',views.PracticeView.as_view(), name='practice'),

    # Review phrases not seen for longes time
    path('review', views.ReviewView.as_view(), name='review'),

    # Practice correct accent translations
    path('accent', views.AccentView.as_view(), name='accent'),
]
