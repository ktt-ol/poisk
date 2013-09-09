import os
from fabric.api import run, env, cd, local, put
from fabric.contrib import files
from fabric import colors

env.roledefs = {
    'production': ['poisk@ktt-ol.de']
}

def init():
    run("git init poisk")
    with cd("poisk"):
        run("git config receive.denyCurrentBranch ignore")

def install():
    if not files.exists("poisk/bin"):
        run("virtualenv poisk")
    with cd("poisk"):
        run("bin/pip install -r requirements.txt")

def deploy():
    if os.path.exists("deploy_config.py"):
        put("deploy_config.py", "poisk/config.py")
    else:
        print colors.red("no deploy_config.py found, using existing on server")
    local("git push --force poisk@ktt-ol.de:poisk/ master:master")
    put("run.sh", "poisk/", mode=0750)
    with cd("poisk"):
        run("git checkout master")
        run("git reset --hard")

        #run('sqlite3 app.db < upgrade.sql')
