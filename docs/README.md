# CSV到Notion导入工具

这是一个用于将CSV文件中的股票交易记录导入到Notion数据库的Web应用程序。它支持自动创建持仓记录并建立关联关系。

## 功能特点

- 📊 支持CSV文件上传和解析
- 🔗 自动关联交易记录与持仓记录
- ➕ 如果持仓记录不存在，自动创建
- 🚫 自动跳过重复的交易记录（基于委托编号）
- 🌐 简单易用的Web界面
- 🐳 Docker容器化部署

## 使用方法

### 使用Docker（推荐）

1. 拉取镜像：
```bash
docker pull treydong/csv-to-notion-app:latest
```

2. 运行容器：
```bash
docker run -d -p 8000:8000 \
  -e NOTION_TOKEN="your_notion_token" \
  -e NOTION_DATABASE_ID="your_database_id" \
  -e NOTION_HOLDINGS_DATABASE_ID="your_holdings_database_id" \
  treydong/csv-to-notion-app:latest
```

3. 访问 http://localhost:8000 使用Web界面

### 本地运行

1. 克隆仓库并安装依赖：
```bash
pip install -r requirements.txt
```

2. 设置环境变量：
```bash
export NOTION_TOKEN="your_notion_token"
export NOTION_DATABASE_ID="your_database_id"
export NOTION_HOLDINGS_DATABASE_ID="your_holdings_database_id"
```

3. 运行应用：
```bash
python app.py
```

## 环境变量配置

- `NOTION_TOKEN`: Notion API集成令牌
- `NOTION_DATABASE_ID`: 交易记录数据库ID
- `NOTION_HOLDINGS_DATABASE_ID`: 持仓记录数据库ID

## CSV文件格式

CSV文件应包含以下列（列名需要与Notion数据库属性匹配）：

- 证券代码
- 证券名称
- 委托方向
- 成交数量
- 成交均价
- 成交金额
- 佣金
- 其他费用
- 印花税
- 过户费
- 资金余额
- 委托编号
- 交易市场
- 成交日期
- 成交时间

## 工作流程

1. 用户上传CSV文件
2. 应用解析CSV文件内容
3. 对于每条交易记录：
   - 检查委托编号是否已存在，避免重复导入
   - 查询持仓数据库中是否存在对应的股票记录
   - 如果不存在，自动创建新的持仓记录
   - 创建交易记录并与持仓记录建立关联
4. 返回导入结果

## 技术栈

- Python 3.9
- FastAPI
- Pandas
- Requests
- Docker

## 注意事项

- 确保Notion API令牌有足够的权限访问和修改数据库
- 持仓数据库需要包含"证券代码"和"证券名称"字段
- 交易数据库需要包含"股票持仓"关系字段
- 建议在导入前备份Notion数据库

## 许可证

MIT License