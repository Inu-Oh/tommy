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
        return f"{self.user.username}'s Profile"


class Module(models.Model):
    name = models.CharField(
        max_length=24,
        validators=[MinLengthValidator(5, "This name is too short")]
    )

    def __str__(self):
        return self.name


class Phrase(models.Model):
    FRENCH = "French"
    ENGLISH = "English"
    LANGUAGES = [
        (FRENCH, "French"),
        (ENGLISH, "English")
    ]
    language = models.CharField(max_length=12, choices=LANGUAGES, default=FRENCH)
    phrase = models.CharField(
        max_length=248,
        validators=[MinLengthValidator(1, "This phrase is too short")]
    )
    phrase_strength = models.ManyToManyField(settings.AUTH_USER_MODEL,
        through='UserPhraseStrength', related_name='user_strength')
    module = models.ForeignKey(Module, null=True, on_delete=models.SET_NULL)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.phrase


class Translation(models.Model):
    FRENCH = "French"
    ENGLISH = "English"
    LANGUAGES = [
        (FRENCH, "French"),
        (ENGLISH, "English")
    ]
    language = models.CharField(max_length=12, choices=LANGUAGES, default=FRENCH)
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
        return f'Phrase: "{self.phrase}" - Translation: "{self.translation}"'


class UserPhraseStrength(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='user_phrase_strength')
    phrase = models.ForeignKey(Phrase, on_delete=models.CASCADE)
    learned = models.BooleanField(default=False)
    views = models.IntegerField(default=0)
    correct = models.IntegerField(default=0)
    strength = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'phrase')
    
    def __str__(self):
        rep = f'User: {self.user.username}; Phrase: "{self.phrase.phrase}";'
        rep += f'Learned: "{self.learned}" Strength: {self.strength}'
        return rep