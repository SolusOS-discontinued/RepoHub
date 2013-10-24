from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static

from django.views.generic.simple import direct_to_template

from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns("",
    url(r"^$", direct_to_template, {"template": "homepage.html"}, name="home"),
    url(r"^buildfarm/", include ("buildfarm.urls")),
    url(r"^admin/", include(admin.site.urls)),
    url(r"^api/", include("api.urls")),
    url(r"^repo/", include ("repository.urls")),
    url(r"^account/", include("account.urls")),
    url(r"^builders/", include ("builder.urls")),
    url(r"^profiles/", include("profiles.urls")),
    url(r"^source/", include ("source.urls")),
    url(r"^manage/", include ("management.urls")),
)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
