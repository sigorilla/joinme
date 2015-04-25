from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils.timezone import now


class UserProfile(models.Model):

    class Meta:
        verbose_name = "UserProfile"
        verbose_name_plural = "UserProfiles"
        unique_together = (("user", "vk_user_id"),)

    def __str__(self):
        return self.user.username

    def __unicode__(self):
        return self.user.username

    def get_username(self):
        return ("%s %s" % (self.user.first_name, self.user.last_name)).strip()

    def get_user_email(self):
        return self.user.email

    def get_user_photo(self):
        return self.vk_photo_200

    user = models.OneToOneField(User)
    activation_key = models.CharField(max_length=40)
    key_expires = models.DateTimeField()
    vk_user_id = models.IntegerField(default=0)
    vk_access_token = models.CharField(max_length=254, default="", blank=True)
    vk_expires_in = models.CharField(max_length=254, default="", blank=True)
    vk_email = models.CharField(max_length=60, blank=True)
    # TODO: set default photo
    vk_photo_200 = models.CharField(max_length=255, blank=True)


class Category(models.Model):

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.title

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("joinme:category", kwargs={"pk": self.pk})

    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=100, blank=True, default="mdi-content-send")
    color = models.CharField(max_length=100, blank=True, default="material-teal")
    active = models.BooleanField(default=True)


class Comment(models.Model):

    class Meta:
        verbose_name = "Comment"
        verbose_name_plural = "Comments"

    def __str__(self):
        return self.message

    def __unicode__(self):
        return self.message

    user = models.ForeignKey(UserProfile, default=0)
    message = models.TextField()
    pub_date = models.DateTimeField("date published", default=now)


class Event(models.Model):

    class Meta:
        verbose_name = "Event"
        verbose_name_plural = "Events"

    def __str__(self):
        return self.title

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("joinme:event", kwargs={"pk": self.pk})

    def get_edit_url(self):
        return reverse("joinme:edit-event", kwargs={"pk": self.pk})

    def get_delete_url(self):
        return reverse("joinme:delete-event", kwargs={"pk": self.pk})

    def get_join_url(self):
        return reverse("joinme:join-event", kwargs={"pk": self.pk})

    def get_leave_url(self):
        return reverse("joinme:leave-event", kwargs={"pk": self.pk})

    def get_rating(self):
        return (self.rating / self.rating_count) if self.rating_count else self.rating

    title = models.CharField(max_length=45)
    description = models.TextField()
    datetime = models.DateTimeField()
    pub_date = models.DateTimeField("date published", default=now)
    category = models.ForeignKey(Category, default=1)
    author = models.ForeignKey(UserProfile, related_name='author')
    users = models.ManyToManyField(UserProfile, blank=True)
    active = models.BooleanField(default=True)
    comments = models.ManyToManyField(Comment, blank=True)
    rating = models.FloatField(default=0, blank=True)
    rating_count = models.IntegerField(default=0, blank=True)
    rating_users = models.ManyToManyField(UserProfile, blank=True, related_name="rating_users")
