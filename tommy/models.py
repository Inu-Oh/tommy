from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models


class Language(models.Model):
    ENGLISH = 'Anglais'
    FRENCH = 'French'
    LANGUAGE_CHOICES = [
        (ENGLISH, 'Anglais'),
        (FRENCH, 'French'),
    ]
    language = models.CharField(
        max_length=20,
        choices=LANGUAGE_CHOICES,
        unique=True,
    )

    def __str__(self):
        return self.language


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(
        max_length=25,
        validators=[MinLengthValidator(1, "Choose a name I can call you")]
    )
    learning = models.ForeignKey(Language, default='French', on_delete=models.SET_DEFAULT)
    xp = models.IntegerField(default=0)
    level = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} Pofile"


class Translation(models.Model):
    translation = models.CharField(
        max_length=248,
        validators=[MinLengthValidator(1, "This phrase is too short")]
    )
    language = models.ForeignKey(Language, on_delete=models.CASCADE)

    def __str__(self):
        return self.translation


class Phrase(models.Model):
    phrase = models.CharField(
        max_length=248,
        validators=[MinLengthValidator(1, "This phrase is too short")]
    )
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    translations = models.ManyToManyField(Translation)


    def __str__(self):
        return self.phrase