from django.db import models
from django.contrib import admin

import django

from repository.models import SourceRepository

# Create your models here.
class SourcePackage (models.Model):
	name = models.CharField (max_length=200)
	version = models.CharField (max_length=30)
	maintainer_name = models.CharField (max_length=100)
	maintainer_email = models.CharField (max_length=100)
	component = models.CharField (max_length=100)
	
	summary = models.CharField(max_length=200)
	description = models.CharField(max_length=1000)
	
	release = models.CharField (max_length=10)
	
	known_user = models.ForeignKey (django.contrib.auth.models.User, null=True)
	source_uri = models.CharField (max_length=200)
	
	repository = models.ForeignKey (SourceRepository)
	
	def __unicode__(self):
		return "%s - %s" % (self.name, self.summary)	

class SourceUpdate (models.Model):
	name = models.CharField (max_length=200)
	version = models.CharField (max_length=30)
	release = models.CharField (max_length=10)
	comment = models.TextField ()
	email = models.CharField (max_length=200)
	
	known_user = models.ForeignKey (django.contrib.auth.models.User, null=True)
	# Each SourceUpdate must be associated with a SourcePackage
	package = models.ForeignKey (SourcePackage)
	
	def __unicode__(self):
		return "%s %s - release %s" % (self.package.name, self.version, self.release)

class SourceArchive (models.Model):
	file_type = models.CharField (max_length=10)
	target = models.CharField (max_length=100, null=True)
	sha1sum = models.CharField (max_length=150)
	uri = models.CharField (max_length=200)
	
	# Linked SourcePackage
	package = models.ForeignKey (SourcePackage)
	
	def __unicode__(self):
		return "%s : %s" % (self.package.name, self.uri)

class BuildDependency (models.Model):
    '''
    Represents build-dependencies for source packages
    '''
    name = models.CharField (max_length=200)
    
    source_package = models.ForeignKey (SourcePackage)
    
    def __unicode__(self):
        return "%s depends on %s" % (self.source_package.name, self.name)
    	
admin.site.register (SourcePackage)
admin.site.register (SourceUpdate)
admin.site.register (SourceArchive)
admin.site.register (BuildDependency)
