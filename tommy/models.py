from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(
        max_length=25,
        validators=[MinLengthValidator(1, "Choose a name I can call you")]
    )
    xp = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} Pofile"


class Phrase(models.Model):
    phrase = models.CharField(
        max_length=248,
        validators=[MinLengthValidator(1, "This phrase is too short")]
    )
    translations = models.CharField(
        max_length=248,
        validators=[MinLengthValidator(1, "This phrase is too short")]
    )
    learned = models.ManyToManyField(settings.AUTH_USER_MODEL,
        through='UserLearned', related_name='user_learned')
    phrase_strength = models.ManyToManyField(settings.AUTH_USER_MODEL,
        through='UserStrength', related_name='user_strength')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.phrase
