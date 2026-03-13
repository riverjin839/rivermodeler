"""
애플리케이션 설정 - 환경변수 기반 구성
K8s 환경에서 Pod env로 주입되는 값들을 관리
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Neo4j (GraphRAG / Ontology) ---
    neo4j_uri: str = "bolt://neo4j-service:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "neo4jpassword"

    # --- ChromaDB (Vector RAG) ---
    chromadb_host: str = "http://chromadb-service:8000"

    # --- Ollama (LLM 서빙) ---
    ollama_base_url: str = "http://ollama-service:11434"
    ollama_model: str = "exaone3"

    # --- ML Serving ---
    ml_serving_url: str = "http://ml-serving-service:8081"

    class Config:
        env_file = ".env"


settings = Settings()
