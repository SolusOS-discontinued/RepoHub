import celery
import urllib2
from xml.dom.minidom import parse as parse_xml
from django.db import transaction

import django.contrib
from repository.models import SourceRepository, Repository, PisiPackage, PackageDependency, BinMan

from source.models import SourcePackage, SourceUpdate, SourceArchive, BuildDependency

import os
import tempfile
import shutil
import subprocess
import xmlrpclib
import datetime
import time

@celery.task
def process_incoming_binman (binman_id):
    binman = BinMan.objects.get(id=binman_id)
    if binman.busy:
        return False
        
    binman.busy = True
    binman.save ()
    try:
        prox = xmlrpclib.ServerProxy("http://%s:%s" % (binman.hostname, binman.control_port))
        prox.process_incoming ()
        prox.index ()
        binman.busy = False
        binman.save ()
        return True
    except Exception, e:
        print e
    return False
    
@celery.task
def create_deltas_binman (binman_id):
    binman = BinMan.objects.get(id=binman_id)
    if binman.busy:
        return False
        
    binman.busy = True
    binman.save ()
    try:
        prox = xmlrpclib.ServerProxy("http://%s:%s" % (binman.hostname, binman.control_port))
        prox.produce_deltas ()
        prox.index ()
        binman.busy = False
        binman.save ()
        return True
    except Exception, e:
        print e
    return False
    
@celery.task
def reload_all_repos ():
    s_repos = SourceRepository.objects.all()
    b_repos = Repository.objects.all()
    for source_repo in s_repos:
        import_source_repo (source_repo.id)
        
    for binary_repo in b_repos:
        rebuild_repo (binary_repo.id)
        
@celery.task
def import_source_repo (source_repo_id):
    source_repo = SourceRepository.objects.get(id=source_repo_id)
    repo = source_repo.url
    fail = False
    if source_repo.username != "" and source_repo.password != "":
        # Set the authentication up
        parts = source_repo.url.split("//")
        repo = "%s//%s:%s@%s" % (parts[0], source_repo.username, source_repo.password, parts[1])
    temp_dir = tempfile.mkdtemp (suffix="-repo", prefix="sSourceRepo")
    
    # Let's clone HG (add git later :P)
    try:
        source_repo.loading_status = "Cloning.."
        source_repo.save ()
        process = subprocess.Popen ("hg clone %s" % repo, cwd=temp_dir, shell=True)
        process.wait ()

        repo_dir = os.path.join (temp_dir, os.listdir (temp_dir)[0])
        source_repo.loading_status = "Updating.."
        source_repo.save ()
        process = subprocess.Popen ("hg update", cwd=repo_dir, shell=True)
        process.wait ()
    except:
        print "Could not import repo!"
        fail = True
    
    if not fail:
        pspec = os.path.join (repo_dir, "pisi-index.xml")
        if not os.path.exists (pspec):
            print "Could not find %s" % pspec
            fail = True
    
    # If we haven't failed now, hit up a new repo object :)
    source_repo.save ()
    try:
        with open (pspec, "r") as pspec_file:
            source_repo.loading_status = "Importing.."
            source_repo.save ()
            document = parse_xml (pspec_file)
            
            # Delete old objects
            with transaction.commit_on_success():
                for package in SourcePackage.objects.filter(repository=source_repo):
                    package.delete ()
                    
            # Handy shortcuts :)
            gall = lambda x, y : x.getElementsByTagName (y)
            get_value = lambda x, y : x.getElementsByTagName (y)[0].firstChild.nodeValue
            get_attr = lambda x, y : x.getAttribute (y)
            
            spec_files = document.getElementsByTagName ("SpecFile")
            with transaction.commit_on_success():
                for spec_file in spec_files:                   
                    # Basic source info
                    source = gall (spec_file, "Source")[0]
                    name = get_value (source, "Name")
                    license = get_value (source, "License")
                    summary = get_value (source, "Summary")
                    component = get_value (source, "PartOf")
                    description = get_value (source, "Description")
                    source_uri = get_value (source, "SourceURI")
                    
                    try:
                        homepage = get_value (source, "Homepage")
                    except:
                        homepage = None
                        
                    packager = gall (source, "Packager")[0]
                    packager_name = get_value (packager, "Name")
                    packager_email = get_value (packager, "Email")
                    
                    package = SourcePackage ()
                    package.name = name
                    package.maintainer_name = packager_name
                    package.maintainer_email = packager_email
                    package.summary = summary
                    package.description = description
                    package.component = component
                    package.repository = source_repo
                    package.source_uri = source_uri
                    
                    package.save ()
                                
                    # Process archives
                    for archive in gall (source, "Archive"):
                        uri = archive.firstChild.nodeValue
                        arch_type = get_attr (archive, "type")
                        try:
                            target = get_attr (archive, "target")
                        except:
                            target = None
                        sha1sum = get_attr (archive, "sha1sum")
                        
                        archive_db = SourceArchive ()
                        archive_db.uri = uri
                        archive_db.sha1sum = sha1sum
                        archive_db.target = target
                        archive_db.file_type = arch_type
                        archive_db.package = package
                        archive_db.save ()
                    
                    # Process the various build dependencies
                    try:
                        build_deps = gall (source, "BuildDependencies")[0]
                        for dep in gall (build_deps, "Dependency"):
                            dep_name = dep.firstChild.nodeValue
                            pbuild_dep = BuildDependency ()
                            pbuild_dep.name = dep_name
                            pbuild_dep.source_package = package
                                    
                            pbuild_dep.save ()
                    except:
                        pass
                    # Process history..
                    history = gall (spec_file, "History")[0]
                    highest_release = 0
                    version = ""
                    
                    for update in gall (history, "Update"):
                        updater_name = get_value (update, "Name")
                        updater_email = get_value (update, "Email")
                        update_comment = get_value (update, "Comment")
                        update_version = get_value (update, "Version")
                        update_release = int(get_attr (update, "release"))
                        
                        if update_release > highest_release:
                            highest_release = update_release
                            version = update_version
                            
                        update_db = SourceUpdate ()
                        update_db.name = updater_name
                        update_db.email = updater_email
                        update_db.comment = update_comment
                        update_db.release = update_release
                        update_db.version = update_version
                        update_db.package = package
                        update_db.save ()
                        
                    package.release = highest_release 
                    package.version = version
                    package.save ()    
                   
    except Exception, e:
        print e
        fail = True
    
    if fail:
        source_repo.delete () # Failed? Delete repository..
    else:
        source_repo.loading = False
        source_repo.loading_status = ""
        source_repo.save ()
    # Kill it wiv fiah.
    shutil.rmtree (temp_dir)
    
    return not fail
    
@celery.task
def rebuild_repo (repo_id):
    '''
    Rebuild the given repository - May take a long time !
    TODO: Update a Repository.status to indicate a rebuild is
    happening
    Also, we need to link PisiPackage objects to a Repository
    '''
    repo = Repository.objects.get(id=repo_id)
    
    print "Deleting all current PisiPackage objects"
    with transaction.commit_on_success():
        for deletion in PisiPackage.objects.filter(repository=repo):
            for dep in PackageDependency.objects.filter(package=deletion):
                dep.delete()
            deletion.delete ()
    
    try:
        url_obj = urllib2.urlopen (repo.url)
    except Exception, e:
        print e
        repo.building = False
        repo.save ()
        return
    document = parse_xml (url_obj)
    # Now parse the XML
    packages = document.getElementsByTagName ("Package")
    
    # Loop through and parse every package
    gall = lambda x, y : x.getElementsByTagName (y)
    
    get_value = lambda x, y : x.getElementsByTagName (y)[0].firstChild.nodeValue
    get_attr = lambda x, y : x.getAttribute (y)
    
    with transaction.commit_on_success():    
        for package in packages:
            try:
                name = get_value (package, "Name")
                history = gall (package, "History")
                updates = gall (history[0], "Update")
                
                # Most recent update..
                current_release = get_attr (updates[0], "release")
                version = get_value (updates[0], "Version")
                comment = get_value (updates[0], "Comment")
                date = str(get_value (updates[0], "Date"))
                
                # Hacks to get date working
                failed_date = False
                try:
                    conv_data = datetime.datetime.strptime (date, "%Y-%m-%d")
                except:
                    failed_date = True
                if failed_date:
                    try:
                        conv_date = datetime.datetime.strptime (date, "%m-%d-%Y")
                    except:
                        conv_data = datetime.datetime.strptime (date, "%Y-%d-%m")
                # Maintainer cruft
                maintainer = gall (package, "Packager")[0]
                maintainer_name = get_value (maintainer, "Name")
                maintainer_email = get_value (maintainer, "Email")
                
                # Info
                summary = get_value (package, "Summary")
                description = get_value (package, "Description")
                component = get_value (package, "PartOf")
                
                # Source 
                source = gall (package, "Source")[0]
                source_name = get_value (source, "Name")
                homepage = None
                try:
                    homepage = get_value (source, "Homepage")
                except:
                    pass
                
                ppackage = PisiPackage ()
                ppackage.name = name
                ppackage.version = version
                ppackage.maintainer_name = maintainer_name
                ppackage.maintainer_email = maintainer_email
                ppackage.summary = summary
                ppackage.component = component
                ppackage.description = description
                ppackage.date_updated = conv_date.strftime('%Y-%m-%d')
                ppackage.comment = comment
                ppackage.source_name = source_name
                ppackage.release = current_release
                ppackage.repository = repo
                
                # Attempt to determine 'known user'
                try:
                    user = django.contrib.auth.models.User.objects.get(email=maintainer_email)
                    ppackage.known_user = user
                except:
                    pass

                ppackage.save ()
                
                # Handle dependencies
                deps = gall (package, "RuntimeDependencies")
                try:
                    depPropers = gall (deps[0], "Dependency")
                    for dep in depPropers:
                        depends_on = dep.firstChild.nodeValue
                        pisi_dep = PackageDependency ()
                        pisi_dep.name = depends_on
                        pisi_dep.package = ppackage
                        pisi_dep.save ()
                except:
                    pass
            except Exception, e:
                print e
    repo.building = False
    repo.save ()
