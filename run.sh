#! /bin/sh
cd $(dirname $0)
bin/python manage.py runserver --port 7997 2>&1 |tee --append poisk-access.log
