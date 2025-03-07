from django.contrib import admin
from tommy.models import Module, Phrase, Profile, Translation, UserPhraseStrength


admin.site.register(Module)
admin.site.register(Phrase)
admin.site.register(Profile)
admin.site.register(Translation)
admin.site.register(UserPhraseStrength)
