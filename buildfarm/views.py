# Patchless XMLRPC Service for Django
# Kind of hacky, and stolen from Crast on irc.freenode.net:#django
# Self documents as well, so if you call it from outside of an XML-RPC Client
# it tells you about itself and its methods
#
# Brendan W. McAdams <brendan.mcadams@thewintergrp.com>

# SimpleXMLRPCDispatcher lets us register xml-rpc calls w/o
# running a full XMLRPC Server.  It's up to us to dispatch data

from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404

from buildfarm.models import Package, Queue

from repository.models import Repository, PisiPackage

from source.models import SourcePackage

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

import xmlrpclib

from django.template.loader import render_to_string

from django.utils import simplejson

from django.template import Context, Template

from django import forms

from django.utils import simplejson

from django.db import transaction

from django.shortcuts import redirect

from django.contrib.admin.views.decorators import staff_member_required

from django.contrib import messages

from buildfarm.tasks import build_all_in_queue 

class NewQueueForm (forms.ModelForm):
	class Meta:
		model = Queue
		fields = ( 'name', 'builder', 'source_repo', 'binman', 'sandboxed')

def site_index (request):
	queues = Queue.objects.all ()
	
	context = { 'queues': queues, 'navhint': 'queue', 'not_reload': 'true', 'form' : NewQueueForm() }
	
	return render (request, "buildfarm/site_index.html", context)

def package_progress_json (request, queue_id):
	rdict = {}
	q = Queue.objects.get(id=queue_id)
	
	packages = Package.objects.filter(queue=q)
	pct =float ( float(q.current) / q.length ) * 100
	
	rdict = { 'percent' : pct, 'total': q.length, 'current': q.current, 'name_current': q.current_package_name }
	json = simplejson.dumps(rdict, ensure_ascii=False)

	return HttpResponse( json, content_type='application/json')	

@staff_member_required
def delete_from_queue (request, package_id):
    pkg = get_object_or_404 (Package, id=package_id)
    q_id = pkg.queue.id
    
    pkg.delete ()
    return redirect ('/buildfarm/queue/%d/' % q_id)

@staff_member_required
def delete_queue (request, queue_id):
    queue = get_object_or_404 (Queue, id=queue_id)
    queue.delete ()
    
    return redirect ('/manage/')
    
@staff_member_required
def new_queue (request):
	
	if request.method == 'POST':
		# New submission
		form = NewQueueForm (request.POST)
		rdict = { 'html': "<b>Fail</b>", 'tags': 'fail' }
		context = Context ({'form': form})
		if form.is_valid ():
			rdict = { 'html': "The new queue has been set up", 'tags': 'success' }
			model = form.save (commit=False)
			model.current = 0
			model.length = 0
			model.current_package_name = ""
			model.save ()

		else:
			html = render_to_string ('buildfarm/new_queue.html', {'form_queue': form})
			rdict = { 'html': html, 'tags': 'fail' }
		json = simplejson.dumps(rdict, ensure_ascii=False)

		print json
		# And send it off.
		return HttpResponse( json, content_type='application/json')
			
	else:
		form = NewQueueForm ()
	
	context = {'form': form }
	
	return render (request, 'buildfarm/new_queue.html', context)
			
def queue_index(request, queue_id=None):
	q = get_object_or_404 (Queue, id=queue_id)

	packages = Package.objects.filter(queue=q).order_by('build_status')
	paginator = Paginator (packages, 15)

	pkg_count = q.length

	if (pkg_count > 0):
		pct =float ( float(q.current) / q.length ) * 100
	else:
		pct = 0
			
	page = request.GET.get("page")
	try:
		packages = paginator.page(page)
	except PageNotAnInteger:
		packages = paginator.page (1)
	except EmptyPage:
		packages = paginator.page (paginator.num_pages)
	context = {'navhint': 'queue', 'queue': q, 'package_list': packages, 'total_packages': q.length, 'current_package': q.current, 'total_pct': pct, 'current_package_name': q.current_package_name}
		
	return render (request, "buildfarm/index.html", context)

@staff_member_required
def build_queue (request, queue_id):
    queue = Queue.objects.get (id=queue_id)
    
    messages.info (request, "Starting build of \"%s\" queue" % queue.name)
    
    build_all_in_queue.delay (queue_id)
    
    return redirect ('/manage/')
    
@staff_member_required
def populate_queue (request, queue_id):
    q = Queue.objects.get(id=queue_id)

    packages = SourcePackage.objects.filter (repository=q.source_repo)

    failList = list ()
    for package in packages:
        binaries = PisiPackage.objects.filter(source_name=package.name)
        if len(binaries) == 0:
            # We have no binaries
            print "New package for source: %s" % (package.name)
            failList.append (package)
        else:
            for package2 in binaries:
                if package2.release != package.release:
                    print "Newer release for: %s" % package2.name
                    failList.append (package)
                    break

        try:
            binary = Package.objects.get(queue=q, name=package.name)
            failList.remove (package)
        except:
            pass
    with transaction.commit_on_success():		
        for fail in failList:
            pkg = Package ()
            pkg.name = fail.name
            pkg.version = fail.version
            pkg.build_status = "pending"
            pkg.queue = q
            pkg.spec_uri = fail.source_uri
            pkg.save ()
        
    return redirect ("/buildfarm/queue/%d" % q.id)		
	
