from django.contrib import admin
from tommy.models import Module, Phrase, Profile, Translation, UserPhraseStrength


admin.site.register(Module)
admin.site.register(Profile)
admin.site.register(Translation)
admin.site.register(UserPhraseStrength)

@admin.register(Phrase)
class PhraseAdmin(admin.ModelAdmin):
    list_display = ('phrase', 'language', 'module')
    ordering = ('phrase', 'language', 'module')
    search_fields = ('phrase',)
    list_filter = ('language', 'module', 'phrase')
    


