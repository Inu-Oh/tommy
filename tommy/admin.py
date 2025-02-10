from django.contrib import admin
from tommy.models import Language, Phrase, Profile, Translation


admin.site.register(Language)
admin.site.register(Phrase)
admin.site.register(Profile)
admin.site.register(Translation)