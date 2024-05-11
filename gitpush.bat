@echo off
if "%1" == "" (
    echo message!!
    echo method: gitpush "msseage"
    exit /b 1
)
echo Adding...
git add .
echo Message: %1
git commit -m %1
echo pushing
git push
echo checkout
git pull
