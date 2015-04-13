# -*- coding: utf-8 -*-
import datetime
import random
import hashlib
from functools import wraps

from django.utils.decorators import available_attrs
from django.core.mail import send_mail
from django.contrib.auth import authenticate
from django.core.urlresolvers import *
from django.http import JsonResponse
from django.middleware.csrf import _get_new_csrf_key

from joinme.forms import RegistrationForm
from joinme.models import UserProfile


def csrf_exempt(view_func):
    """
    Marks a view function as being exempt from the CSRF view protection.
    """
    # We could just do view_func.csrf_exempt = True, but decorators
    # are nicer if they don't have side-effects, so we return a new
    # function.
    def wrapped_view(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)
    wrapped_view.csrf_exempt = True
    return wraps(view_func, assigned=available_attrs(view_func))(wrapped_view)


"""
@api {get} /csrf/

@apiSuccess {String} token Token to access.

@apiError {String} error Message about error.
"""


def csrf(request):
    return JsonResponse({"token": _get_new_csrf_key()})


"""
@api {post} /reg/:email:password

@apiParam {String} email Users unique email
@apiParam {String} password Users password

@apiSuccess {String} token Token to access.

@apiError {String} error Message about error.
"""


@csrf_exempt
def reg(request):
    if request.POST:
        new_data = {
            "email": request.POST['email'],
            "password": request.POST['password']
        }
        form = RegistrationForm(new_data)
        if (new_data["email"] is not "") and (new_data["password"] is not ""):
            match = re.match(r'(?P<email>.+@.+\..+)', new_data["email"])
            if not (match and match.groupdict()["email"] == new_data["email"]):
                return JsonResponse({"error": "Wrong format of email."})
        else:
            return JsonResponse({"error": "Data is empty."})

        errors = form.is_valid_username(new_data["email"])
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
hours:\n\nhttp://master-igor.com%s" % (
                new_user.username,
                reverse_lazy(
                    "joinme:confirm-key",
                    kwargs={"activation_key": new_profile.activation_key}
                )
            )

            try:
                send_mail(
                    email_subject,
                    email_body,
                    "noreply@master-igor.com",
                    [new_user.email]
                )
            except Exception, e:
                return JsonResponse({"error": "Something happends on the server side."})

            return JsonResponse({"token": activation_key})
        else:
            return JsonResponse({"error": "This email is already taken."})
    else:
        return JsonResponse({"error": "It should be POST request."})


"""
@api {get} /login/:login:password

@apiParam {String} login Users unique login/email
@apiParam {String} password Users password

@apiSuccess {String} token Token to access.

@apiError {String} error Message about error.
"""


def login(request):
    if request.GET:
        if ('login' in request.GET) and request.GET['login'].strip() and \
                ('password' in request.GET) and request.GET['password'].strip():
            new_data = {
                "email": request.GET['login'],
                "password": request.GET['password']
            }
        else:
            return JsonResponse({"error": "Data is empty."})

        user = authenticate(username=new_data["email"], password=new_data["password"])
        if user is not None:
            if user.is_active:
                # login(request, user)
                profile = UserProfile.objects.filter(user__id__exact=user.id)[:1].values()
                if profile:
                    return JsonResponse({"token": profile[0]["activation_key"]})
                else:
                    return JsonResponse({"error": "User is not found."})
            else:
                # account is disabled
                return JsonResponse({"error": "User is disabled."})
        else:
            # invalid login/password
            return JsonResponse({"error": "Invalid data."})
    else:
        return JsonResponse({"error": "It should be GET request."})
