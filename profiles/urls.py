from django.conf.urls import patterns, url

from profiles import views

urlpatterns = patterns('',
    url(r'^(?P<name>\w+)$', views.show_user, name='show_user'),
)
