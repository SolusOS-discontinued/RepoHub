import xmlrpclib

from repository.models import BinMan, BinManInfo

def binman_info_from_binman (binman_id):
    binman = BinMan.objects.get (id=binman_id)
    binman_info = BinManInfo ()
    
    try:
        prox = xmlrpclib.ServerProxy("http://%s:%s" % (binman.hostname, binman.control_port))
        binman_info.pending_packages = prox.pending_count ()
        binman_info.active = True
    except Exception, e:
        print e
        pass
    return binman_info
    
