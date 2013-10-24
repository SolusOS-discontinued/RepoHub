from django.conf.urls import patterns, url

from source import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^package/(?P<package_name>[^/]+)', views.view_package, name='view_package'),
)
