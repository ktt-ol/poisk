from fabric.api import run, env, cd, local, put
from fabric.contrib import files

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
    local("git push --force poisk@ktt-ol.de:poisk/ master:master")
    put("config.py", "poisk/")
    put("run.sh", "poisk/", mode=0750)
    with cd("poisk"):
        run("git checkout master")
        run("git reset --hard")
