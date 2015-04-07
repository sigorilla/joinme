from django.conf.urls import patterns, url

from mipt_hack_server import views

urlpatterns = patterns('',
  url(r'^$', views.index, name='index'),
)