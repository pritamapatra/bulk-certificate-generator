import os

DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
MAX_RECIPIENTS: int = int(os.getenv("MAX_RECIPIENTS", "1000"))
GENERATED_DIR: str = os.getenv("GENERATED_DIR", "generated")
