# Create your views here.
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404

from django.contrib.auth.models import User

from repository.models import PisiPackage

def show_user (request, name=None):
	user = get_object_or_404 (User, username=name)
	context = { 'user' : user }
	
	packages = None
	try:
		packages = PisiPackage.objects.filter(known_user=user).order_by("-date_updated")
		count = len(packages)
		total_packages = len(PisiPackage.objects.all())
		
		pct = float (float(count) / (total_packages)) * 100

		packages = packages[:7]
		context = {  'user': user, 'package_count': count, 'package_ratio': pct, 'packages': packages}

	except Exception, e:
		print e
		pass
		
	return render (request, "profiles/individ.html", context)
