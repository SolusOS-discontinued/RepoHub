import celery

from buildfarm.models import Queue, Package

import xmlrpclib

from django.conf import settings

import os
import os.path
import commands

from django.utils.encoding import smart_text

@celery.task
def fix_frozen_queues ():
    '''
    On occassion, long running queues freeze the 'busy'
    status in the DB, meaning we never sync logs or
    packages, whether they succeeded or not
    '''
    for queue in Queue.objects.all():
        if not queue.busy:
            continue
        # We only deal with locked busy queues
        packages = Package.objects.filter(queue=queue)
        bail = False
        hasFailures = False
        acceptables = ["built","fail"]
        for package in packages:
            if not package.build_status in acceptables:
                print package.build_status
                bail = True
            if package.build_status != "built":
                hasFailures = True
        if bail:
            return False
        # Got this far, we could have a possible queue freeze.
        builder = queue.builder
        try:
            prox = xmlrpclib.ServerProxy("http://%s:%s" % (builder.address, builder.port))
            if not prox.worker_busy ():
                # Worker is idle, force a resync
                prox.sync_logs (settings.RSYNC_LOG_HOST, settings.RSYNC_LOG_TARGET, settings.RSYNC_LOG_USERNAME, settings.RSYNC_LOG_PASSWORD)
                if not hasFailures:
                    # Sync packages.
                    binman = queue.binman
                    result = prox.sync_packages (binman.hostname, binman.rsync_target, binman.rsync_username, binman.rsync_password)

                    for package in packages:
                        naming = "%s-%s.txt" % (package.name, package.version)
                        fpath = os.path.join (settings.LOG_BASE_DIRECTORY, naming)
                        log = commands.getoutput ("tail -n 30 %s" % fpath).decode ("latin-1")
                        package.build_log = smart_text(log, encoding='utf-8', strings_only=False, errors='strict')
                        package.save ()
                queue.busy = False
                queue.save ()
        except Exception, e:
            print e
            return False
    return True
                            
@celery.task
def build_all_in_queue (queue_id):
    queue = Queue.objects.get (id=queue_id)
    if queue.busy:
        return False
    queue.busy = True
    queue.save ()
    builder = queue.builder
    repo = queue.source_repo
    try:
        prox = xmlrpclib.ServerProxy("http://%s:%s" % (builder.address, builder.port))
        # Firstly, let's load the source repo.
        queue.busy_string = "Adding source repo"
        queue.save ()
        VCS = 'mercurial' if repo.repo_type == 'M' else 'git'
        if repo.username != "" and repo.username != "":
            # Add the source repo using credentials.
            prox.add_source_repo (repo.url, VCS, repo.username, repo.password)
        else:
            prox.add_source_repo (repo.url, VCS)
        
        # Also helps if the repo is up to date ^^
        binary_repo = builder.repo
        queue.busy_string = "Upgrading"
        queue.save ()
        prox.add_binary_repo (binary_repo.name, binary_repo.url)
        # Now build it.
        queue.busy_string = "Building"
        queue.save ()
        result = prox.begin_build (queue_id, queue.sandboxed)
        queue.busy_string = "Syncing"
        queue.save ()
        prox.sync_logs (settings.RSYNC_LOG_HOST, settings.RSYNC_LOG_TARGET, settings.RSYNC_LOG_USERNAME, settings.RSYNC_LOG_PASSWORD)
        
        if result:
            binman = queue.binman
            print "Syncing packages"
            result = prox.sync_packages (binman.hostname, binman.rsync_target, binman.rsync_username, binman.rsync_password)
        
        packages = Package.objects.filter (queue=queue)
        for package in packages:
            naming = "%s-%s.txt" % (package.name, package.version)
            fpath = os.path.join (settings.LOG_BASE_DIRECTORY, naming)
            log = commands.getoutput ("tail -n 30 %s" % fpath).decode ("latin-1")
            package.build_log = smart_text(log, encoding='utf-8', strings_only=False, errors='strict')
            package.save ()    
        queue.busy = False
        queue.busy_string = None
        queue.save ()
        return result
    except Exception, e:
        print e
        queue.busy = False
        queue.busy_string = None
        queue.save ()
        return False
