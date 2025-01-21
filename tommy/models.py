from django.core.validators import RegexValidator, MinLengthValidator, MaxValueValidator, MinValueValidator
from django.db import models


class WordTranslation(models.Model):
    word_translation = models.CharField(
        max_length=39,
        validators=[MinLengthValidator(1, "A word must have at least one letter.")]
    )
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

    def __str__(self):
        return self.word_translation
    

class Word(models.Model):
    word = models.CharField(
        max_length=39,
        validators=[MinLengthValidator(1, "A word must have at least one letter.")],
    )
    word_translation = models.ManyToManyField(WordTranslation)

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


class PhraseTranslation(models.Model):
    phrase_translation = models.CharField(
        max_length=248,
        validators=[MinLengthValidator(5, "A phrase must have at least two words"),
                    RegexValidator(r'[a-zA-Z]+\s+[a-zA-Z]+',"A phrase must have at least two words")],
    )
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

    def __str__(self):
        return self.phrase_translation


class Phrase(models.Model):
    phrase = models.CharField(
        max_length=248,
        validators=[MinLengthValidator(5, "A phrase must have at least two words"),
                    RegexValidator(r'[a-zA-Z]+\s+[a-zA-Z]+',"A phrase must have at least two words")],
    )
    phrase_translation = models.ManyToManyField(PhraseTranslation)

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