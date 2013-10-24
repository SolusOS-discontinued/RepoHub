import xmlrpclib

import celery

class BuildHost:
    
    def __init__(self, host_info):
        self.kernel = host_info [3]
        self.hostname = host_info [2]
        self.total = float (host_info [0])
        self.avail = float (host_info [1])
        self.used = self.total - self.avail
        self.percent = (self.used / self.total) * 100
        self.percent_human = "%0.2f%%" % self.percent
        self.real_arch = host_info [4]
        self.max_jobs = int (host_info[5])
        self.imaging_progress = int (host_info[6])

def build_info_from_builder (builder):
    '''
    Get the build hosts information via xmlrpc
    '''

    try:
        prox = xmlrpclib.ServerProxy("http://%s:%s" % (builder.address, builder.port))
        host_info = prox.get_host_info ()
        prox = None
        return BuildHost (host_info)
    except Exception, e:
        print e
        return None
