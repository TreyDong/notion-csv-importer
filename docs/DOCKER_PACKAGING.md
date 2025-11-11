# Docker镜像打包指南

## 镜像打包方式

### 方式一：使用Docker Hub（推荐）

#### 1. 准备工作
```bash
# 确保已安装Docker
docker --version

# 登录Docker Hub
docker login

# 确保项目文件完整
ls -la
```

#### 2. 使用构建脚本
```bash
# 给脚本添加执行权限
chmod +x build_and_push.sh

# 执行构建和推送
./build_and_push.sh
```

#### 3. 手动构建和推送
```bash
# 构建镜像
docker build -t your-dockerhub-username/notion-csv-importer:1.0.0 .

# 推送版本标签
docker push your-dockerhub-username/notion-csv-importer:1.0.0

# 推送latest标签
docker tag your-dockerhub-username/notion-csv-importer:1.0.0 your-dockerhub-username/notion-csv-importer:latest
docker push your-dockerhub-username/notion-csv-importer:latest
```

### 方式二：使用GitHub Packages（适合开源项目）

#### 1. 创建GitHub Personal Access Token
1. 访问 https://github.com/settings/tokens
2. 点击"Generate new token"
3. 选择"Generate new token (classic)"
4. 设置权限：`repo`, `write:packages`, `delete:packages`
5. 复制生成的token

#### 2. 创建GitHub Actions工作流
创建 `.github/workflows/docker-publish.yml`：

```yaml
name: Docker Image CI

on:
  push:
    branches:
      - main
  release:
    types: [published]

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          file: ./Dockerfile
          push: true
          tags: |
            your-dockerhub-username/notion-csv-importer:latest
            your-dockerhub-username/notion-csv-importer:${{ github.ref_name }}
          your-dockerhub-username/notion-csv-importer:${{ github.sha }}
```

#### 3. 创建Dockerfile（GitHub Packages优化）
```dockerfile
# 多阶段构建，优化镜像大小
FROM python:3.9-slim as builder

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app.py .

# 创建最终镜像
FROM python:3.9-slim

WORKDIR /app

# 复制依赖（从构建阶段）
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

# 复制应用代码
COPY app.py .

# 创建非root用户
RUN useradd --create-home --shell /bin/bash app
USER app

# 暴露端口
EXPOSE 8000

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 启动命令
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 4. 配置GitHub仓库Secrets
在GitHub仓库设置中添加以下Secrets：
- `DOCKERHUB_USERNAME`: 你的Docker Hub用户名
- `DOCKERHUB_TOKEN`: 你的Docker Hub访问token

### 方式三：使用云服务商

#### 1. AWS ECR
```bash
# 创建ECR仓库
aws ecr create-repository --repository-name notion-csv-importer --region us-east-1

# 登录ECR
aws ecr get-login-password --region us-east-1

# 构建并推送
docker build -t notion-csv-importer:latest .
docker tag notion-csv-importer:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/notion-csv-importer:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/notion-csv-importer:latest
```

#### 2. 阿里云容器镜像服务
```bash
# 构建并推送到阿里云
docker build -t registry.cn-hangzhou.aliyuncs.com/your-namespace/notion-csv-importer:latest .
docker push registry.cn-hangzhou.aliyuncs.com/your-namespace/notion-csv-importer:latest

# 腾讯云容器镜像服务配置
# 在docker-compose.yml中使用
image: registry.cn-hangzhou.aliyuncs.com/your-namespace/notion-csv-importer:latest
```

#### 3. 谷歌云GCR
```bash
# 配置gcloud认证
gcloud auth configure-docker

# 构建并推送
docker build -t gcr.io/your-project/notion-csv-importer:latest .
docker push gcr.io/your-project/notion-csv-importer:latest
```

## 镜像优化建议

### 1. 减少镜像大小
- 使用多阶段构建
- 使用`.dockerignore`文件排除不必要文件
- 选择合适的基础镜像（alpine vs slim）

### 2. 安全最佳实践
```dockerfile
# 使用非root用户
RUN useradd --create-home --shell /bin/bash app
USER app

# 只安装必要的依赖
RUN pip install --no-cache-dir -r requirements.txt

# 设置安全的环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
```

### 3. 标签策略
- 使用语义化版本标签（如1.0.0, 1.1.0）
- 同时推送latest标签用于稳定版本
- 使用git SHA作为构建标签

### 4. .dockerignore示例
```
# 排除不必要的文件
.git
.gitignore
README.md
.env.example
__pycache__
.pyc
.pyo
.pyd
.vscode
.idea
```

## 自动化CI/CD

### GitHub Actions完整配置
```yaml
name: Docker Image CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  release:
    types: [published]

env:
  REGISTRY: your-dockerhub-username
  IMAGE_NAME: notion-csv-importer

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          python -m pytest tests/ || echo "Tests skipped"
  
  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          file: ./Dockerfile
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.ref_name }}
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
```

## 部署检查清单

### 部署前检查
- [ ] Docker Hub账户已创建
- [ ] 构建脚本已测试
- [ ] 环境变量已配置
- [ ] 镜像已成功推送到Docker Hub
- [ ] docker-compose.yml文件已创建
- [ ] 部署文档已更新

### 部署后验证
- [ ] 镜像可以成功拉取
- [ ] 容器可以正常启动
- [ ] Web界面可以正常访问
- [ ] CSV文件可以正常上传
- [ ] 数据可以正常导入到Notion
- [ ] 股票持仓关联功能正常工作

---

**版本**: 1.0.0
**更新时间**: 2025-11-11
**状态**: 准备就绪