"""
Configuración de la aplicación usando variables de entorno.
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

class Settings:
    """Configuración de la aplicación."""
    
    # Base de datos
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_BUCKET: str = os.getenv("SUPABASE_BUCKET", "sentencias")
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Configuración general
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

# Instancia global de configuración
settings = Settings()