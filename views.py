# -*- coding: utf-8 -*-
import datetime, random, hashlib
import re
from django import forms
from django.shortcuts import render, render_to_response, get_object_or_404
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login

from mipt_hack_server.models import UserProfile
from mipt_hack_server.forms import RegistrationForm

def index(request):
	if request.user.is_authenticated():
		return render(request, "mipt_hack_server/index.html", {"has_account": True})
	if request.POST:
		new_data = request.POST.copy()
		form = RegistrationForm(new_data)
		if (new_data["email"] is not "") and (new_data["password"] is not ""):
			match = re.match(r'(?P<email>.+@.+\..+)', new_data["email"])
			if not (match and match.groupdict()["email"] == new_data["email"]):
				return render(request, "mipt_hack_server/index.html", {"empty_data": True, "form": form})
		else:
			return render(request, "mipt_hack_server/index.html", {"empty_data": True, "form": form})

		errors = form.isValidUsername(new_data["email"])
		if not errors:
			new_user = form.save(new_data)

			salt = hashlib.md5(str(random.random())).hexdigest()[:5]
			activation_key = hashlib.md5(salt + new_user.username).hexdigest()
			key_expires = datetime.datetime.today() + datetime.timedelta(2)

			new_profile = UserProfile(
				user=new_user,
				activation_key=activation_key,
				key_expires=key_expires
				)
			new_profile.save()

			email_subject = "Your new master-igor.com account confirmation"
			email_body = "Hello, %s, and thanks for signing up for an \
master-igor.com account!\n\nTo activate your account, click this link within 48 \
hours:\n\nhttp://master-igor.com/test/confirm/%s/" % (
				new_user.username,
				new_profile.activation_key
				)
			send_mail(
				email_subject,
				email_body,
				"sigorilla@gmail.com",
				[new_user.email]
				)

			return render(request, "mipt_hack_server/index.html", {"created": True})
		else:
			user = authenticate(username=new_data["email"], password=new_data["password"])
			if user is not None:
				if user.is_active:
					login(request, user)
					# redirect to success page
					return render(request, "mipt_hack_server/index.html", {"has_account": True})
				else:
					# account is disabled
					return render(request, "mipt_hack_server/index.html", {"is_inactive": True, "form": form})
			else:
				# invalid login/password
				return render(request, "mipt_hack_server/index.html", {"wrong_data": True, "form": form})
	else:
		form = RegistrationForm()
		errors = new_data = {}

	return render(request, "mipt_hack_server/index.html", {"form": form})

def confirm(request, activation_key):
	if request.user.is_authenticated():
		return render_to_response("mipt_hack_server/confirm.html", {"has_account": True})
	user_profile = get_object_or_404(
		UserProfile,
		activation_key=activation_key
	)
	if user_profile.key_expires < datetime.datetime.today():
		return render_to_response("mipt_hack_server/confirm.html", {"expired": True})
	form = RegistrationForm()
	if user_profile.user.is_active:
		return render_to_response("mipt_hack_server/confirm.html", {"is_active": True})
	user_account = user_profile.user
	user_account.is_active = True
	user_account.save()
	return render(request, "mipt_hack_server/confirm.html", {"confirm": True})
