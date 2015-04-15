# -*- coding: utf-8 -*-
import urllib2
import json

from django.conf import settings as glob_setting
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import JsonResponse, HttpResponseRedirect

from joinme.models import UserProfile
from joinme.requests import get_data_vk


VK_API_AUTH = "https://oauth.vk.com/access_token"


def get_access_token(code, host="127.0.0.1:8000"):
    url = "%s?client_id=%s&client_secret=%s&code=%s&redirect_uri=http://%s%s" % (
        VK_API_AUTH,
        glob_setting.VK_API_ID,
        glob_setting.VK_API_SECRET,
        code,
        host,
        reverse("joinme:vk-auth"))
    response = urllib2.urlopen(url).read()
    data = json.loads(response)
    return data


# TODO: create handlers of error in more pretty view
def vk_auth(request):
    if request.GET:
        if ("code" in request.GET) and request.GET["code"].strip():
            code = request.GET["code"]
            host = request.get_host()
            data = get_access_token(code, host)
            if "access_token" in data:
                userprofile = UserProfile.objects.get(pk=request.user.userprofile.id)
                userprofile.vk_user_id = data["user_id"]
                userprofile.vk_access_token = data["access_token"]
                userprofile.vk_expires_in = data["expires_in"]
                userprofile.vk_email = data["email"]
                userdata = get_data_vk("users.get",
                                       userprofile.vk_access_token,
                                       users_ids=userprofile.vk_user_id,
                                       fields="photo_200")
                userprofile.vk_photo_200 = userdata["response"][0]["photo_200"]
                userprofile.save()
                if not request.user.first_name or not request.user.last_name:
                    user = User.objects.get(pk=request.user.id)
                    if not user.first_name:
                        user.first_name = userdata["response"][0]["first_name"]
                    if not user.last_name:
                        user.last_name = userdata["response"][0]["last_name"]
                    user.save()
                return HttpResponseRedirect(redirect_to=reverse("joinme:settings"))
            else:
                return JsonResponse({"error": data["error_description"]})
        else:
            return JsonResponse({"error": "No field code."})
    else:
        return JsonResponse({"error": "It should be GET request."})


def vk_auth_delete(request):
    if request.user.is_active:
        user = UserProfile.objects.get(user__id=request.user.id)
        user.vk_user_id = "0"
        user.save()
    return HttpResponseRedirect(redirect_to=reverse("joinme:settings"))
