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