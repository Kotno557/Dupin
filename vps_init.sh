#!/bin/bash
set -euxo pipefail # Exit immediately if a command exits with a non-zero status.

# --- 1. 更新系統並安裝 OpenVPN ---
echo "Updating system and installing OpenVPN..."
sudo apt update -y
sudo apt upgrade -y
sudo apt install -y openvpn

# --- 2. 配置並啟動 OpenVPN 客戶端 ---
# IMPORTANT: 你需要將你的 .ovpn 檔案內容或下載方式放在這裡。
# 選擇以下其中一種方式：

# --- 方式 A: 從 S3 下載 .ovpn 檔案 (推薦自動化) ---
# 將 YOUR_S3_BUCKET_NAME 和 YOUR_OVPN_FILE_NAME 替換為你的實際值。
# 確保 EC2 實例的 IAM Role 有權限從 S3 下載。
# echo "Downloading OpenVPN configuration from S3..."
# sudo aws s3 cp s3://YOUR_S3_BUCKET_NAME/YOUR_OVPN_FILE_NAME /etc/openvpn/client/client.conf

# --- 方式 B: 直接將 .ovpn 內容嵌入腳本 (如果檔案較小且不含敏感資訊) ---
# 將 YOUR_OVPN_FILE_CONTENT 替換為你的 .ovpn 檔案的實際內容。
# 請注意單引號內的所有內容必須是單行，或處理好換行符。
echo "Placing OpenVPN configuration..."
sudo tee /etc/openvpn/client/client.conf > /dev/null << 'EOF'
# BEGIN_OVPN_CONFIG
# 將你的 OpenVPN .ovpn 檔案內容貼在這裡
# 例如:
client
dev tun
proto udp
remote vpn.example.com 1194
resolv-retry infinite
nobind
persist-key
persist-tun
ca ca.crt
cert client.crt
key client.key
remote-cert-tls server
tls-auth ta.key 1
cipher AES-256-CBC
comp-lzo
verb 3
# END_OVPN_CONFIG
EOF

# 如果你的 .ovpn 檔案需要額外的憑證檔案 (ca.crt, client.crt, client.key, ta.key)，
# 你也需要將它們複製到 /etc/openvpn/client/，例如：
# sudo tee /etc/openvpn/client/ca.crt > /dev/null << 'EOF'
# ... CA 憑證內容 ...
# EOF
# sudo tee /etc/openvpn/client/client.crt > /dev/null << 'EOF'
# ... 客戶端憑證內容 ...
# EOF
# sudo tee /etc/openvpn/client/client.key > /dev/null << 'EOF'
# ... 客戶端私鑰內容 ...
# EOF
# sudo tee /etc/openvpn/client/ta.key > /dev/null << 'EOF'
# ... TLS-Auth 金鑰內容 ...
# EOF


echo "Enabling and starting OpenVPN client service..."
sudo systemctl enable openvpn-client@client # 'client' 來自 /etc/openvpn/client/client.conf
sudo systemctl start openvpn-client@client
# 等待 VPN 連接建立 (可選，但對於確保後續服務使用 VPN 很重要)
sleep 10 # 給予 OpenVPN 一些時間來連接

# 檢查 VPN 是否生效 (可選)
echo "Checking public IP after VPN connection:"
curl ifconfig.me || true # 使用 || true 防止命令失敗導致腳本退出

# --- 3. 安裝 Docker 和 Docker Compose ---
echo "Installing Docker and Docker Compose..."
sudo apt install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu # 讓 ubuntu 用戶可以運行 docker 命令

# --- 4. 獲取你的應用程式檔案 ---
# 選擇以下其中一種方式獲取你的 Dupin 專案檔案：

# --- 方式 A: 從 GitHub 克隆你的儲存庫 (如果它是公開的) ---
# 如果你的 Dupin 專案是公開的 GitHub 儲存庫，請將 YOUR_GITHUB_REPO_URL 替換為你的儲存庫 URL。
# echo "Cloning application repository..."
# git clone YOUR_GITHUB_REPO_URL /app
# cd /app

# --- 方式 B: 從 S3 下載應用程式壓縮包 (推薦) ---
# 這需要你先將你的整個 Dupin 專案壓縮成一個 .tar.gz 或 .zip 檔案，並上傳到 S3。
# 確保 EC2 實例的 IAM Role 有權限從 S3 下載。
echo "Downloading application files from S3..."
mkdir -p /app
cd /app
# sudo aws s3 cp s3://YOUR_S3_BUCKET_NAME/dupin-app.tar.gz .
# tar -xzf dupin-app.tar.gz
# 或者，如果你的檔案是手動放置的，請確保它們在此處可用。
# 為此範例，我將假設你已經將相關檔案放置在 /app 目錄中。
# 如果你想手動 scp 這些檔案，請在 EC2 啟動後執行此操作。

# 為這個 User Data 腳本的完整性，我們假設你已經手動將所有必要的應用程式檔案
# (Dockerfile, requirements.txt, dupin_server.py, dupin_vpn_server.py,
# default-config-file/, lib/dupin_python_lib/)
# 放置在 /app 目錄中，或者腳本中會包含一個 git clone 命令。
# 為了避免在 User Data 腳本中處理太多檔案複製邏輯，建議在啟動後手動 scp 或使用 S3 下載。

# 如果是 Git Clone 方案 (請取消註釋並替換為你的 repo URL)：
# git clone https://github.com/your-username/Dupin.git /app/dupin-project # 假設你的 repo 叫 Dupin
# cd /app/dupin-project

# 在這裡假設你的所有項目文件都在 /app
# 為了讓這個示例完整，你需要確保這些文件實際存在於 /app 中。
# 如果你的项目目录结构复杂，例如 git clone 后有一个子目录，请调整 cd /app/dupin-project
cp -r /Users/selab/Documents/Dupin/default-config-file /app/
cp -r /Users/selab/Documents/Dupin/lib/dupin_python_lib /app/
cp /Users/selab/Documents/Dupin/dupin_server.py /app/
cp /Users/selab/Documents/Dupin/dupin_vpn_server.py /app/
cp /Users/selab/Documents/Dupin/requirements.txt /app/
cp /Users/selab/Documents/Dupin/Dockerfile /app/


# --- 5. 建置並運行 Docker 應用程式 ---
echo "Building Docker image..."
sudo docker build -t dupin-vpn-server .

echo "Running Docker container..."
sudo docker run -d -p 8080:8000 --name dupin-app dupin-vpn-server

echo "User Data script completed."
