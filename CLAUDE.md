# Faultless — AI 工程文档审查系统

## 技术栈
Python, Django, LangChain, Langfuse, Gemini API

## 启动命令
python manage.py runserver

## 关键文件
- llm.py：LLM 调用层，接 Gemini API，Langfuse 观测包在外层
- views.py：Django 视图，处理文档上传和审查流程
- prompts.csv：Prompt 模板，所有 System Prompt 存这里
- smart_comment/：去重算法，合并多个 Agent 的 JSON 输出

## 环境变量
GEMINI_API_KEY 和 LANGFUSE_SECRET_KEY 在 .env 文件里

## 当前任务
测试重写后的 Summary prompt，对比原版和新版的输出质量差异