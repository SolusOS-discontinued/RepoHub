from django.http import HttpResponse
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string

from repository.models import SourceRepository, Repository, PisiPackage, PackageDependency, BinMan

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed

from django import forms

from django.utils import simplejson

from django.template import Context, Template

import urllib2
from xml.dom.minidom import parse as parse_xml
from django.db import transaction

import django.contrib

from django.contrib.admin.views.decorators import staff_member_required

from repository.tasks import rebuild_repo, import_source_repo, create_deltas_binman, process_incoming_binman

from django.contrib import messages

class NewSourceRepoForm (forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    class Meta:
        model = SourceRepository
        fields = ( 'name', 'description', 'url', 'repo_type', 'username', 'password')
        
class NewRepoForm (forms.ModelForm):
	class Meta:
		model = Repository
		fields = ( 'name', 'url', 'repo_type')

class NewBinManform (forms.ModelForm):
    rsync_password = forms.CharField(widget=forms.PasswordInput())
    class Meta:
        model = BinMan
        fields = ( 'name', 'hostname', 'control_port', 'rsync_username', 'rsync_password', 'rsync_target')

@staff_member_required
def delete_binary_repo (request, repo_id):
    repo = get_object_or_404 (Repository, id=repo_id)
    repo.delete ()
    
    return redirect ('/manage/')

@staff_member_required
def delete_source_repo (request, repo_id):
    repo = get_object_or_404 (SourceRepository, id=repo_id)
    repo.delete ()
    
    return redirect ('/manage/')

@staff_member_required
def delete_binman (request, binman_id):
    binman = get_object_or_404 (BinMan, id=binman_id)
    binman.delete ()
    
    return redirect ('/manage/')
    
''' Index page of the repo '''
def index (request, component=None):
	if (component is not None):
		packages = PisiPackage.objects.filter(component=component).order_by("name")
	else:
		packages = PisiPackage.objects.all().order_by("name")

	paginator = Paginator (packages, 15)

	page = request.GET.get("page")
	try:
		packages = paginator.page(page)
	except PageNotAnInteger:
		packages = paginator.page (1)
	except EmptyPage:
		packages = paginator.page (paginator.num_pages)
	
	if component is not None:
		context = { 'packages' : packages, "navhint": "repo", 'component': component }
	else:
		context = { 'packages' : packages, "navhint": "repo"}
	return render (request, "repository/index.html", context)

''' View/edit repos themselves '''
def index_repos (request):
    repo = Repository.objects.all()
    
    paginator = Paginator (repo, 15)
    
    page = request.GET.get("page")
    try:
        repo = paginator.page (page)
    except PageNotAnInteger:
        repo = paginator.page (1)
    except EmptyPage:
        repo = paginator.page (paginator.num_pages)
        
    context = { 'repos' : repo , 'navhint' : 'manage' }
    
    return render (request, "repository/index_repos.html", context)
    
''' View a package '''
def view_package (request, package_name):
	package = PisiPackage.objects.get(name=package_name)
	deps = PackageDependency.objects.filter(package=package)
	print len(deps)
	context = { 'package': package, 'dependencies': deps, 'navhint': 'repo'}
	return render (request, "repository/view_package.html", context)

''' Stream of updates '''
def update_stream (request):
	packages = PisiPackage.objects.all().order_by("-date_updated")[:10]
	context = { 'packages': packages, 'navhint': 'repo'}
	
	return render (request, "repository/stream.html", context)
	
	
''' Search for a package by name '''
def search_package (request):
	found_count = 0
	if 'q' in request.GET:
		query_string = request.GET['q']
		packages = PisiPackage.objects.filter(name__icontains=query_string)
		found_count = len(packages)

		paginator = Paginator (packages, 15)

		page = request.GET.get("page")
		try:
			packages = paginator.page(page)
		except PageNotAnInteger:
			packages = paginator.page (1)
		except EmptyPage:
			packages = paginator.page (paginator.num_pages)
		
		context = { 'packages': packages, 'navhint': 'repo', 'found': found_count, 'search_term': query_string }
		return render (request, "repository/search.html", context)
	else:
		context = { 'found': found_count, 'search_term': query_string}
		return render (request, "repository/search.html", context)

@staff_member_required
def reload_repo (request, repo_id):
    repo = get_object_or_404 (Repository, id=repo_id)
    if repo.building:
        # Repo is already reloading.
        # Should raise an error for the UI somewhere.
        messages.add_message (request, messages.ERROR, "The \"%s\" repository is already being reloaded" % repo.name)
        return redirect ('/manage/')
    messages.info (request, "Reloading \"%s\" repository" % repo.name)
    repo.building = True
    repo.save ()
    
    rebuild_repo.delay (repo_id)
    
    # Go back to manage page, we'll rebuild the repo in the background
    return redirect ('/manage/')

@staff_member_required
def process_incoming (request, binman_id):
    binman = get_object_or_404 (BinMan, id=binman_id)
    messages.info (request, "Asking \"%s\" BinMan to process incoming packages" % binman.name)
    
    process_incoming_binman.delay (binman_id)
    
    return redirect ('/manage/')

@staff_member_required
def process_incoming_deltas (request, binman_id):
    binman = get_object_or_404 (BinMan, id=binman_id)
    messages.info (request, "Asking \"%s\" BinMan to produce all deltas" % binman.name)
    
    create_deltas_binman.delay (binman_id)
    
    return redirect ('/manage/')
        
@staff_member_required
def reload_source_repo (request, repo_id):
    repo = get_object_or_404 (SourceRepository, id=repo_id)
    if repo.loading:
        # Repo is already reloading.
        # Should raise an error for the UI somewhere.
        messages.add_message (request, messages.ERROR, "The \"%s\" repository is already being reloaded" % repo.name)
        return redirect ('/manage/')
    messages.info (request, "Reloading \"%s\" repository" % repo.name)
    repo.loading = True
    repo.loading_status = "Resolving"
    repo.save ()
    
    import_source_repo.delay (repo_id)
    
    # Go back to manage page, we'll rebuild the repo in the background
    return redirect ('/manage/')

@staff_member_required        
def new_repo(request):
	
	if request.method == 'POST':
		# New submission
		form = NewRepoForm (request.POST)
		rdict = { 'html': "<b>Fail</b>", 'tags': 'fail' }
		context = Context ({'form_repo': form})
		if form.is_valid ():
			rdict = { 'html': "The new repository has been set up", 'tags': 'success' }
			form.save ()
		else:
			html = render_to_string ('repository/new_repo.html', {'form_repo': form})
			rdict = { 'html': html, 'tags': 'fail' }
		json = simplejson.dumps(rdict, ensure_ascii=False)

		print json
		# And send it off.
		return HttpResponse( json, content_type='application/json')
			
	else:
		form = NewRepoForm ()
	
	context = {'form': form }
	
	return render (request, 'builders/new.html', context)

@staff_member_required
def new_source_repo(request):

    if request.method == 'POST':
        # New submission
        form = NewSourceRepoForm (request.POST)
        rdict = { 'html': "<b>Fail</b>", 'tags': 'fail' }
        context = Context ({'form_repo': form})
        if form.is_valid ():
            rdict = { 'html': "The new repository has been set up", 'tags': 'success' }
            model = form.save (commit=False)
            model.loading = True
            model.save ()
            import_source_repo.delay (model.id)
        else:
            html = render_to_string ('repository/new_source_repo.html', {'form_source': form})
            rdict = { 'html': html, 'tags': 'fail' }
        json = simplejson.dumps(rdict, ensure_ascii=False)

        return HttpResponse( json, content_type='application/json')
            
    else:
        form = NewRepoForm ()

    context = {'form': form }

    return render (request, 'repository/new_source_repo.html', context)

@staff_member_required
def new_binman(request):

    if request.method == 'POST':
        # New submission
        form = NewBinManform (request.POST)
        rdict = { 'html': "<b>Fail</b>", 'tags': 'fail' }
        context = Context ({'form_binman': form})
        if form.is_valid ():
            rdict = { 'html': "The BinMan has been set up", 'tags': 'success' }
            model = form.save (commit=False)
            model.save ()
        else:
            html = render_to_string ('repository/new_binman.html', {'form_binman': form})
            rdict = { 'html': html, 'tags': 'fail' }
        json = simplejson.dumps(rdict, ensure_ascii=False)

        return HttpResponse( json, content_type='application/json')
            
    else:
        form = NewRepoForm ()

    context = {'form': form }

    return render (request, 'repository/new_binman.html', context)
            
class UpdateFeed(Feed):
	title = "Last updated packages"
	link = "/repo/stream/"
	description = "Latest updates to the repository"
	
	item_copyright = "Copyright (C) 2013 SolusOS"
	
	feed_copyright = item_copyright
	
	def items(self):
		return PisiPackage.objects.all().order_by("-date_updated")[:20]
		
	def item_link(self, item):
		return "/repo/package/%s" % item.name
			
	def item_description (self, item):
		return item.comment
	
	def item_author_name (self, item):
		return item.maintainer_name
		
	def item_author_email (self, item):
		return item.maintainer_email
