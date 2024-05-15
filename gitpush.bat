@echo off
::檢查是否有commit訊息
if "%1" == "" (
    echo message!!
    echo method: gitpush "msseage"
    exit /b 1
)
echo Adding...
::設定名字
git config --global user.email %2

git config --global user.name %3
::提交
git add .
echo Message: %1
git commit -m %1
echo pushing
git push
echo checkout
git pull
