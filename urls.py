from django.conf.urls import patterns, url

from mipt_hack_server import views

urlpatterns = patterns("",
  url(r"^$", views.index, name="index"),
  url(r"^confirm/(?P<activation_key>[a-z0-9]{,32})/$", views.confirm, name="confirm-key"),
  url(r"^logout/$", "django.contrib.auth.views.logout", {"next_page": "/test/"}),
)