from django.shortcuts import render, render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django import forms

from django.shortcuts import render, get_object_or_404
from django.shortcuts import redirect

from django.template.loader import render_to_string

from builder.models import Builder, BuilderMedia
from builder.manage import build_info_from_builder

from builder.tasks import update_builder_media

from django.utils import simplejson

from django.template import Context, Template

import xmlrpclib

from django.contrib.admin.views.decorators import staff_member_required

class NewBuilderForm (forms.ModelForm):
	class Meta:
		model = Builder
        
class NewBuilderMediaForm (forms.ModelForm):
	class Meta:
		model = BuilderMedia
		fields = [ 'size', 'backing_store', 'filesystem']
        
def index (request):
	''' Builders index page '''
	builders = Builder.objects.all()
	
	return render (request, 'builders/index.html', { 'not_reload': 'true', 'builders': builders, 'form': NewBuilderForm (), 'navhint': 'queue' })

@staff_member_required
def delete_builder (request, builder_id):
    builder = get_object_or_404 (Builder, id=builder_id)
    builder.delete ()
    
    return redirect ('/manage/')
    
def view_builder (request, builder_name):
    builder = Builder.objects.get (name=builder_name)

    build_info = build_info_from_builder (builder)
    init_data = { 'builder':  builder }
    try:
        builder_media = BuilderMedia.objects.get(builder=builder)
        # If we already know about this backing store, try to populate the form
        b_media = BuilderMedia.objects.get(builder=builder)
        init_data ['size'] = b_media.size
        init_data ['filesystem'] = b_media.filesystem
        init_data ['backing_store'] = b_media.backing_store    
    except:
        builder_media = None

    context = {
        'builder': builder,
        'not_reload': 'true',
        'form': NewBuilderMediaForm(initial=init_data),
        'media': builder_media,
        'build_info': build_info
    }
    
    return render (request, 'builders/view.html', context)

@staff_member_required	
def new_builder (request):
	
	if request.method == 'POST':
		# New submission
		form = NewBuilderForm (request.POST)
		rdict = { 'html': "<b>Fail</b>", 'tags': 'fail' }
		context = Context ({'form': form})
		if form.is_valid ():
			rdict = { 'html': "The new builder has been set up", 'tags': 'success' }
			form.save ()
		else:
			html = render_to_string ('builders/new.html', {'form': form})
			rdict = { 'html': html, 'tags': 'fail' }
		json = simplejson.dumps(rdict, ensure_ascii=False)

		print json
		# And send it off.
		return HttpResponse( json, content_type='application/json')
			
	else:
		form = NewBuilderForm ()
	
	context = {'form': form }
	
	return render (request, 'builders/new.html', context)

@staff_member_required
def media_edit (request, builder_name):
    
    
    builder = Builder.objects.get (name=builder_name)

    if request.method == 'POST':
        # New submission
        form = NewBuilderMediaForm (request.POST)
        rdict = { 'html': "<b>Fail</b>", 'tags': 'fail' }
        context = Context ({'form': form})
        if form.is_valid ():
            rdict = { 'html': "The backing media update has been scheduled", 'tags': 'success' }
            model = form.save (commit=False)
            update_builder_media.delay (builder, model)
        else:
            html = render_to_string ('builders/new_edit_media.html', {'form': form})
            rdict = { 'html': html, 'tags': 'fail' }
        json = simplejson.dumps(rdict, ensure_ascii=False)

        # And send it off.
        return HttpResponse( json, content_type='application/json')
            
    else:
        form = NewBuilderForm ()

    context = {'form': form }
    return render (request, 'builders/new.html', context)    
