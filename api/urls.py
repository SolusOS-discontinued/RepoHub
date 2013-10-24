from django.conf.urls.defaults import *
from piston.resource import Resource
from api.handlers import QueueHandler, QueueUpdateHandler
from piston.authentication import HttpBasicAuthentication

auth = HttpBasicAuthentication(realm="Internal API")

queue_get_handler = Resource (QueueHandler, authentication=auth)
queue_update_handler = Resource (QueueUpdateHandler, authentication=auth)

urlpatterns = patterns('',
   url(r'^queue/(?P<queue_id>\d+)/', queue_get_handler),
   url(r'^queuestatus/(?P<queue_id>\d+)/', queue_update_handler),
)
