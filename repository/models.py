from django.db import models
from django.contrib import admin

import django

REPO_CHOICES = (
	('B', 'Binary'),
	('S', 'Source'),
)

VCS_CHOICES = (
    ('G', 'Git'),
    ('M', 'Mercurial'),
)

class BinManInfo:
    '''
    Info object, used to represent live BinMan instances
    '''
    pending_packages = 0
    active = False
    
class SourceRepository (models.Model):
    '''
    A source repo, which must be controlled by a VCS, i.e. git or mercurial
    '''
    
    name = models.CharField (max_length=200)
    description = models.TextField ()
    url = models.URLField ()

    repo_type = models.CharField (max_length=2, choices=VCS_CHOICES, default='M')
    
    username = models.CharField (max_length=50, blank=True)
    password = models.CharField (max_length=50, blank=True)
    
    loading = models.BooleanField (default=False)
    loading_status = models.CharField(max_length=100, blank=True)
     
    def __unicode__(self):
        return "%s repository: %s" % (("Git" if self.repo_type == 'G' else "Mercurial"), self.name)
            
class Repository (models.Model):
    name = models.CharField (max_length=200)
    description = models.TextField ()
    url = models.URLField ()

    repo_type = models.CharField (max_length=2, choices=REPO_CHOICES, default='B')
    
    building = models.BooleanField (default=False)
    
    def __unicode__(self):
        return self.name

class PisiPackage (models.Model):
    name = models.CharField (max_length=200)
    version = models.CharField (max_length=30)
    maintainer_name = models.CharField (max_length=100)
    maintainer_email = models.CharField (max_length=100)
    component = models.CharField (max_length=100)
    release = models.CharField (max_length=100)

    summary = models.CharField(max_length=200)
    description = models.CharField(max_length=1000)

    source_name = models.CharField(max_length=200)

    known_user = models.ForeignKey (django.contrib.auth.models.User, null=True)

    date_updated = models.DateField ()

    repository = models.ForeignKey (Repository)

    comment = models.TextField ()

    def __unicode__(self):
        return "%s - %s" % (self.name, self.version)

class PackageDependency (models.Model):
	name = models.CharField (max_length=200)
	package = models.ForeignKey (PisiPackage)
	version = models.CharField (max_length=100, null=True)
	relation = models.CharField (max_length=10, null=True)
	
	def __unicode__(self):
		return "%s depends on %s" % (self.package.name, self.name)

class BinMan (models.Model):
    '''
    Represents a BinMan instance
    '''
    name = models.CharField (max_length=200)
    
    hostname = models.CharField (max_length=100)
    control_port = models.IntegerField ()
    
    rsync_username = models.CharField (max_length=50)
    rsync_password = models.CharField (max_length=50)
    rsync_target = models.CharField (max_length=100)
    
    busy = models.NullBooleanField (default=False)
    
    def __unicode__(self):
        return "%s (%s)" % (self.name, self.hostname)

admin.site.register (PisiPackage)
admin.site.register (PackageDependency)
admin.site.register (BinMan)

