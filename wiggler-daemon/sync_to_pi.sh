#!/bin/sh

# I am too cheap to pay for pycharm pro so I am just using rsync to sync
# everything

rsync -avz --exclude .git/ --exclude .gitignore --exclude .idea --exclude .venv --exclude .pytest_cache --exclude **/__pycache__ . pi@192.168.1.100:/home/pi/wiggler-daemon
