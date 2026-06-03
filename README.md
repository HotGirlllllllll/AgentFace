# AgentFace — 美颜 Agent 系统

基于 **LangGraph**（记忆与确定性大脑）+ **Microsoft Agent Framework**（模型调度与安全护栏）的智能美颜 Agent 系统。

## 架构

```
用户 → FastAPI → LangGraph "Brain" (状态机+记忆)
                      │
                 Bridge Layer
                      │
                MAF "Body" (模型编排+安全)
                      │
              ┌───────┴───────┐
        多模态模型:8001   美颜模型:8002
```

| 职责 | LangGraph | MAF |
|------|-----------|-----|
| 工作流状态机 | ✅ | - |
| 短期记忆 (Checkpointer) | ✅ | - |
| 长期记忆 (Store) | ✅ | - |
| 用户偏好演化 (EMA) | ✅ | - |
| 模型调用/调度 | - | ✅ |
| A2A 通信 | - | ✅ |
| MCP 工具协议 | - | ✅ |
| 内容安全过滤 | - | ✅ |
| VRAM 溢出防护 | - | ✅ |

## 快速开始

### 开发模式

```bash
# 1. 安装依赖
pip install -e ".[dev]"

# 2. 配置环境变量
cp .env.example .env

# 3. 启动所有服务（主应用 + 两个模型服务）
./scripts/run_dev.sh
```

### Docker

```bash
docker compose -f docker/docker-compose.yml up
```

### 运行测试

```bash
pytest tests/ -v
```

## API 端点

```
POST   /api/v1/sessions                 创建美颜会话
GET    /api/v1/sessions/{id}            查询会话状态
POST   /api/v1/sessions/{id}/confirm    确认/调整方案 (HITL)
POST   /api/v1/sessions/{id}/feedback   提交反馈 (HITL)
GET    /api/v1/users/{id}/preferences    获取用户偏好
GET    /api/v1/users/{id}/history        历史会话
DELETE /api/v1/sessions/{id}            放弃会话
GET    /api/v1/health                    健康检查
```

## HITL 工作流

1. **创建会话** → 上传图片
2. **方案确认** → 查看分析结果，确认或调整参数
3. **提交反馈** → 查看美颜结果，评分 1-5
4. **记忆更新** → 满意度 ≥ 3 自动更新偏好 (EMA)

## 项目结构

```
src/agent_face/
├── main.py                   # FastAPI 入口
├── config.py                 # pydantic-settings
├── api/                      # REST API 层
├── langgraph_brain/          # LangGraph "大脑"
│   ├── state.py              # 状态定义
│   ├── graph.py              # StateGraph 编译
│   ├── nodes/                # 9 个节点
│   ├── routing.py            # 条件路由
│   └── memory/               # 偏好/历史/反馈
├── maf_body/                 # MAF "身体"
│   ├── orchestrator.py       # DAG 编排器
│   ├── agents/               # 3 个 Agent
│   ├── tools/                # MCP 工具
│   └── middleware/           # 安全中间件
├── bridge/                   # 桥接层
├── models/                   # 模型 HTTP 客户端
└── shared/                   # 工具函数
```
