from django import forms
from django.core import validators
from django.contrib.auth.models import User
from django.contrib.auth.forms import SetPasswordForm, PasswordResetForm
from django.utils.translation import ugettext, ugettext_lazy as _

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
			return field_data
		return validators.ValidationError("The username '%s' is already taken." % field_data)

	def save(self, new_data):
		u = User.objects.create_user(
			new_data["email"],
			new_data["email"],
			new_data["password"]
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

class MyPasswordResetForm(PasswordResetForm):
	email = forms.EmailField(
		label=_("Email"), 
		max_length=254, 
		widget=forms.EmailInput(attrs={"class": "form-control", "required": ""})
		)
