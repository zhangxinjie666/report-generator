# 实验报告智能生成系统 (Report Generator)

通过 AI 自动生成实验报告的全栈项目，用于学习 AI 应用开发技术。

## 项目状态

当前版本：**v1 MVP 规划中**

## 文档

- [产品说明文档 (PRD)](./docs/PRD.md)
- [技术选型文档](./docs/技术选型.md)

## 技术栈

- 后端：FastAPI + LangChain + Chroma
- LLM：智谱 GLM-4.5-Flash（免费）
- Embedding：本地 bge-small-zh
- 文档处理：python-docx + pymupdf

## 目录结构

```
report-generator/
├── backend/     # FastAPI 后端
├── assets/      # 模板、参考报告等素材
├── docs/        # 产品与技术文档
└── README.md
```

## 迭代路线

| 版本 | 功能 |
|---|---|
| v1 | 规则编排 + RAG + LLM 生成 + 导出 |
| v2 | 多模态（VLM 识别手写表格） |
| v3 | 前端界面 |
| v4 | Agent 化编排 |
| v5 | 数据库 + 历史记录 |
| v6 | 多用户 + 鉴权 |
| v7 | 工程化补齐 |
| v8 | MCP 集成 |
| ... | ... |

## 学习目标

本项目服务于 AI 全栈 / Agent 开发工程师的学习目标，每个版本对应一组核心技术的学习。
