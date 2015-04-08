from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):

	class Meta:
		verbose_name = "UserProfile"
		verbose_name_plural = "UserProfiles"

	def __str__(self):
		return self.user.username

	def __unicode__(self):
		return self.user.username

	user = models.OneToOneField(User)
	activation_key = models.CharField(max_length=40)
	key_expires = models.DateTimeField()
