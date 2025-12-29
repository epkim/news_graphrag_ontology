"""환경변수 로드 및 설정 관리"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # Supabase (REST API 방식)
    supabase_url: str  # Supabase 프로젝트 URL
    supabase_key: str  # Supabase API Key (anon key 또는 service_role key)
    
    # Neo4j
    neo4j_uri: str
    neo4j_username: str
    neo4j_password: str
    neo4j_database: str = "neo4j"
    
    # LLM Provider
    llm_provider: str = "openai"  # openai, anthropic, ollama
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama2"
    
    # Embedding
    embedding_provider: str = "local"  # local, openai
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    openai_embedding_model: str = "text-embedding-3-small"
    
    # Chunking
    chunk_size: int = 500
    chunk_overlap: int = 50
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

