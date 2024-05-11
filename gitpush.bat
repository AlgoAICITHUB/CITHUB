@echo off
if "%1" == "" (
    echo 訊息!!
    echo 方法: gitpush "訊息"
    exit /b 1
)
echo 添加中
git add .
echo 訊息 %1
git commit -m %1
echo 推送
git push
echo 檢查
git pull
