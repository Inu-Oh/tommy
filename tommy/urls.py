from django.urls import path
from . import views

app_name = 'tommy'
urlpatterns = [
    # Home page
    path('', views.Home.as_view(), name='home'),

    # Dictionary view
    path('dictionary', views.Dictionary.as_view(), name='dictionary'),
]
