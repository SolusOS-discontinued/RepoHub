import celery
import xmlrpclib

from builder.models import Builder, BuilderMedia

@celery.task
def refresh_known_medias ():
    for builder in Builder.objects.all ():
        try:
            prox = xmlrpclib.ServerProxy("http://%s:%s" % (builder.address, builder.port))
            bm = BuilderMedia.objects.filter(builder=builder)
            if bm != None:
                bm.delete ()
            fs_info = prox.get_storage_info ()
            b_media = BuilderMedia ()
            b_media.builder = builder
            b_media.size = int(fs_info [1])
            b_media.filesystem = fs_info [0]
            b_media.backing_store = fs_info [2]
            b_media.save ()
            prox = None
        except:
            pass

@celery.task
def update_builder_media (builder, media):
    '''
    Update/create the build media via xmlrpc
    '''
    try:
        prox = xmlrpclib.ServerProxy("http://%s:%s" % (builder.address, builder.port))
        result = prox.update_media (media.filesystem, media.size, media.backing_store)
        
        # Ensure correct FS info
        fs_info = prox.get_storage_info ()
        # Now update known BuilderMedia
        bm = BuilderMedia.objects.filter(builder=builder)
        if bm != None:
            bm.delete ()
        b_media = BuilderMedia ()
        b_media.builder = builder
        b_media.size = int(fs_info [1])
        b_media.filesystem = fs_info [0]
        b_media.backing_store = fs_info [2]
        b_media.save ()
        prox = None
        if not result:
            print "Failed to create backing media"
        else:
            print "Created backing media"
        return True
    except Exception, e:
        print e
        return False
