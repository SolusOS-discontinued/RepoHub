from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django import forms

from builder.models import Builder
from builder.views import NewBuilderForm
from repository.models import Repository, SourceRepository, BinMan, BinManInfo

from builder.manage import build_info_from_builder
from repository.manage import binman_info_from_binman

from buildfarm.models import Queue
from buildfarm.views import NewQueueForm
from repository.views import NewRepoForm, NewSourceRepoForm, NewBinManform

from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def index (request):
    builders = Builder.objects.all ()
    queues = Queue.objects.all ()
    repos = Repository.objects.all ()
    s_repos = SourceRepository.objects.all ()
    repo_list = []
    binmen = BinMan.objects.all ()
    for repo in [repos, s_repos]:
        for item in repo:
            repo_list.append (item)
    
    
    for builder in builders:
        try:
            build_info = build_info_from_builder (builder)
            builder.build_info = build_info
            print build_info
        except Exception, e:
            print e
            pass
            
    for binman in binmen:
        binman.bin_info = binman_info_from_binman (binman.id)
        
    context = {
        'navhint' : 'manage' ,
        'not_reload':  'true',
        'form': NewBuilderForm(),
        'builders': builders,
        'queues': queues,
        'binmen': binmen,
        'repos': repo_list,
        'form_queue': NewQueueForm(),
        'form_repo': NewRepoForm(),
        'form_source': NewSourceRepoForm(),
        'form_binman': NewBinManform(),
        }
    return render (request, 'management/index.html', context)
