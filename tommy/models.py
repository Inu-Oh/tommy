from django.core.validators import MinLengthValidator, MaxValueValidator, MinValueValidator
from django.db import models


class Word(models.Model):
    word = models.CharField(
        max_length=39,
        validators=[MinLengthValidator(2, "A word must have at least one letter.")],
    )
    word_translation = models.ManyToManyField('self')

    ENGLISH = 'EN'
    FRENCH = 'FR'
    CHINESE = 'CN'
    LANGUAGE_CHOICES = [
        (ENGLISH, 'English'),
        (FRENCH, 'French'),
        (CHINESE, 'Chinese'),
    ]
    language = models.CharField(
        max_length=2,
        choices=LANGUAGE_CHOICES,
        default=ENGLISH,
    )
    level = models.IntegerField(
        default=0,
        validators=[
            MaxValueValidator(10),
            MinValueValidator(0)
        ])

    def __str__(self):
        return self.word

class Phrase(models.Model):
    phrase = models.CharField(
        max_length=248,
        validators=[MinLengthValidator(5, "A phrase must have at least two words")],
    )
    phrase_translation = models.ManyToManyField('self')

    ENGLISH = 'EN'
    FRENCH = 'FR'
    CHINESE = 'CN'
    LANGUAGE_CHOICES = [
        (ENGLISH, 'English'),
        (FRENCH, 'French'),
        (CHINESE, 'Chinese'),
    ]
    language = models.CharField(
        max_length=2,
        choices=LANGUAGE_CHOICES,
        default=ENGLISH,
    )
    level = models.IntegerField(
        default=0,
        validators=[
            MaxValueValidator(10),
            MinValueValidator(0)
        ])

    def __str__(self):
        return self.phrase