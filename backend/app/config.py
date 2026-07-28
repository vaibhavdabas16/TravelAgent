"""Application configuration management using pydantic-settings."""
import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Google API Keys
    google_maps_api_key: str
    gemini_api_key: str
    gemini_api_key_1: Optional[str] = None
    gemini_api_key_2: Optional[str] = None
    gemini_api_key_3: Optional[str] = None

    @property
    def gemini_api_keys(self) -> list[str]:
        keys = [self.gemini_api_key, self.gemini_api_key_1, self.gemini_api_key_2, self.gemini_api_key_3]
        return [k for k in keys if k]
    
    # Amadeus API (Phase 2.3)
    amadeus_api_key: str
    amadeus_api_secret: str
    amadeus_base_url: str = "https://test.api.amadeus.com"  # or https://api.amadeus.com for production
    
    # SerpAPI (Phase 2.3 - Week 5)
    serpapi_api_key: str = "demo"  # Default demo key
    
    # SearchApi.io (Phase 4)
    search_api_key: Optional[str] = None
    search_api_key1: Optional[str] = None
    search_api_key2: Optional[str] = None
    search_api_key3: Optional[str] = None
    search_api_key4: Optional[str] = None
    
    @property
    def search_api_keys(self) -> list[str]:
        keys = [self.search_api_key, self.search_api_key1, self.search_api_key2, self.search_api_key3, self.search_api_key4]
        return [k for k in keys if k]
    
    # Environment
    environment: str = "development"
    log_level: str = "INFO"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS - Support for ngrok and custom origins
    cors_origins: str = "http://localhost:3000,http://localhost:3001,http://localhost:5173,http://localhost:5174,http://127.0.0.1:3000,http://127.0.0.1:8000"
    
    # Additional CORS origins for ngrok (comma-separated)
    # Example: "https://abc123.ngrok-free.app,https://xyz789.ngrok-free.app"
    additional_cors_origins: str = ""
    
    @property
    def all_cors_origins(self) -> list[str]:
        """Get all CORS origins including ngrok URLs."""
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        
        # Add additional origins (like ngrok URLs)
        if self.additional_cors_origins:
            additional = [o.strip() for o in self.additional_cors_origins.split(",") if o.strip()]
            origins.extend(additional)
        
        return origins
    
    # Database (Phase 2.2)
    database_host: str = "localhost"
    database_port: int = 5433  # Changed from 5432 to avoid conflicts with local PostgreSQL
    database_name: str = "travel_agent"
    database_user: str = "postgres"
    database_password: str = "postgres"
    
    # Vector Database - Pinecone (Phase 2.2)
    pinecone_api_key: str = "your-pinecone-api-key"
    pinecone_environment: str = "gcp-starter"  # Free tier
    pinecone_index_name: str = "travel-agent-pois"
    
    # Redis Cache (Phase 2.4)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # Authentication (Phase 2.2)
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60 * 24 * 7  # 7 days
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()

