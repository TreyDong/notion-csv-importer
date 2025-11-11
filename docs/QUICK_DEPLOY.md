# 快速部署指南

## 镜像已准备

镜像名称: `your-dockerhub-username/notion-csv-importer:latest`

## 快速部署步骤

### 1. 拉取镜像
```bash
docker pull your-dockerhub-username/notion-csv-importer:latest
```

### 2. 创建docker-compose.yml
复制以下内容到 `docker-compose.yml` 文件：

```yaml
version: '3.8'

services:
  notion-csv-importer:
    image: your-dockerhub-username/notion-csv-importer:latest
    ports:
      - "8000:8000"
    volumes:
      - ./.env:/app/.env:ro
    environment:
      - NOTION_TOKEN=${NOTION_TOKEN}
      - NOTION_DATABASE_ID=${NOTION_DATABASE_ID}
      - NOTION_HOLDINGS_DATABASE_ID=${NOTION_HOLDINGS_DATABASE_ID}
      - CSV_FILE_PATH=${CSV_FILE_PATH:-Table_5478.csv}
      - CSV_ENCODING=${CSV_ENCODING:-gbk}
    restart: unless-stopped
```

### 3. 创建.env文件
创建 `.env` 文件并设置以下变量：

```bash
# Notion API配置
NOTION_TOKEN=your_notion_token_here
NOTION_DATABASE_ID=your_main_database_id_here
NOTION_HOLDINGS_DATABASE_ID=your_holdings_database_id_here

# CSV文件配置（可选）
CSV_FILE_PATH=Table_5478.csv
CSV_ENCODING=gbk
```

### 4. 启动服务
```bash
# 启动服务
docker-compose -f docker-compose.simple.yml up -d

# 查看日志
docker-compose -f docker-compose.simple.yml logs -f

# 停止服务
docker-compose -f docker-compose.simple.yml down
```

### 5. 访问应用

打开浏览器访问: http://localhost:8000

## 功能说明

- 🌐 **Web界面**: 上传CSV文件并导入到Notion
- 📊 **数据处理**: 自动清理Excel公式和空格
- 🔗 **智能关联**: 自动关联股票持仓数据库
- 📝 **备注标注**: 自动添加"外部导入"标记

## 注意事项

1. 确保8000端口未被占用
2. 确保Docker已安装并运行
3. 确保Notion token有效且有数据库访问权限
4. 建议先测试少量数据再导入全部

## 故障排除

### 常见问题

1. **端口占用**
   ```bash
   netstat -tulpn | grep :8000
   # 或者
   lsof -i :8000
   ```

2. **权限问题**
   ```bash
   # 检查Docker权限
   sudo usermod -aG $USER docker
   ```

3. **查看日志**
   ```bash
   docker-compose -f docker-compose.simple.yml logs -f --tail=100
   ```

4. **重启服务**
   ```bash
   docker-compose -f docker-compose.simple.yml restart
   ```

## 支持

如遇问题，请检查：
1. Docker日志输出
2. 浏览器控制台错误
3. Notion API连接状态
4. 网络连接情况

---
**版本**: 1.0.0
**更新时间**: 2025-11-11