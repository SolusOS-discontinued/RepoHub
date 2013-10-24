from django.conf.urls import patterns, url

from buildfarm import views

urlpatterns = patterns('',
    url(r'^$', views.site_index, name='index'),
    url(r'^queue/(?P<queue_id>\d+)/$', views.queue_index, name='queue_index'),
    url(r'^delete_from_queue/(?P<package_id>\d+)/$', views.delete_from_queue, name='delete_queue_item'),
    url(r'^delete_queue/(?P<queue_id>\d+)/$', views.delete_queue, name='delete_queue'),
    url(r'^queuejson/(?P<queue_id>\d+)/$', views.package_progress_json, name='queue_progress_json'),
    url(r'build/(?P<queue_id>\d+)/$', views.build_queue, name='build_queue'),
    url(r'^addqueue/$', views.new_queue, name='new_queue'),
    url(r'^pop_queue/(?P<queue_id>\d+)/$', views.populate_queue, name='pop_queue'),
)
