from django.contrib import admin
from tommy.models import Language, Phrase, LearnedPhrase, PhraseStrength, Profile, Translation


admin.site.register(Language)
admin.site.register(Phrase)
admin.site.register(LearnedPhrase)
admin.site.register(PhraseStrength)
admin.site.register(Profile)
admin.site.register(Translation)
