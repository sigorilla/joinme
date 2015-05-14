# -*- coding: utf-8 -*-
import datetime
import random
import hashlib
from functools import wraps

from django.utils.decorators import available_attrs
from django.core import serializers
from django.core.mail import send_mail
from django.contrib.auth import authenticate
from django.core.urlresolvers import *
from django.http import JsonResponse
from django.middleware.csrf import _get_new_csrf_key
from django.template.defaultfilters import truncatewords

from joinme.forms import RegistrationForm
from joinme.models import UserProfile, Event


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
            match = re.match(r'(?P<email>.+@phystech.edu)', new_data["email"])
            if not (match and match.groupdict()["email"] == new_data["email"]):
                return JsonResponse({"error": "Неверный формат почты."})
        else:
            return JsonResponse({"error": "Не найден логин или пароль. Повторите, пожалуйста."})

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

            email_subject = "Подтверждение нового аккаунта на сайте JoinMipt.com"
            email_body = ("Привет, %s! Спасибо за регистрацию на нашем сайте!\n\n\
Для активации аккаунта пройдите, пожалуйста, по ссылке в течении 48 часов:\n\n\
https://joinmipt.com%s").decode("utf-8", "replace") % (
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
                    "noreply@joinmipt.com",
                    [new_user.email]
                )
            except Exception, e:
                return JsonResponse({"error": "Что-то случилось на стороне сервера."})

            return JsonResponse({"token": activation_key})
        else:
            return JsonResponse({"error": "Эта почта уже занята."})
    else:
        return JsonResponse({"error": "Должен быть POST запрос."})


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
            return JsonResponse({"error": "Не найден логин или пароль. Повторите, пожалуйста."})

        user = authenticate(username=new_data["email"], password=new_data["password"])
        if user is not None:
            if user.is_active:
                # login(request, user)
                profile = UserProfile.objects.filter(user__id__exact=user.id)[:1].values()
                if profile:
                    return JsonResponse({"token": profile[0]["activation_key"]})
                else:
                    return JsonResponse({"error": "Не найден логин. Попробуйте зарегистрироваться."})
            else:
                # account is disabled
                return JsonResponse({"error": "Пожалуйста, подтвердите почту."})
        else:
            # invalid login/password
            return JsonResponse({"error": "Пароль неверен!"})
    else:
        return JsonResponse({"error": "Должен быть GET запрос."})


"""
@api {get} /events/:category:token

@apiParam {String} category name of Category
@apiParam {String} token activation key of current User

@apiSuccess {List} events List with Events

@apiError {String} error Message about error.
"""


# TODO: slice list of events
def get_events_by_category(request):
    if request.GET:
        if ('category' in request.GET) and request.GET['category'].strip() and \
                ('token' in request.GET) and request.GET['token'].strip():
            new_data = {
                "category": request.GET['category'],
                "token": request.GET['token']
            }
        else:
            return JsonResponse({"error": "Данные пустые."})
        try:
            userprofile = UserProfile.objects.filter(activation_key__exact=new_data["token"])
        except UserProfile.DoesNotExist:
            return JsonResponse({"error": "Ваш токен не найден в базе."})

        try:
            events_obj = list(Event.objects.filter(
                category__title__iexact=new_data["category"],
                active__exact=True
            ).order_by("-datetime", "title"))
            if not events_obj:
                return JsonResponse({"error": "В категории нет событий"})
            events = list()
            for event in events_obj:
                users_obj = list(event.users.all())
                users = list()
                for user in users_obj:
                    users.append({
                        "username": user.get_user_email(),
                        "id": user.id,
                    })
                events.append({
                    "id": event.id,
                    "title": event.title,
                    "author": {
                        "username": event.author.get_user_email(),
                        "photo": event.author.get_user_photo(),
                        "id": event.author.id,
                    },
                    "description": event.description,
                    "description_title": truncatewords(event.description, 20),
                    "datetime": event.datetime,
                    "members": users,
                    "coord": event.coord,
                })
        except Event.DoesNotExist:
            return JsonResponse({"error": "События не найдены."})
        else:
            return JsonResponse({"events": events})
    else:
        return JsonResponse({"error": "Должен быть GET запрос."})


"""
@api {get} /events/next/:token

@apiParam {String} token activation key of current User

@apiSuccess {Object} response Objects with fields 'count' and 'categories'

@apiError {String} error Message about error.
"""


def get_next_events(request):
    if request.GET:
        if ('token' in request.GET) and request.GET['token'].strip():
            new_data = {
                "token": request.GET['token']
            }
        else:
            return JsonResponse({"error": "Данные пустые."})
        try:
            userprofile = UserProfile.objects.filter(activation_key__exact=new_data["token"])
        except UserProfile.DoesNotExist:
            return JsonResponse({"error": "Ваш токен не найден в базе."})

        try:
            week = datetime.datetime.now() + datetime.timedelta(days=7)
            events_obj = Event.objects.filter(users__in=userprofile, active__exact=True, datetime__lte=week)
            events_author = Event.objects.filter(author__id=userprofile[0].id, active__exact=True, datetime__lte=week)

            categories = list()
            for event in (list(events_obj) + list(events_author)):
                category = event.category.title
                if category not in categories:
                    categories.append(event.category.title)

        except Event.DoesNotExist:
            return JsonResponse({"error": "События не найдены."})
        else:
            return JsonResponse({"response": {
                "count": events_obj.count(),
                "count_author": events_author.count(),
                "categories": categories
            }})
    else:
        return JsonResponse({"error": "Должен быть GET запрос."})


"""
@api {get} /event/join/:token:id

@apiParam {Int} id ID of event
@apiParam {String} token activation key of current User

@apiSuccess {String} success Message about success

@apiError {String} error Message about error.
"""


def join_event(request):
    if request.GET:
        if ('id' in request.GET) and request.GET['id'].strip() and \
                ('token' in request.GET) and request.GET['token'].strip():
            new_data = {
                "pk": request.GET["id"],
                "token": request.GET['token']
            }
        else:
            return JsonResponse({"error": "Данные пустые."})
        try:
            userprofile = UserProfile.objects.get(activation_key__exact=new_data["token"])
        except UserProfile.DoesNotExist:
            return JsonResponse({"error": "Ваш токен не найден в базе."})

        try:
            event = Event.objects.get(pk=new_data["pk"])
            if event.author.id != userprofile.id:
                event.users.add(userprofile)
                return JsonResponse({"success": "Вы присоединились к событию."})
            else:
                return JsonResponse({"error": "Вы автор события."})
        except Event.DoesNotExist:
            return JsonResponse({"error": "Событие не найдено."})
        except Exception:
            return JsonResponse({"error": "Что-то случилось на стороне сервера."})
    else:
        return JsonResponse({"error": "Должен быть GET запрос."})


"""
@api {get} /event/leave/:token:id

@apiParam {Int} id ID of event
@apiParam {String} token activation key of current User

@apiSuccess {String} success Message about success

@apiError {String} error Message about error.
"""


def leave_event(request):
    if request.GET:
        if ('id' in request.GET) and request.GET['id'].strip() and \
                ('token' in request.GET) and request.GET['token'].strip():
            new_data = {
                "pk": request.GET["id"],
                "token": request.GET['token']
            }
        else:
            return JsonResponse({"error": "Данные пустые."})
        try:
            userprofile = UserProfile.objects.get(activation_key__exact=new_data["token"])
        except UserProfile.DoesNotExist:
            return JsonResponse({"error": "Ваш токен не найден в базе."})

        try:
            event = Event.objects.get(pk=new_data["pk"])
            if event.author.id != userprofile.id:
                event.users.remove(userprofile)
                return JsonResponse({"success": "Вы покинули событие."})
            else:
                return JsonResponse({"error": "Вы автор события."})
        except Event.DoesNotExist:
            return JsonResponse({"error": "Событие не найдено."})
        except Exception:
            return JsonResponse({"error": "Что-то случилось на стороне сервера."})
    else:
        return JsonResponse({"error": "Должен быть GET запрос."})


"""
@api {get} /event/delete/:token:id

@apiParam {Int} id ID of event
@apiParam {String} token activation key of current User

@apiSuccess {String} success Message about success

@apiError {String} error Message about error.
"""


def delete_event(request):
    if request.GET:
        if ('id' in request.GET) and request.GET['id'].strip() and \
                ('token' in request.GET) and request.GET['token'].strip():
            new_data = {
                "pk": request.GET["id"],
                "token": request.GET['token']
            }
        else:
            return JsonResponse({"error": "Данные пустые."})
        try:
            userprofile = UserProfile.objects.get(activation_key__exact=new_data["token"])
        except UserProfile.DoesNotExist:
            return JsonResponse({"error": "Ваш токен не найден в базе."})

        try:
            event = Event.objects.get(pk=new_data["pk"])
            if event.author.id == userprofile.id:
                event.delete()
                return JsonResponse({"success": "Событие удалено."})
            else:
                return JsonResponse({"error": "Вы не автор события."})
        except Event.DoesNotExist:
            return JsonResponse({"error": "Событие не найдено."})
        except Exception:
            return JsonResponse({"error": "Что-то случилось на стороне сервера."})
    else:
        return JsonResponse({"error": "Должен быть GET запрос."})
