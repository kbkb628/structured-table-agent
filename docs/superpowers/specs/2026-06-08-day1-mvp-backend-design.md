# 第 1 天 MVP 骨架与数据闭环设计

## 1. 目标

本设计严格遵循 [DEVELOPMENT_GUIDE.md](/e:/bgagent1/DEVELOPMENT_GUIDE.md) 中“第 1 天：项目骨架 + 数据闭环”的要求，仅实现真实可跑的最小后端闭环：

- 上传销售订单 CSV
- 生成字段画像
- 将文件元数据与画像写入 SQLite
- 基于真实 CSV 执行 `groupby_aggregate`
- 统一返回 `ToolResponse`

本设计不提前实现以下能力：

- `LangGraph`
- `Redis`
- 轻量 `RAG`
- 分析任务接口
- 事件 `Trace`
- 图表生成
- 报告生成
- `RuleScorer`

## 2. 设计原则

设计和实现必须遵守以下原则：

- 严格以指导文档为准，不擅自调整阶段策略和接口边界。
- 只做真实能力，不做假上传、假聚合、假持久化、假工具调用。
- 第 1 天只完成文档明确要求的数据闭环，不把第二阶段能力混入 MVP。
- 代码目录名尽量与指导文档推荐结构保持一致，避免后续返工。
- 所有响应结构、字段命名和错误语义优先服从指导文档。

## 3. 实现范围

### 3.1 必做能力

- FastAPI 应用骨架
- `POST /api/files/upload`
- `GET /api/files/{file_id}/profile`
- SQLite 最小持久化
- CSV 真实解析
- 字段画像生成
- `groupby_aggregate` 工具
- 统一 `ToolResponse`
- 样例销售订单数据
- 上传、画像、聚合测试

### 3.2 明确延后

以下能力虽在总项目范围内，但不进入第 1 天实现：

- `/api/analysis/start`
- `/api/analysis/{task_id}/run`
- Agent 状态字段
- MockLLM
- 本地知识库与检索
- 事件表与事件时间线接口
- 图表工具
- 报告工具
- 规则评分器

## 4. 目录设计

第 1 天按如下目录创建最小实现：

```text
backend/
  app/
    main.py
    api/
      files.py
    core/
      config.py
      exceptions.py
    schemas/
      file_schema.py
      tool_schema.py
    storage/
      database.py
      models.py
      file_store.py
    tools/
      data_profile.py
      duckdb_tools.py
  data/
    uploads/
    samples/
      sales_orders.csv
  tests/
  README.md
```

说明：

- 目录名对齐指导文档推荐结构。
- 仅创建第 1 天必要文件，不预先填充未用模块。
- `README.md` 至少记录启动、依赖、样例数据和最小验证方式。

## 5. 模块职责

### `app/main.py`

- 创建 FastAPI 应用。
- 注册文件相关路由。
- 在启动时初始化数据库和必要目录。

### `app/api/files.py`

- 负责文件上传接口。
- 负责字段画像查询接口。
- 仅处理 HTTP 请求/响应，不承载聚合业务。

### `app/core/config.py`

- 管理 SQLite 文件路径、上传目录、样例数据目录等基础配置。

### `app/core/exceptions.py`

- 定义项目内常见业务异常，统一接口错误处理。

### `app/schemas/file_schema.py`

- 定义字段元信息 Schema。
- 定义字段画像 Schema。
- 定义上传响应 Schema。

### `app/schemas/tool_schema.py`

- 定义统一 `ToolResponse`。
- 定义 `groupby_aggregate` 请求参数和错误结构。

### `app/storage/database.py`

- 提供 SQLite 初始化逻辑。
- 建立数据库连接和建表入口。

### `app/storage/models.py`

- 覆盖第 1 天最小数据表：`files`。
- `files` 表包含：
  - `file_id`
  - `filename`
  - `stored_path`
  - `row_count`
  - `column_count`
  - `columns_json`
  - `created_at`

### `app/storage/file_store.py`

- 保存上传文件。
- 写入和读取 `files` 元数据。
- 通过 `file_id` 查找文件记录和真实路径。

### `app/tools/data_profile.py`

- 读取真实 CSV。
- 生成字段画像：
  - 列名
  - 推断类型
  - 缺失率
  - 样例值
  - 唯一值数量
  - 行数
  - 列数

### `app/tools/duckdb_tools.py`

- 实现 `groupby_aggregate`。
- 基于 `file_id` 找到真实 CSV 文件。
- 使用 DuckDB 对 CSV 执行真实聚合。
- 返回统一 `ToolResponse`。

## 6. 数据流设计

### 上传与画像

1. 客户端调用 `POST /api/files/upload`
2. 服务校验扩展名是否为 `csv`
3. 文件保存到 `backend/data/uploads/`
4. 使用 `pandas` 读取 CSV
5. 生成字段画像
6. 将文件元数据和字段画像 JSON 写入 SQLite `files` 表
7. 返回上传响应

### 查询字段画像

1. 客户端调用 `GET /api/files/{file_id}/profile`
2. 服务通过 `file_id` 查询 SQLite `files` 表
3. 返回已保存的字段画像

### 聚合工具

1. 通过 `file_id` 从 `files` 表查到真实文件路径
2. 校验 `group_by` 与 `metric_column` 是否存在于字段画像
3. 使用 DuckDB 读取 CSV 并执行分组聚合
4. 对结果执行排序与限制条数
5. 返回统一 `ToolResponse`

## 7. API 契约

第 1 天仅实现以下已冻结接口。

### 7.1 上传文件

`POST /api/files/upload`

请求：

- `multipart/form-data`
- 字段名：`file`

响应结构必须对齐指导文档：

```json
{
  "file_id": "file_xxx",
  "filename": "sales_orders.csv",
  "row_count": 1000,
  "column_count": 10,
  "columns": [
    {
      "name": "product_category",
      "type": "string",
      "missing_rate": 0.0,
      "sample_values": ["办公用品", "电子产品"],
      "unique_count": 8
    }
  ],
  "created_at": "2026-06-08T18:00:00"
}
```

### 7.2 查询字段画像

`GET /api/files/{file_id}/profile`

响应结构与上传结果一致，只是不重复文件存储行为。

## 8. ToolResponse 契约

第 1 天必须实现统一 `ToolResponse`，字段与指导文档保持一致：

```json
{
  "success": true,
  "tool_name": "groupby_aggregate",
  "data": {},
  "summary": "按品类统计销售额并返回 Top5",
  "error": null,
  "metadata": {
    "columns_used": ["product_category", "sales_amount"],
    "row_count": 5,
    "elapsed_ms": 126
  }
}
```

失败结构：

```json
{
  "success": false,
  "tool_name": "groupby_aggregate",
  "data": null,
  "summary": "工具执行失败",
  "error": {
    "code": "FIELD_NOT_FOUND",
    "message": "字段 sales_amount 不存在",
    "suggested_fields": ["amount", "total_amount"]
  },
  "metadata": {
    "elapsed_ms": 12
  }
}
```

## 9. 聚合工具约束

`groupby_aggregate` 输入契约：

```json
{
  "file_id": "file_xxx",
  "group_by": "product_category",
  "metric_column": "sales_amount",
  "aggregation": "sum",
  "sort_order": "desc",
  "limit": 5
}
```

约束：

- `group_by` 必须存在于字段画像中
- `metric_column` 必须存在于字段画像中
- `aggregation` 仅允许：`sum`、`avg`、`count`、`min`、`max`
- `sort_order` 仅允许：`asc`、`desc`
- `limit` 默认 10，最大 100
- 非数值指标列不允许进行 `sum`、`avg`、`min`、`max`

## 10. 错误处理策略

第 1 天仅实现与数据闭环直接相关的错误处理：

- 非 `csv` 文件上传：返回明确错误
- 空文件：返回明确错误
- CSV 解析失败：返回明确错误
- 编码错误：允许有限降级尝试，不成功则返回解析错误
- 查询不存在的 `file_id`：返回 `404`
- `groupby_aggregate` 字段不存在：返回失败 `ToolResponse`
- 指标字段非数值：返回失败 `ToolResponse`

约束：

- 不允许悄悄降级为伪结果
- 不允许在失败时仍返回成功结构
- 不允许编造聚合结果

## 11. 样例数据要求

第 1 天样例数据使用销售订单 CSV，并尽量符合指导文档建议字段：

```text
order_id
customer_id
order_date
region
channel
product_category
product_name
quantity
sales_amount
discount
order_status
```

样例数据至少满足：

- 可用于按 `product_category` 聚合 `sales_amount`
- 至少有 5 个品类
- 至少包含 `completed`、`cancelled`、`refunded`
- 可支持“品类销售额 Top5”演示

## 12. 测试与验收

### 最低测试

- 文件上传测试
- 字段画像测试
- `groupby_aggregate` 工具测试

### 验收标准

- Swagger 能上传真实 CSV
- 上传接口返回真实字段画像
- `GET /api/files/{file_id}/profile` 能返回持久化后的画像
- SQLite 中存在 `files` 表且能查回文件元数据
- `groupby_aggregate` 能基于真实 CSV 返回品类销售额 Top5
- 工具返回结构统一符合 `ToolResponse`

## 13. 非目标声明

为避免简历表述和代码现实脱节，第 1 天不得声称已实现：

- Agent 状态流
- 动态任务规划
- 业务语义检索
- 多轮记忆
- 事件时间线
- 图表配置生成
- 报告生成
- 规则评分器
- LLM-as-Judge
- DockerSandbox

## 14. 后续衔接

第 1 天完成后，第 2 天才能在此骨架上继续接入：

- 分析任务接口
- `match_fields`
- 图表与报告工具
- 事件记录
- 完整任务状态查询

第 3 天后再进入：

- `LangGraph`
- MockLLM
- 轻量 `RAG`

本顺序不得颠倒。
