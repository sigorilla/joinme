from django import forms
from django.core import validators
from django.contrib.auth.models import User

class RegistrationForm(forms.Form):
	email = forms.EmailField(
		max_length=40,
		required=True,
		widget=forms.EmailInput(attrs={"class": "form-control"})
		)
	password = forms.CharField(
		max_length=60,
		required=True,
		widget=forms.PasswordInput(attrs={"class": "form-control"})
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
			new_data["password"]
			)
		u.is_active = False
		u.save()
		return u
