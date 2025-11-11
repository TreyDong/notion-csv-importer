# Docker Compose在线部署指南

## 部署方案

### 方案一：使用云服务器部署（推荐）

#### 1. 准备云服务器
- 购买云服务器（阿里云、腾讯云、AWS等）
- 确保服务器已安装Docker和Docker Compose
- 开放必要端口（如8000）

#### 2. 上传项目文件
```bash
# 在服务器上创建项目目录
mkdir -p /opt/notion-csv-importer
cd /opt/notion-csv-importer

# 上传项目文件（使用scp、rsync或FTP）
scp -r ./* user@your-server:/opt/notion-csv-importer/
```

#### 3. 配置环境变量
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
nano .env
```

#### 4. 启动服务
```bash
# 构建并启动服务
docker-compose up --build -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 方案二：使用Docker Cloud（零配置）

#### 1. 准备Dockerfile
创建一个优化的Dockerfile用于云部署：

```dockerfile
# 使用官方Python镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y gcc

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app.py .

# 创建必要的目录
RUN mkdir -p templates static

# 暴露端口
EXPOSE 8000

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 启动命令
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. 构建并推送到Docker Hub
```bash
# 构建镜像
docker build -t your-username/notion-csv-importer .

# 登录Docker Hub
docker login

# 推送镜像
docker push your-username/notion-csv-importer
```

#### 3. 部署到云平台

##### Docker Cloud部署
```bash
# 创建docker-compose.yml
cat > docker-compose.yml << EOF
version: '3.8'

services:
  notion-csv-importer:
    image: your-username/notion-csv-importer:latest
    ports:
      - "8000:8000"
    environment:
      - NOTION_TOKEN=\${NOTION_TOKEN}
      - NOTION_DATABASE_ID=\${NOTION_DATABASE_ID}
      - NOTION_HOLDINGS_DATABASE_ID=\${NOTION_HOLDINGS_DATABASE_ID}
      - CSV_FILE_PATH=\${CSV_FILE_PATH:-Table_5478.csv}
      - CSV_ENCODING=\${CSV_ENCODING:-gbk}
    restart: unless-stopped
EOF

# 部署
docker-compose up -d
```

##### AWS ECS部署
```bash
# 创建ECS任务定义
cat > task-definition.json << EOF
{
  "family": "notion-csv-importer",
  "networkMode": "awsvpc",
  "requiresCompatibilities": [
    {
      "cpu": "256",
      "memory": "512"
    }
  ],
  "containerDefinitions": [
    {
      "name": "notion-csv-importer",
      "image": "your-username/notion-csv-importer:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "hostPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "NOTION_TOKEN",
          "value": "\${NOTION_TOKEN}"
        },
        {
          "name": "NOTION_DATABASE_ID",
          "value": "\${NOTION_DATABASE_ID}"
        },
        {
          "name": "NOTION_HOLDINGS_DATABASE_ID",
          "value": "\${NOTION_HOLDINGS_DATABASE_ID}"
        }
      ]
    }
  ]
}
EOF

# 注册任务定义
aws ecs register-task-definition --cli-input-json file://task-definition.json

# 创建服务
aws ecs create-service --cluster your-cluster --service-name notion-csv-importer --task-definition notion-csv-importer --desired-count 1
```

### 方案三：使用PaaS平台（Heroku、Render等）

#### Heroku部署
```bash
# 创建Procfile
cat > Procfile << EOF
web: uvicorn app:app --host 0.0.0.0 --port \${PORT:-8000}
EOF

# 创建heroku.yml
cat > heroku.yml << EOF
build:
  docker:
    dockerfile: Dockerfile
run:
  web:
    command: uvicorn app:app --host 0.0.0.0 --port \${PORT:-8000}
    environment:
      - NOTION_TOKEN
      - NOTION_DATABASE_ID
      - NOTION_HOLDINGS_DATABASE_ID
EOF

# 部署
heroku create your-app-name

# 设置环境变量
heroku config:set NOTION_TOKEN=your_token
heroku config:set NOTION_DATABASE_ID=your_database_id
heroku config:set NOTION_HOLDINGS_DATABASE_ID=your_holdings_database_id
```

#### Render部署
```yaml
# render.yaml
services:
  - type: web
    name: notion-csv-importer
    env: docker
    plan: free
    dockerContext: .
    dockerfilePath: ./Dockerfile
    envVars:
      - key: NOTION_TOKEN
        value: your_token
      - key: NOTION_DATABASE_ID
        value: your_database_id
      - key: NOTION_HOLDINGS_DATABASE_ID
        value: your_holdings_database_id
```

### 方案四：使用Kubernetes

#### 1. 创建Kubernetes配置
```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: notion-csv-importer
spec:
  replicas: 1
  selector:
    matchLabels:
      app: notion-csv-importer
  template:
    metadata:
      labels:
        app: notion-csv-importer
    spec:
      containers:
      - name: notion-csv-importer
        image: your-username/notion-csv-importer:latest
        ports:
        - containerPort: 8000
        env:
        - name: NOTION_TOKEN
          valueFrom:
            secretKeyRef:
              name: notion-secrets
              key: NOTION_TOKEN
        - name: NOTION_DATABASE_ID
          valueFrom:
            secretKeyRef:
              name: notion-secrets
              key: NOTION_DATABASE_ID
        - name: NOTION_HOLDINGS_DATABASE_ID
          valueFrom:
            secretKeyRef:
              name: notion-secrets
              key: NOTION_HOLDINGS_DATABASE_ID
---
apiVersion: v1
kind: Service
metadata:
  name: notion-csv-importer-service
spec:
  selector:
    app: notion-csv-importer
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: LoadBalancer
```

#### 2. 创建Secret
```yaml
# notion-secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: notion-secrets
type: Opaque
data:
  NOTION_TOKEN: <base64-encoded-token>
  NOTION_DATABASE_ID: <base64-encoded-database-id>
  NOTION_HOLDINGS_DATABASE_ID: <base64-encoded-holdings-id>
```

#### 3. 部署
```bash
# 应用配置
kubectl apply -f notion-secrets.yaml
kubectl apply -f k8s-deployment.yaml

# 查看状态
kubectl get pods -l app=notion-csv-importer
kubectl get services
```

### 监控和维护

#### 1. 健康检查
```bash
# 添加健康检查端点到app.py
# 在app.py中添加：
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
```

#### 2. 日志管理
```bash
# 查看容器日志
docker-compose logs -f --tail=100

# 设置日志轮转
# 在docker-compose.yml中添加：
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

#### 3. 自动重启策略
```yaml
# 在docker-compose.yml中添加：
restart_policy:
  delay: 5s
  window: 30s
  max_attempts: 3
```

### 安全配置

#### 1. HTTPS配置
```yaml
# 使用Nginx反向代理
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $scheme;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
}
```

#### 2. 防火墙配置
```bash
# UFW防火墙
sudo ufw allow 8000
sudo ufw allow 443

# iptables防火墙
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
```

### 性能优化

#### 1. 资源限制
```yaml
# 在docker-compose.yml中设置资源限制
services:
  notion-csv-importer:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

#### 2. 缓存配置
```python
# 在app.py中添加缓存
from fastapi_cache import FastAPICache
from fastapi_cache.backends import InMemoryCache

# 创建缓存实例
cache = FastAPICache()

@app.get("/config", response_model=ConfigResponse)
@cache(expire=300)  # 缓存5分钟
async def get_config():
    return get_config_from_db()
```

### 备份策略

#### 1. 数据库备份
```bash
# 自动备份脚本
cat > backup.sh << EOF
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T notion-csv-importer pg_dump -U user -d database > backup_$DATE.sql
EOF

chmod +x backup.sh

# 设置定时备份
echo "0 2 * * * /path/to/backup.sh" | crontab -
```

#### 2. 配置版本控制
```bash
# 使用Git标签管理版本
git tag -a v1.0.0 -m "Initial release"
git push origin v1.0.0

# 创建发布说明
cat > RELEASE_NOTES.md << EOF
# 版本 1.0.0
## 新功能
- 完整的Web界面
- Docker化部署
- 股票持仓关联功能

## 部署说明
详见DEPLOYMENT.md
EOF
```

### 故障排除

#### 常见问题及解决方案

1. **容器启动失败**
   ```bash
   # 检查Docker守护进程
   sudo systemctl status docker
   
   # 检查磁盘空间
   df -h
   
   # 清理Docker资源
   docker system prune -a
   ```

2. **网络连接问题**
   ```bash
   # 检查端口占用
   netstat -tulpn | grep :8000
   
   # 检查防火墙
   sudo ufw status
   
   # 测试连接
   curl -I http://localhost:8000
   ```

3. **内存不足错误**
   ```bash
   # 增加swap空间
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   
   # 优化Docker内存使用
   echo 'vm.swappiness=10' >> /etc/sysctl.conf
   sysctl -p
   ```

4. **Notion API限制**
   ```python
   # 在app.py中添加重试机制
   import time
   from tenacity import retry, stop_after_attempt, wait_exponential
   
   @retry(stop_after_attempt=3, wait=wait_exponential(multiplier=1, min=4, max=10))
   def create_notion_page(data):
       # API调用逻辑
       pass
   ```

这个部署指南涵盖了从简单的云服务器部署到复杂的Kubernetes集群部署的各种方案，以及监控、安全和故障排除的最佳实践。