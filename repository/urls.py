from django.conf.urls import patterns, url

from repository import views
from repository.views import UpdateFeed

urlpatterns = patterns('',
    url(r'^$', views.index, name='repo_index'),
    url(r'^(?P<component>[^/]+)$', views.index, name='repo_index_component'),
    url(r'^package/(?P<package_name>[^/]+)', views.view_package, name='view_binary_package'),
    url(r'^search/$', views.search_package, name='search_package'),
    url(r'^stream/$', views.update_stream, name='update_stream'),
    url(r'^addrepo/$', views.new_repo, name='new_binary_repo'),
    url(r'^addsourcerepo/$', views.new_source_repo, name='new_source_repo'),
    url(r'^addbinman/$', views.new_binman, name='new_binman'),            
    url(r'^index/$', views.index_repos, name='index_repos'),
    url(r'^reload/(?P<repo_id>[^/]+)/$', views.reload_repo, name='reload_repo'),
    url(r'^process_incoming/(?P<binman_id>[^/]+)/$', views.process_incoming, name='binman_process_incoming'),
    url(r'^process_deltas/(?P<binman_id>[^/]+)/$', views.process_incoming_deltas, name='binman_process_deltas'),
    url(r'^reload_source/(?P<repo_id>[^/]+)/$', views.reload_source_repo, name='reload_source_repo'),
    url(r'^delete_source_repo/(?P<repo_id>[^/]+)/$', views.delete_source_repo, name='delete_source_repo'),
    url(r'^delete_binary_repo/(?P<repo_id>[^/]+)/$', views.delete_binary_repo, name='delete_binary_repo'),
    url(r'^delete_binman/(?P<binman_id>[^/]+)/$', views.delete_binman, name='delete_binman'),
    url(r'^stream/rss/$', UpdateFeed())
)
