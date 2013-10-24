from piston.handler import BaseHandler
from buildfarm.models import Package, Queue
from piston.utils import rc
from builder.models import Builder
from source.models import SourcePackage

class PackageHandler (BaseHandler):
	allowed_methods = ('GET',)
	model = Package
	
	def read (self, request, name=None):
		""" Return a given package or all """
		base = Package.objects
		if name:
			return base.get(name=name)
		else:
			return base.all ()

class QueueHandler (BaseHandler):
    allowed_methods = ('GET', 'PUT',)
    model = Package
    exclude = ('queue','id',)

    def read (self, request, queue_id):
        try:
            queue = Queue.objects.get (id=queue_id)
            builder = queue.builder

            packages =  Package.objects.filter (queue=queue)
            return packages
        except:
            pass
        return rc.NOT_FOUND
        
    def update (self, request, queue_id):
        try:
            data = request.data
            queue = Queue.objects.get (id=queue_id)
            builder = queue.builder
            package = Package.objects.get (queue=queue, name=data['name'])
            package.build_status = data['build_status']
            package.save ()
        except Exception, e:
            print e
        #return rc.OK

class QueueUpdateHandler (BaseHandler):
    allowed_methods = ('PUT',)
    model = Queue
	
    def update (self, request, queue_id):
        print "Requested queue update"
        try:
            queue = Queue.objects.get (id=queue_id)
            builder = queue.builder
            
            data = request.data
            queue.current = int (data['current'])
            queue.current_package_name = data['package_name']
            queue.length = data['length']
            queue.save ()
        except Exception, e:
            print e
					
class PackageAddHandler (BaseHandler):
	allowed_methods = ('POST',)
	model = Package
	
	def create(self, request, queuename=None, arch=None):
		""" Add packages to the queue """
		Package.objects.all().delete()
		print queuename
		print arch
		queue = None
		try:
			queue = Queue.objects.get(name=queuename, architecture=arch)
		except Exception, e:
			print e
			pass
		if queue == None:
			# Create a new queue
			queue = Queue (name=queuename, architecture=arch, current_package_name="", current=0)
			queue.save ()
		for item in request.data:
			pkg = Package(name=item['name'], version=item['version'], queue=queue)
			pkg.save ()
			
		return rc.CREATED

