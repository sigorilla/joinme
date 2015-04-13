import json
import urllib2

VK_API_METHOD = "https://api.vk.com/method/"


def get_data_vk(method, access_token, **kwargs):
    url = "%s%s?access_token=%s&v=5.29&lang=en" % (VK_API_METHOD, method, access_token)
    for key, value in kwargs.iteritems():
        url += "&%s=%s" % (key, value)
    response = urllib2.urlopen(url).read()
    data = json.loads(response)
    return data
