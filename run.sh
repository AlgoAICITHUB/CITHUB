#!/bin/bash

echo "開始設置專案環境..."

# 更新
echo "更新系統並安裝基本依賴項..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv curl

# 設置虛擬環境
echo "設置 Python 虛擬環境..."
python3 -m venv venv
source venv/bin/activate

# 安裝 Python 依賴項
echo "安裝 Python 依賴項..."
pip install -r requirements.txt

# 安裝 Docker
if ! command -v docker &> /dev/null; then
    echo "安裝 Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm get-docker.sh

    sudo usermod -aG docker $USER
    echo "請重新登錄以應用 Docker 群組更改。"
fi


echo "構建並啟動 Docker 容器..."
sudo docker build -t my_flask_app .
sudo docker run -d -p 5000:5000 --name my_flask_container my_flask_app

# 顯示設置完成的訊息
echo "專案環境設置完成並已啟動 Docker 容器！"
