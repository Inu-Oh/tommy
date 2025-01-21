from django.contrib import admin
from tommy.models import Word, WordTranslation, Phrase, PhraseTranslation

# Register your models here.
admin.site.register(Word)
admin.site.register(WordTranslation)
admin.site.register(Phrase)
admin.site.register(PhraseTranslation)