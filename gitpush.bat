@echo off
git add .
git commit -m %1
git push
git pull