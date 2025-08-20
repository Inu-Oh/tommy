from django.test import TestCase
from django.contrib.auth import get_user_model

from .models import Module, Phrase, Profile, Translation, UserPhraseStrength


class ProfileTestCase(TestCase):

    def setUp(self):
        
        # Create users
        User = get_user_model()
        user = User.objects.create_user(username="foo", password="dj39&*d2", email="foo@cb-bc.gc.ca")
        admin = User.objects.create_superuser(username="bar", password="jd93*&2d", email="bar@cb-bc.gc.ca")
        threat = User.objects.create_user(username="baz", password="2fcv2$@1", email="baz@gmail.com")

        # Create profiles
        Profile.objects.create(user=user, name="Foo")
        Profile.objects.create(user=admin, name="Bar", xp=0)
        Profile.objects.create(user=threat, name="", xp=999_999_999)
    
    def test_profile_count(self):
        profiles = Profile.objects.all()
        self.assertEqual(profiles.count(), 3)

    def test_valid_user(self):
        user_profile = Profile.objects.get(name="Foo")
        self.assertTrue(user_profile.is_valid_profile())
    
    def test_valid_admin(self):
        admin_profile = Profile.objects.get(name="Bar")
        self.assertEqual(admin_profile.is_valid_profile())