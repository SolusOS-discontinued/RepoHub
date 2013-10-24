repohub
=====================

The SolusOS Repo and Buildfarm Management Interface
NOTE: You must use Python2.6 for Celery to work correctly


NOTES:
Admin's password is 'admin' (see fixtures)

Installation
-------------

**RabbitMQ**

     sudo rabbitmqctl add_user repohub repohub
     sudo rabbitmqctl add_vhost repohub
     sudo rabbitmqctl set_permissions -p repohub repohub ".*" ".*" ".*"
     
**From the base directory of the repohub repository:**

     virtualenv backend
     source backend/bin/activate
     pip install -r web/requirements.txt
     
**Usage:**

     cd web/
     source ../backend/bin/activate
     python manage.py syncdb --noinput
     python manage.py runserver
     
**Start the celery daemon**

    python manage.py celery worker -E -B
    
Other Daemons
-------------
RepoHub requires that rsyncd be running and configured for use by RepoHub.
We need to be able to receive log files from the build slave.

/etc/rsyncd.conf
----------------
    motd file = /etc/rsyncd.motd

    [buildlogs]
    path = /home/repohub/logs
    comment = RepoHub log files
    uid = repohub
    gid = repohub
    read only = false
    auth users = repohub
    secrets file = /etc/rsyncd.secret

/etc/rsyncd.secrets (mode 600)
------------------------------
    repohub:repohub


Now navigate to locahost:8080 to try out repohub
