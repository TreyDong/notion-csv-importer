# CSV到Notion导入工具

一个功能强大的Web应用程序，用于将股票交易CSV文件导入到Notion数据库，支持自动创建持仓记录关联。

## 功能特性

- 🔄 自动清理Excel公式格式数据
- 📊 智能识别并创建持仓记录
- 🌍 支持多种文件编码格式（GBK、UTF-8等）
- ⚡ 批量处理避免API限制
- 🔍 重复数据检测与跳过
- 🎨 现代化响应式Web界面
- 📱 支持拖拽上传文件

## 项目结构

```
.
├── app.py                 # 主应用程序文件
├── requirements.txt        # Python依赖
├── Dockerfile            # Docker容器配置
├── docker-compose.yml     # Docker Compose配置
├── templates/            # HTML模板
│   └── index.html       # Web界面
├── static/              # 静态资源
├── scripts/             # 脚本文件
│   └── build_and_push.sh  # 构建和推送Docker镜像脚本
├── .env.example         # 环境变量示例
├── .env                 # 环境变量配置(本地)
└── .gitignore           # Git忽略文件
```

## 快速开始

### 使用Docker（推荐）

1. 克隆项目
```bash
git clone <repository-url>
cd csv-notion-importer
```

2. 配置环境变量
```bash
cp .env.example .env
# 编辑.env文件，填入您的Notion API token和数据库ID
```

3. 启动服务
```bash
docker-compose up -d
```

4. 访问Web界面
```
http://localhost:8002
```


### 本地运行

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 设置环境变量
```bash
cp .env.example .env
# 编辑.env文件，填入您的Notion API token和数据库ID
```

3. 运行应用
```bash
python app.py
```

## 部署说明

### Docker部署(推荐)

1. 确保已安装Docker和Docker Compose
2. 配置环境变量
```bash
cp .env.example .env
# 编辑.env文件，填入必要的配置信息
```

3. 启动服务
```bash
docker-compose up -d
```

4. 停止服务
```bash
docker-compose down
```

5. 查看日志
```bash
docker-compose logs -f
```

### 手动部署

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 设置环境变量
```bash
export NOTION_TOKEN="your_notion_token"
export NOTION_DATABASE_ID="your_database_id"
export NOTION_HOLDINGS_DATABASE_ID="your_holdings_database_id"
```

3. 使用Gunicorn作为生产服务器
```bash
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"
```

## Docker镜像构建与推送

项目提供了便捷的脚本用于构建和推送Docker镜像:

```bash
# 构建并推送镜像
./scripts/build_and_push.sh
```

脚本会自动完成以下操作:
- 检查Docker是否安装
- 登录Docker Hub(如需)
- 构建Docker镜像
- 标记镜像版本
- 推送镜像到Docker Hub

### WSL环境Docker构建

如果您在WSL（Windows Subsystem for Linux）环境中，可以使用以下命令直接构建和推送：

```bash
# 构建镜像（使用Windows Docker Desktop）
docker.exe build -t treydong/notion-csv-importer:latest .

# 推送镜像到Docker Hub
docker.exe push treydong/notion-csv-importer:latest
```

这种方法利用WSL与Windows Docker Desktop的集成，无需在WSL中启动Docker守护进程。

### 直接拉取使用

您也可以直接拉取已构建的镜像：

```bash
# 拉取最新镜像
docker pull treydong/notion-csv-importer:latest

# 使用docker-compose启动
docker-compose up -d
```

## 配置说明
### 环境变量

变量名 | 描述 | 必需 |
|---------|------|------|
| NOTION_TOKEN | Notion API集成token | 是 |
| NOTION_DATABASE_ID | 交易记录数据库ID | 是 |
| NOTION_HOLDINGS_DATABASE_ID | 持仓记录数据库ID | 是 |
| CSV_ENCODING | CSV文件编码（默认gbk） | 否 |

### Notion数据库要求

#### 交易记录数据库

必须包含以下字段：
- 证券代码（文本）
- 证券名称（文本）
- 委托编号（文本）
- 交易日期（日期）
- 股票持仓（关联）

#### 持仓记录数据库

建议包含以下字段：
- 证券代码（文本）
- 股票（标题）：格式为"股票名称(股票代码)"
- 市场（选择）
- 证券类型（选择）
- 交易所代码（文本）
- 建仓日期（日期）
- 持仓数量（数字）
- 成本价（数字）

## 使用说明

1. 准备CSV文件，确保包含必要的列（证券代码、证券名称、委托编号等）
2. 访问Web界面并上传CSV文件
3. 配置导入参数（行数限制、批量大小、请求间隔等）
4. 点击"上传并导入"按钮
5. 系统会自动处理数据，创建持仓记录关联，并导入交易记录

## 注意事项

- 系统会自动跳过重复的委托编号
- 如果持仓记录不存在，系统会自动创建
- 股票字段会按照"股票名称(股票代码)"格式填充
- 建议使用较小的批量大小和适当的请求间隔，避免API限制

## 故障排除

### 常见问题

1. **导入失败**
   - 检查环境变量是否正确配置
   - 确认Notion数据库权限
   - 查看容器日志：`docker-compose logs`

2. **中文乱码**
   - 尝试不同的文件编码（GBK、UTF-8等）
   - 确保CSV文件使用正确的编码保存

3. **持仓记录未创建**
   - 检查持仓数据库结构是否包含必要字段
   - 确认API权限

## 贡献

欢迎提交问题和功能请求！

## 许可证

MIT License