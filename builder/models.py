from django.contrib import admin
from django.db import models

from repository.models import Repository

ARCH_CHOICES = (
	('32', 'i686'),
	('64', 'x86_64'),
)

BACKING_STORE_CHOICES = (
    ('32', 'SolusOS 2 32-bit'),
)

FILESYSTEM_CHOICES = (
    ('btrfs', 'btrfs'),
    ('ext2', 'ext2'),
    ('ext3', 'ext3'),
    ('ext4', 'ext4'),
)

# Create your models here.
class Builder(models.Model):
	
	name = models.CharField (max_length=15, verbose_name="Builder name")
	address = models.GenericIPAddressField (verbose_name="IP Address")
	port = models.IntegerField (verbose_name="Port number")
		
	architecture = models.CharField (max_length=2, choices=ARCH_CHOICES, default='32')
	
	repo = models.ForeignKey (Repository)
		
	def __unicode__(self):
		return "%s %s" % (self.name, "")

class BuilderMedia (models.Model):
    
    size = models.IntegerField (verbose_name="Backing store size (MB)")
    backing_store = models.CharField (max_length=2, choices=BACKING_STORE_CHOICES, default='32', verbose_name="Backing system")
    
    filesystem = models.CharField (max_length=4, choices=FILESYSTEM_CHOICES, default='ext4')
    
    builder = models.ForeignKey (Builder)
    
admin.site.register (Builder)
admin.site.register (BuilderMedia)
