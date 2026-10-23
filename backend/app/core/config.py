"""配置中心。

所有可变的配置（密钥、模型名、目录）都放在 backend/.env 里，
这里通过 pydantic-settings 读取并做类型校验：
    - .env 缺失字段 -> 用默认值
    - .env 写了但类型不对 -> 启动时直接报错，不会带着错配置跑
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/ 目录，用于拼出各资源目录的绝对路径
BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "实验报告智能生成系统"

    # LLM（智谱 OpenAI 兼容接口）
    llm_api_key: str = ""
    llm_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    llm_model: str = "glm-4.5-flash"

    # 本地 embedding 模型
    embedding_model: str = "BAAI/bge-small-zh-v1.5"

    # 目录
    assets_dir: Path = BACKEND_DIR.parent / "assets"
    output_dir: Path = BACKEND_DIR.parent / "assets" / "generated"
    chroma_dir: Path = BACKEND_DIR.parent / "assets" / "chroma_db"


settings = Settings()

# 确保输出目录存在，后面写生成的 docx/PDF 时不用再判断
settings.output_dir.mkdir(parents=True, exist_ok=True)
