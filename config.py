import os

# 优先读环境变量（GitHub Actions Secrets 注入），本地开发可在项目根目录放 .env 文件
API_KEY = os.environ.get("OPENAI_API_KEY", "")
BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai-proxy.org/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4.1-mini")
