from django.conf import settings
from django.core.validators import MinLengthValidator
from django.contrib.auth.models import User
from django.db import models

from tommy.models import Language


User._meta.get_field('email').blank = False


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    learning = models.ForeignKey(Language, default='French', on_delete=models.SET_DEFAULT) # Review
    xp = models.IntegerField(default=0)
    level = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} Pofile"