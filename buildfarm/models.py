from django.db import models
from django.contrib import admin

from builder.models import Builder
from repository.models import SourceRepository, BinMan

class Queue (models.Model):
    name = models.CharField (max_length=200)
    current = models.IntegerField (null=True)
    current_package_name = models.CharField (max_length=200,null=True)
    architecture = models.CharField (max_length=10, default="i686",null=True)
    length = models.IntegerField (null=True)

    builder = models.ForeignKey (Builder)
    
    source_repo = models.ForeignKey (SourceRepository)
    
    binman = models.ForeignKey (BinMan, verbose_name="Target BinMan")
    
    busy = models.NullBooleanField (default=False)
    
    busy_string = models.CharField (null=True, blank=True, max_length=100)
    
    sandboxed = models.BooleanField (default=True)
    
    def __unicode__(self):
        return "%s - %s" %  (self.name, self.architecture)

# Represents a Package
class Package (models.Model):
    name = models.CharField (max_length=200)
    version = models.CharField (max_length=200)
    build_status = models.CharField (max_length=200, default="pending")

    queue = models.ForeignKey (Queue, null=True)

    spec_uri = models.CharField (max_length=200)

    build_log = models.TextField (blank=True)

    def __unicode__(self):
        return "%s - %s" % (self.name, self.version)


							
# Hook up the admin interface
admin.site.register (Package)
admin.site.register (Queue)
