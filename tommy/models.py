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
        return f"{self.user.username} Profile"


class Phrase(models.Model):
    phrase = models.CharField(
        max_length=248,
        validators=[MinLengthValidator(1, "This phrase is too short")]
    )
    learned = models.ManyToManyField(settings.AUTH_USER_MODEL,
        through='UserLearnedPhrase', related_name='user_learned')
    phrase_strength = models.ManyToManyField(settings.AUTH_USER_MODEL,
        through='UserPhraseStrength', related_name='user_strength')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.phrase


class Translation(models.Model):
    translation = models.CharField(
        max_length=248,
        validators=[MinLengthValidator(1, "This phrase is too short")]
    )
    """ How to get all translations for the phrase ?
    phrase = Phrase.objects.get(id=pk)
    translations = phrase.translation_set.all()
    """
    phrase = models.ForeignKey(Phrase, null=True, on_delete=models.SET_NULL,
        related_name='phrase_translation')

    def __str__(self):
        return 'Phrase: "%s" - Translation: "%s"'%(
            self.phrase,
            self.translation
        )


class UserLearnedPhrase(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='user_learned_phrase')
    phrase = models.ForeignKey(Phrase, on_delete=models.CASCADE)
    learned = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'phrase')
    
    def __str__(self):
        if (self.learned == True):
            return '%s has learned the phrase "%s"'%(
                self.user.username,
                self.phrase.phrase
            )
        else:
            return '%s has not yet learned the phrase "%s"'%(
                self.user.username,
                self.phrase.phrase
            )


class UserPhraseStrength(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='user_phrase_strength')
    phrase = models.ForeignKey(Phrase, on_delete=models.CASCADE)
    strength = models.IntegerField(default=0)

    class Meta:
        unique_together = ('user', 'phrase')
    
    def __str__(self):
        return 'User: %s; Phrase: "%s"; Strength: %d'%(
            self.user.username,
            self.phrase.phrase,
            self.strength
        )