from django.db import models
from django.contrib.auth.models import User
from django.db.models import Count
from django.utils.timezone import datetime as dt

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

class Category(models.Model):

	class Meta:
		verbose_name = "Category"
		verbose_name_plural = "Categories"

	def __str__(self):
		return self.title

	def __unicode__(self):
		return self.title

	title = models.CharField(max_length=100)
	description = models.TextField(blank=True)
	icon = models.CharField(max_length=100, blank=True, default="mdi-content-send")
	color = models.CharField(max_length=100, blank=True, default="material-teal")
	active = models.BooleanField(default=True)

class Event(models.Model):

	class Meta:
		verbose_name = "Event"
		verbose_name_plural = "Events"

	def __str__(self):
		return self.title

	def __unicode__(self):
		return self.title

	title = models.CharField(max_length=200)
	description = models.TextField()
	datetime = models.DateTimeField()
	pub_date = models.DateTimeField("date published", default=dt.now())
	count_users = models.IntegerField(blank=True, default=100)
	category = models.ForeignKey(Category)
	author = models.ForeignKey(UserProfile, related_name='author')
	users = models.ManyToManyField(UserProfile, blank=True)
	active = models.BooleanField(default=True)
