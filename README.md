# poisk

The following might work:

    git clone https://github.com/ktt-ol/poisk.git
    cd poisk
    virtualenv ./poisk
    ./poisk/bin/pip install -r requirements.txt
    python manage.py init_db
    python manage.py runserver
