from django.conf.urls import patterns, url

from builder import views

urlpatterns = patterns('',
	url(r'^$', views.index, name='builder_index'),
    url(r'^add/$', views.new_builder, name='new_builder'),
    url(r'^view/(?P<builder_name>[^/]+)', views.view_builder, name='view_builder'),
    url(r'^media/(?P<builder_name>[^/]+)', views.media_edit, name='media_edit'),   
    url(r'^delete_builder/(?P<builder_id>\d+)/$', views.delete_builder, name='delete_builder'),
)
