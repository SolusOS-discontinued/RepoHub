from django.http import HttpResponse
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404

from source.models import SourcePackage, SourceArchive, SourceUpdate

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def index (request):
	packages = SourcePackage.objects.all ().order_by ("name")
	paginator = Paginator (packages, 15)

	page = request.GET.get("page")
	try:
		packages = paginator.page(page)
	except PageNotAnInteger:
		packages = paginator.page (1)
	except EmptyPage:
		packages = paginator.page (paginator.num_pages)
			
	context = { 'packages': packages, 'navhint' : 'repo' }
	
	return render (request, 'source/index.html', context)

def view_package (request, package_name):
	package = get_object_or_404 (SourcePackage, name=package_name)
	archives = SourceArchive.objects.filter(package=package)
	updates = SourceUpdate.objects.filter (package=package)
	
	context = { 'package' : package, 'updates': updates, 'archives': archives, 'navhint' : 'repo' }
	
	return render (request, 'source/view_package.html', context)
	
