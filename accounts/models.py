from django.conf import settings
from django.core.validators import MinLengthValidator
from django.contrib.auth.models import User
from django.db import models

from tommy.models import Language


User._meta.get_field('email').blank = False