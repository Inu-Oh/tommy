from django.contrib import admin
from tommy.models import Language, Phrase, Translation


admin.site.register(Language)
admin.site.register(Phrase)
admin.site.register(Translation)