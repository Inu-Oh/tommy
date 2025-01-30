from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models


class Language(models.Model):
    ENGLISH = 'EN'
    FRENCH = 'FR'
    LANGUAGE_CHOICES = [
        (ENGLISH, 'English'),
        (FRENCH, 'French'),
    ]
    language = models.CharField(
        max_length=2,
        choices=LANGUAGE_CHOICES,
        unique=True,
        validators=[MinLengthValidator(3, "This name is too short")],
    )

    def __str__(self):
        return self.language


class Profile(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(
        max_length=20,
        validators=[MinLengthValidator(1, "Add your name")]
    )
    learning = models.ForeignKey(Language, default='FR', on_delete=models.SET_DEFAULT) # Review
    xp = models.IntegerField(default=0)
    level = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} Pofile"


class Translation(models.Model):
    translation = models.CharField(
        max_length=248,
        validators=[MinLengthValidator(5, "This phrase is too short")]
    )
    language = models.ForeignKey(Language, on_delete=models.CASCADE)

    def __str__(self):
        return self.translation


class Phrase(models.Model):
    phrase = models.CharField(
        max_length=248,
        validators=[MinLengthValidator(5, "This phrase is too short")]
    )
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    translations = models.ManyToManyField(Translation)


    def __str__(self):
        return self.phrase