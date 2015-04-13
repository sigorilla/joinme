# -*- coding: utf-8 -*-
import urllib2
import json

from django.conf import settings as glob_setting
from django.core.urlresolvers import reverse
from django.http import JsonResponse, HttpResponseRedirect

from joinme.models import UserProfile


VK_API_URL = "https://oauth.vk.com/access_token"


def get_access_token(code, host="127.0.0.1:8000"):
    url = "%s?client_id=%s&client_secret=%s&code=%s&redirect_uri=http://%s%s" % (
        VK_API_URL,
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
                user = UserProfile.objects.get(pk=request.user.userprofile.id)
                user.vk_user_id = data["user_id"]
                user.vk_access_token = data["access_token"]
                user.vk_expires_in = data["expires_in"]
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
