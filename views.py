# -*- coding: utf-8 -*-
import datetime, random, hashlib
import re
from django import forms
from django.shortcuts import render, render_to_response, get_object_or_404
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import *
from django.http import HttpResponseRedirect
from django.views import generic

from mipt_hack_server.models import UserProfile, Category, Event, User
from mipt_hack_server.forms import RegistrationForm, ResetForm

class LoginRequiredMixin(object):
	@classmethod
	def as_view(cls, **initkwargs):
		view = super(LoginRequiredMixin, cls).as_view(**initkwargs)
		return login_required(view, login_url=reverse_lazy("mipt:index"))

def index(request):
	if request.user.is_authenticated():
		list_categories = Category.objects.filter(active__exact=True)
		obj = {
			"has_account": True,
			"categories": list_categories,
		}
		return render(request, "mipt_hack_server/index.html", obj)

	next = ""
	if request.GET:
		next = request.GET["next"]

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
				"noreply@master-igor.com",
				[new_user.email]
				)

			return render(request, "mipt_hack_server/index.html", {"created": True})
		else:
			user = authenticate(username=new_data["email"], password=new_data["password"])
			if user is not None:
				if user.is_active:
					login(request, user)
					if next == "":
						return HttpResponseRedirect(reverse("mipt:index"))
					else:
						return HttpResponseRedirect(next)
					# redirect to success page
					# return render(request, "mipt_hack_server/index.html", {"has_account": True})
				else:
					# account is disabled
					return render(request, "mipt_hack_server/index.html", {"is_inactive": True, "form": form})
			else:
				# invalid login/password
				return render(request, "mipt_hack_server/index.html", {"wrong_data": True, "form": form})
	else:
		form = RegistrationForm()
		errors = new_data = {}

	return render(request, "mipt_hack_server/index.html", {"form": form, "next": next})

def confirm(request, activation_key):
	if request.user.is_authenticated():
		return render(request, "mipt_hack_server/confirm.html", {"has_account": True})
	user_profile = get_object_or_404(
		UserProfile,
		activation_key=activation_key
	)
	if user_profile.key_expires < datetime.datetime.today():
		return render(request, "mipt_hack_server/confirm.html", {"expired": True})
	form = RegistrationForm({"email": user_profile.user.email, "password": ""})
	if user_profile.user.is_active:
		return render(request, "mipt_hack_server/confirm.html", {"is_active": True, "form": form})
	user_account = user_profile.user
	user_account.is_active = True
	user_account.save()
	return render(request, "mipt_hack_server/confirm.html", {"confirm": True, "form": form})

@login_required(login_url=reverse_lazy("mipt:index"))
def settings(request):
	reset_form = ResetForm(user=request.user)
	if request.POST:
		if request.POST["name_form"] == "new_pass":
			reset_form = ResetForm(user=request.user, data=request.POST)
			if reset_form.is_valid():
				reset_form.save()
				return render(request, "mipt_hack_server/settings.html", 
					{"reset_form": reset_form, "reset_success": True})

	return render(request, "mipt_hack_server/settings.html", {"reset_form": reset_form})

class CategoryView(LoginRequiredMixin, generic.DetailView):
	model = Category
	template_name = "mipt_hack_server/category.html"

	def get_context_data(self, **kwargs):
		context = super(CategoryView, self).get_context_data(**kwargs)
		context["events"] = Event.objects.filter(category__exact=kwargs["object"].id)
		return context

class EventView(LoginRequiredMixin, generic.DetailView):
	model = Event
	template_name = "mipt_hack_server/event.html"

class MyEventsList(LoginRequiredMixin, generic.ListView):
	template_name = "mipt_hack_server/myevents.html"
	context_object_name = "events"

	def get_queryset(self):
		author = UserProfile.objects.filter(user__id=self.request.user.id).values()[0]
		return Event.objects.filter(author__id=author["id"])
