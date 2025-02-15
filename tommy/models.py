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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} Pofile"


class Translation(models.Model):
    translation = models.CharField(
        max_length=248,
        validators=[MinLengthValidator(1, "This phrase is too short")]
    )
    language = models.ForeignKey(Language, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.translation


class Phrase(models.Model):
    phrase = models.CharField(
        max_length=248,
        validators=[MinLengthValidator(1, "This phrase is too short")]
    )
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    translations = models.ManyToManyField(Translation)
    learned = models.ManyToManyField(settings.AUTH_USER_MODEL,
        through='LearnedPhrase', related_name='phrases_learned')
    phrase_strength = models.ManyToManyField(settings.AUTH_USER_MODEL,
        through='PhraseStrength', related_name='phrases_strength')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.phrase


class LearnedPhrase(models.Model):
    phrase = models.ForeignKey(Phrase, on_delete=models.CASCADE)
    learner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phrase_learned = models.BooleanField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('learner', 'phrase')
    
    def __str__(self):
        return '%s has learned phrase "%s"'%(
            self.learner.username,
            self.phrase.phrase)
    

class PhraseStrength(models.Model):
    phrase = models.ForeignKey(Phrase, on_delete=models.CASCADE)
    learner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    view_count = models.PositiveIntegerField(default=1)
    user_phrase_score = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('learner', 'phrase')

    def __str__(self):
        return '%s has a user score of %d for the phrase "%s"'%(
            self.learner.username,
            int( (self.user_phrase_score / self.view_count) * 100),
            self.phrase.phrase
        )

    