import random
from django import forms
from django.core import validators
from django.contrib.auth.models import User
from django.contrib.auth.forms import SetPasswordForm
from django.utils.translation import ugettext, ugettext_lazy as _
from django.utils.timezone import datetime
from django.core.mail import send_mail
from django.core.urlresolvers import *

from joinme.models import *

class RegistrationForm(forms.Form):
	email = forms.EmailField(
		label=_("Email"),
		max_length=40,
		required=True,
		widget=forms.EmailInput(attrs={"class": "form-control", "required": ""})
		)
	password = forms.CharField(
		label=_("Password"),
		max_length=60,
		required=True,
		widget=forms.PasswordInput(attrs={"class": "form-control", "required": ""})
		)

	def isValidUsername(self, field_data):
		try:
			User.objects.get(username=field_data)
		except User.DoesNotExist:
			return
		return validators.ValidationError("The username '%s' is already taken." % field_data)

	def save(self, new_data):
		u = User.objects.create_user(
			new_data["email"],
			new_data["email"],
			new_data["password"],
			last_login=datetime.now()
			)
		u.is_active = False
		u.save()
		return u

class ResetForm(SetPasswordForm):
	# old_password = forms.CharField(
	# 	label="Old password",
	# 	widget=forms.PasswordInput(attrs={"class": "form-control", "required": ""})
	# 	)
	new_password1 = forms.CharField(
		label=_("New password"),
		widget=forms.PasswordInput(attrs={"class": "form-control", "required": ""})
		)
	new_password2 = forms.CharField(
		label=_("New password confirmation"),
		widget=forms.PasswordInput(attrs={"class": "form-control", "required": ""})
		)

class PasswordResetForm(forms.Form):
	email = forms.EmailField(
		label=_("Email"), 
		max_length=254, 
		widget=forms.EmailInput(attrs={"class": "form-control", "required": ""})
		)

	def isValidEmail(self, data):
		try:
			return User.objects.get(username=data)
		except User.DoesNotExist:
			self.add_error("email", "User with email %s does not exist. " % data)
			return None

	def generate_password(self):
		alphabet = "abcdefghijklmnopqrstuvwxyz"
		upperalphabet = alphabet.upper()
		pw_len = 8
		pwlist = []

		for i in range(pw_len//3):
			pwlist.append(alphabet[random.randrange(len(alphabet))])
			pwlist.append(upperalphabet[random.randrange(len(upperalphabet))])
			pwlist.append(str(random.randrange(10)))
		for i in range(pw_len-len(pwlist)):
			pwlist.append(alphabet[random.randrange(len(alphabet))])

		random.shuffle(pwlist)
		return "".join(pwlist)

	def send_password(self, data):
		new_pass = self.generate_password()
		curr_user = User.objects.get(username__exact=data)
		curr_user.set_password(new_pass)
		curr_user.save()
		email_subject = "Reset password"
		email_body = "Hello, %s, and you reset password for an \
master-igor.com account!\n\nYour new password: %s \n\n\
After sign in, please, change you password in Settings page of your account:\n\
\thttp://master-igor.com/%s" % (
			curr_user.username,
			new_pass,
			reverse("joinme:settings")
			)
		return send_mail(
			email_subject,
			email_body,
			"noreply@master-igor.com",
			[curr_user.email]
			)

class CreationEventForm(forms.ModelForm):
	class Meta:
		model = Event
		fields = ('title', 'description', 'category', 'datetime', 'count_users')
		labels = {
			'datetime': 'Date of Event',
			'count_users': 'Limit of Members'
		}
		help_text = {
		}
		error_message = {
		}
		widgets = {
			'description': forms.Textarea(attrs={'rows': 4}),
		}
