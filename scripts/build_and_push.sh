#!/bin/bash
# 构建并推送Docker镜像到Docker Hub的脚本

set -e

# 配置变量
IMAGE_NAME="notion-csv-importer"
VERSION="1.0.0"
DOCKERHUB_USERNAME="treydong"  # 需要替换为实际的Docker Hub用户名

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}开始构建和推送Docker镜像${NC}"
echo -e "${BLUE}镜像信息:${NC}"
echo -e "镜像名称: ${IMAGE_NAME}"
echo -e "版本: ${VERSION}"
echo -e "Docker Hub用户: ${DOCKERHUB_USERNAME}"
echo ""

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker未安装，请先安装Docker${NC}"
    echo -e "${YELLOW}安装Docker命令:${NC}"
    echo -e "  Ubuntu/Debian: sudo apt-get update && sudo apt-get install -y docker.io"
    echo -e "  CentOS/RHEL: sudo yum install -y docker"
    echo -e "  macOS: 下载Docker Desktop"
    echo -e "  Windows: 下载Docker Desktop"
    echo -e "  或访问: https://docs.docker.com/get-docker/"
    exit 1
fi

echo -e "${GREEN}✅ Docker已安装${NC}"

# 检查是否已登录Docker Hub
echo -e "${BLUE}检查当前Docker登录状态...${NC}"
if docker info | grep -q "Username"; then
    echo -e "${GREEN}✅ 已登录Docker Hub${NC}"
    echo -e "${BLUE}当前用户: $(docker info | grep Username | sed 's/.*Username: //; s/.*//g')${NC}"
else
    echo -e "${YELLOW}⚠️  未登录Docker Hub${NC}"
    echo -e "${BLUE}尝试重新登录...${NC}"
    
    # 尝试重新登录（可能会失败，但至少尝试）
    echo "y" | docker login 2>/dev/null || echo -e "${RED}重新登录失败${NC}"
fi

echo ""

# 检查项目文件
echo -e "${BLUE}检查项目文件...${NC}"
if [ ! -f "app.py" ]; then
    echo -e "${RED}错误: 找不到app.py文件${NC}"
    exit 1
fi

if [ ! -f "Dockerfile" ]; then
    echo -e "${RED}错误: 找不到Dockerfile文件${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 项目文件检查通过${NC}"

# 构建镜像
echo -e "${GREEN}构建Docker镜像...${NC}"
BUILD_OUTPUT=$(docker build -t ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${VERSION} . 2>&1)
BUILD_EXIT_CODE=$?

# 检查构建结果
if [ $BUILD_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Docker镜像构建成功${NC}"
    echo -e "${BLUE}镜像详情:${NC}"
    docker images | grep ${DOCKERHUB_USERNAME}/${IMAGE_NAME}
else
    echo -e "${RED}❌ Docker镜像构建失败${NC}"
    echo -e "${RED}构建错误信息:${NC}"
    echo "${BUILD_OUTPUT}"
    exit 1
fi

# 推送镜像
echo -e "${GREEN}推送镜像到Docker Hub...${NC}"
docker push ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${VERSION}

PUSH_EXIT_CODE=$?

# 检查推送结果
if [ $PUSH_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Docker镜像推送成功${NC}"
    echo -e "${BLUE}镜像地址: ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${VERSION}${NC}"
else
    echo -e "${RED}❌ Docker镜像推送失败${NC}"
    exit 1
fi

# 推送latest标签
echo -e "${GREEN}推送latest标签...${NC}"
docker tag ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${VERSION} ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:latest

LATEST_PUSH_EXIT_CODE=$?

if [ $LATEST_PUSH_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ latest标签推送成功${NC}"
else
    echo -e "${RED}❌ latest标签推送失败${NC}"
fi

echo ""

# 显示Docker Compose配置示例
echo -e "${BLUE}Docker Compose配置示例:${NC}"
echo "version: '3.8'"
echo ""
echo "services:"
echo "  notion-csv-importer:"
echo "    image: ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:latest"
echo "    ports:"
echo "      - \"8000:8000\""
echo "    environment:"
echo "      - NOTION_TOKEN=\${NOTION_TOKEN}"
echo "      - NOTION_DATABASE_ID=\${NOTION_DATABASE_ID}"
echo "      - NOTION_HOLDINGS_DATABASE_ID=\${NOTION_HOLDINGS_DATABASE_ID}"
echo "      - CSV_FILE_PATH=\${CSV_FILE_PATH:-Table_5478.csv}"
echo "      - CSV_ENCODING=\${CSV_ENCODING:-gbk}"
echo ""

echo -e "${GREEN}✅ 所有操作完成!${NC}"
echo ""
echo -e "${YELLOW}使用方法:${NC}"
echo "1. 拉取镜像: docker pull ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:latest"
echo "2. 创建docker-compose.yml文件，复制上面的配置"
echo "3. 创建.env文件，设置环境变量"
echo "4. 启动服务: docker-compose up -d"
echo ""
echo -e "${BLUE}部署完成!${NC}"
echo -e "${GREEN}镜像地址: ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:latest${NC}"