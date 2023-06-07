##!/bin/bash
#sh blacked.sh
#pip freeze > request.txt
black .
git config --global user.name "bussiere"
git config --global user.email "bussiere@gmail.com"
branch=$(git symbolic-ref HEAD | sed -e 's,.*/\(.*\),\1,')
git pull origin $branch
git add .
current="`date +'%Y-%m-%d %H:%M:%S'`"
msg="Updated: $current"
git commit -m "wip $branch $msg"
git push origin $branch

