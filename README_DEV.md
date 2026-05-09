# SmartExamSystem 开发者指南

## 项目简介

智能做题系统 - 基于 FastAPI + Vue 3 的试卷解析与练习平台。

## 环境要求

- Python 3.10+
- Node.js 18+ / npm

---

## 后端启动指南

### 1. 创建虚拟环境

```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动开发服务器

```bash
uvicorn main:app --reload
```

服务器将在 `http://127.0.0.1:8000` 启动。

---

## 前端启动指南

### 1. 进入前端目录

```bash
cd frontend
```

### 2. 安装依赖

```bash
npm install
```

### 3. 启动开发服务器

```bash
npm run dev
```

前端服务默认运行在 `http://localhost:5173`。

### 4. 构建生产版本

```bash
npm run build
```

构建产物将输出到 `frontend/dist` 目录。

---

## 大模型 API 配置

### 方式一：前端配置

1. 启动应用后，进入「大模型设置」页面
2. 填写以下参数：
   - API Key: 你的 OpenAI API Key
   - Base URL: API 端点（默认 `https://api.openai.com/v1`）
   - Model: 模型名称（默认 `gpt-3.5-turbo`）

### 方式二：环境变量

在项目根目录创建 `.env` 文件：

```env
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-3.5-turbo
```

### 注意事项

- 使用国内代理或自定义 API 时，请修改 Base URL
- 确保 API Key 有足够的余额和权限
- 建议使用环境变量方式保存敏感信息

---

## 项目结构

```
SmartExamSystem/
├── main.py                    # 后端 FastAPI 主文件
├── requirements.txt           # Python 依赖
├── frontend/                  # Vue 前端项目
│   ├── src/
│   │   ├── components/        # Vue 组件
│   │   ├── App.vue            # 主应用
│   │   └── main.js            # 入口文件
│   ├── package.json           # npm 依赖
│   └── vite.config.js         # Vite 配置
└── README_DEV.md              # 开发者文档
```

---

## 功能模块

| 模块 | 描述 |
|------|------|
| 解析与校对台 | 上传 docx/pdf 文件，AI 提取题目，支持手动编辑 |
| 练习模式 | 即时答题，实时反馈答案对错 |
| 考试模式 | 模拟考试环境，随机组卷，交卷后评分 |
| 大模型设置 | 配置 OpenAI API 参数 |

---

## 支持题型

- 单选题 (single)
- 多选题 (multiple)
- 判断题 (judge)
- 填空题 (fill)
- 简答题 (essay)
