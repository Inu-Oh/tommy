from django.contrib import admin
from tommy.models import Phrase, Profile, Translation, UserLearnedPhrase, UserPhraseStrength


admin.site.register(Phrase)
admin.site.register(Profile)
admin.site.register(Translation)
admin.site.register(UserLearnedPhrase)
admin.site.register(UserPhraseStrength)
