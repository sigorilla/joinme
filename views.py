# -*- coding: utf-8 -*-
import datetime
import random
import hashlib

from django.conf import settings as glob_setting
from django.shortcuts import render, get_object_or_404
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.urlresolvers import *
from django.http import HttpResponseRedirect
from django.views import generic

from joinme.models import UserProfile, Category, Event
from joinme.forms import ResetForm, RegistrationForm, CreateEventForm, PasswordResetForm, EditEventForm, EditUser


class LoginRequiredMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(LoginRequiredMixin, cls).as_view(**initkwargs)
        return login_required(view, login_url=reverse_lazy("joinme:index"))


class NeverCacheMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(NeverCacheMixin, cls).as_view(**initkwargs)
        return never_cache(view)


def index(request):
    if request.user.is_authenticated():
        list_categories = Category.objects.filter(active__exact=True)
        obj = {
            "has_account": True,
            "categories": list_categories,
        }
        return render(request, "joinme/index.html", obj)

    next = ""
    if request.GET:
        next = request.GET["next"]

    if request.POST:
        new_data = request.POST.copy()
        form = RegistrationForm(new_data)
        if (new_data["email"] is not "") and (new_data["password"] is not ""):
            match = re.match(r'(?P<email>.+@.+\..+)', new_data["email"])
            if not (match and match.groupdict()["email"] == new_data["email"]):
                return render(request, "joinme/index.html", 
                              {"empty_data": True, "form": form})
        else:
            return render(request, "joinme/index.html", 
                          {"empty_data": True, "form": form})

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
                return render(request, "joinme/index.html", 
                              {"server_fail": True, "form": form})

            return render(request, "joinme/index.html", {"created": True})
        else:
            user = authenticate(username=new_data["email"], password=new_data["password"])
            if user is not None:
                if user.is_active:
                    login(request, user)
                    if next == "":
                        return HttpResponseRedirect(reverse("joinme:index"))
                    else:
                        return HttpResponseRedirect(next)
                    # redirect to success page
                    # return render(request, "joinme/index.html", {"has_account": True})
                else:
                    # account is disabled
                    return render(request, "joinme/index.html", 
                                  {"is_inactive": True, "form": form})
            else:
                # invalid login/password
                return render(request, "joinme/index.html", 
                              {"wrong_data": True, "form": form})
    else:
        form = RegistrationForm()

    return render(request, "joinme/index.html", {"form": form, "next": next})


def confirm(request, activation_key):
    if request.user.is_authenticated():
        return render(request, "joinme/confirm.html", {"has_account": True})
    user_profile = get_object_or_404(
        UserProfile,
        activation_key=activation_key
    )
    if user_profile.key_expires < datetime.datetime.today():
        return render(request, "joinme/confirm.html", {"expired": True})
    form = RegistrationForm({"email": user_profile.user.email, "password": ""})
    if user_profile.user.is_active:
        return render(request, "joinme/confirm.html", {"is_active": True, "form": form})
    user_account = user_profile.user
    user_account.is_active = True
    user_account.save()
    return render(request, "joinme/confirm.html", {"confirm": True, "form": form})


class SettingsView(NeverCacheMixin, LoginRequiredMixin, generic.View):

    @staticmethod
    def get(request):
        reset_form = ResetForm(user=request.user, prefix="reset_form")
        user_form = EditUser(instance=request.user, prefix="user_form")
        return render(request, "joinme/settings.html", {
            "reset_form": reset_form,
            "user_form": user_form,
            "title": "Settings",
            "VK_API_ID": glob_setting.VK_API_ID,
            "host": request.get_host()
        })

    @staticmethod
    def post(request):
        reset_form = ResetForm(user=request.user, prefix="reset_form")
        user_form = EditUser(instance=request.user, prefix="user_form")
        reset_success = False
        user_success = False
        action = request.POST["name_form"]
        if action == "new_pass":
            if reset_form.is_valid():
                reset_form.save()
                reset_success = True
        elif action == "user_edit":
            user_form = EditUser(request.POST, instance=request.user, prefix="user_form")
            if user_form.is_valid():
                user_form.save()
                user_success = True
        context = {
            "reset_form": reset_form,
            "user_form": user_form,
            "reset_success": reset_success,
            "user_success": user_success,
            "title": "Settings",
            "VK_API_ID": glob_setting.VK_API_ID,
            "host": request.get_host(),
        }
        return render(request, "joinme/settings.html", context)


class CategoryView(LoginRequiredMixin, generic.DetailView):
    model = Category
    template_name = "joinme/category.html"

    def get_context_data(self, **kwargs):
        context = super(CategoryView, self).get_context_data(**kwargs)
        context["events"] = Event.objects.filter(
            category__exact=kwargs["object"].id, 
            active__exact=True
        )
        return context


class EventView(NeverCacheMixin, LoginRequiredMixin, generic.DetailView):
    model = Event
    template_name = "joinme/event.html"
    paginate_by = 10


@never_cache
def join_event(request, pk):
    event = Event.objects.get(pk=pk)
    if event.author.id != request.user.userprofile.id:
        event.users.add(request.user.userprofile)
        event.save()
    return HttpResponseRedirect(event.get_absolute_url())


@never_cache
def leave_event(request, pk):
    event = Event.objects.get(pk=pk)
    if event.author.id != request.user.userprofile.id:
        event.users.remove(request.user.userprofile)
        event.save()
    return HttpResponseRedirect(event.get_absolute_url())


class MyEventsList(NeverCacheMixin, LoginRequiredMixin, generic.ListView):
    template_name = "joinme/event_list.html"
    context_object_name = "events"
    paginate_by = 10

    def get_queryset(self):
        user_id = self.request.user.userprofile.id
        query = (Q(active=True) & Q(users__id=user_id)) | Q(author__id=user_id)
        return Event.objects.filter(query).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super(MyEventsList, self).get_context_data(**kwargs)
        context["title"] = "My Events"
        return context


class CreatedEventsList(NeverCacheMixin, LoginRequiredMixin, generic.ListView):
    template_name = "joinme/event_list.html"
    context_object_name = "events"
    paginate_by = 10

    def get_queryset(self):
        return Event.objects.filter(
            author__id=self.request.user.userprofile.id).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super(CreatedEventsList, self).get_context_data(**kwargs)
        context["title"] = "My created Events"
        return context


class AllEventsList(NeverCacheMixin, LoginRequiredMixin, generic.ListView):
    template_name = "joinme/event_list.html"
    context_object_name = "events"
    paginate_by = 10

    def get_queryset(self):
        return Event.objects.filter(active__exact=True).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super(AllEventsList, self).get_context_data(**kwargs)
        context["title"] = "All Events"
        return context


class ResetPassword(generic.FormView):
    template_name = "joinme/reset-pass.html"
    form_class = PasswordResetForm
    success_url = reverse_lazy("joinme:thanks")

    def get(self, request, *args, **kwargs):
        if request.user.is_active:
            return HttpResponseRedirect(reverse("joinme:settings"))
        else:
            form = self.get_form()
            return self.render_to_response(self.get_context_data(form=form))

    def post(self, request, *args, **kwargs):
        if request.user.is_active:
            return HttpResponseRedirect(reverse("joinme:settings"))
        form = self.get_form()
        email = request.POST["email"]
        if form.is_valid_email(email):
            form.send_password(email)
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class SearchList(LoginRequiredMixin, generic.ListView):
    model = Event
    template_name = "joinme/search.html"
    paginate_by = 10

    @staticmethod
    def normalize_query(query_string,
                        findterms=re.compile(r'"([^"]+)"|(\S+)').findall,
                        normspace=re.compile(r'\s{2,}').sub):
        return [normspace(' ', (t[0] or t[1]).strip())
                for t in findterms(query_string)]

    def get_query(self, query_string, search_fields):
        # Query to search for every search term
        query = None
        terms = self.normalize_query(query_string)
        for term in terms:
            # Query to search for a given term in each field
            or_query = None 
            for field_name in search_fields:
                q = Q(**{"%s__icontains" % field_name: term})
                if or_query is None:
                    or_query = q
                else:
                    or_query = or_query | q
            if query is None:
                query = or_query
            else:
                query = query | or_query
        return query

    def get_queryset(self):
        if ('q' in self.request.GET) and self.request.GET['q'].strip():
            query_string = self.request.GET['q']
            entry_query = self.get_query(query_string, ['title', 'description', ])
            return Event.objects.filter(entry_query).order_by('-pub_date')
        else:
            self.paginate_by = None

    def get_context_data(self, **kwargs):
        context = super(SearchList, self).get_context_data(**kwargs)
        context["query"] = self.request.GET['q']
        return context


class CreateEventView(LoginRequiredMixin, generic.CreateView):
    model = Event
    form_class = CreateEventForm
    template_name_suffix = "_create_form"

    def form_valid(self, form):
        form.instance.author = self.request.user.userprofile
        return super(CreateEventView, self).form_valid(form)


class EditEventView(LoginRequiredMixin, generic.UpdateView):
    model = Event
    form_class = EditEventForm
    template_name_suffix = "_create_form"

    def get_context_data(self, **kwargs):
        context = super(EditEventView, self).get_context_data(**kwargs)
        context["cat_current"] = self.get_object().category.title
        return context


class DeleteEventView(LoginRequiredMixin, generic.DeleteView):
    model = Event
    success_url = reverse_lazy("joinme:index")
