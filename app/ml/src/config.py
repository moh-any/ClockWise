"""
Configuration loader for Surge Detection System.
Loads settings from environment variables with defaults.
"""

import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if it exists
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded environment from {env_path}")
else:
    print(f"⚠️  No .env file found at {env_path}")
    print(f"   Create one from .env.example")


class SurgeDetectionConfig:
    """Configuration for surge detection system."""
    
    # Database (backend team configures)
    DATABASE_URL: Optional[str] = os.getenv('DATABASE_URL')
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_PORT: int = int(os.getenv('DB_PORT', '5432'))
    DB_NAME: str = os.getenv('DB_NAME', 'deloitte')
    DB_USER: str = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', '')
    
    # Social Media APIs
    TWITTER_BEARER_TOKEN: Optional[str] = os.getenv('TWITTER_BEARER_TOKEN')
    EVENTBRITE_API_KEY: Optional[str] = os.getenv('EVENTBRITE_API_KEY')
    
    # Alert System (Layer 3)
    TWILIO_ACCOUNT_SID: Optional[str] = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN: Optional[str] = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER: Optional[str] = os.getenv('TWILIO_PHONE_NUMBER')
    SENDGRID_API_KEY: Optional[str] = os.getenv('SENDGRID_API_KEY')
    SLACK_WEBHOOK_URL: Optional[str] = os.getenv('SLACK_WEBHOOK_URL')
    
    # LLM Analysis (Layer 3)
    ANTHROPIC_API_KEY: Optional[str] = os.getenv('ANTHROPIC_API_KEY')
    
    # Data Collection
    DATA_COLLECTION_INTERVAL: int = int(os.getenv('DATA_COLLECTION_INTERVAL', '300'))
    ML_MODEL_PATH: str = os.getenv('ML_MODEL_PATH', 'data/models/rf_model.joblib')
    
    # Surge Detection
    SURGE_THRESHOLD: float = float(os.getenv('SURGE_THRESHOLD', '1.5'))
    SURGE_WINDOW_HOURS: int = int(os.getenv('SURGE_WINDOW_HOURS', '3'))
    SURGE_MIN_EXCESS_ITEMS: int = int(os.getenv('SURGE_MIN_EXCESS_ITEMS', '20'))
    SURGE_COOLDOWN_HOURS: int = int(os.getenv('SURGE_COOLDOWN_HOURS', '2'))
    SURGE_LLM_THRESHOLD: float = float(os.getenv('SURGE_LLM_THRESHOLD', '0.7'))
    
    # Cost Control
    MAX_DAILY_LLM_COST: float = float(os.getenv('MAX_DAILY_LLM_COST', '10.0'))
    MAX_DAILY_SMS_COST: float = float(os.getenv('MAX_DAILY_SMS_COST', '5.0'))
    
    # Logging & Monitoring
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: str = os.getenv('LOG_FILE', 'logs/surge_detection.log')
    METRICS_ENABLED: bool = os.getenv('METRICS_ENABLED', 'true').lower() == 'true'
    METRICS_PORT: int = int(os.getenv('METRICS_PORT', '9090'))
    
    @classmethod
    def validate(cls) -> dict:
        """
        Validate configuration and return status.
        
        Returns:
            Dict with validation results and warnings
        """
        warnings = []
        errors = []
        
        # Check required APIs for Layer 1
        if not cls.TWITTER_BEARER_TOKEN:
            warnings.append("Twitter API not configured - social signals will be limited")
        
        if not cls.EVENTBRITE_API_KEY:
            warnings.append("Eventbrite API not configured - event detection disabled")
        
        # Check model path
        model_path = Path(cls.ML_MODEL_PATH)
        if not model_path.exists():
            warnings.append(f"ML model not found at {cls.ML_MODEL_PATH} - using fallback predictions")
        
        if not cls.DATABASE_URL:
            warnings.append("DATABASE_URL not set - backend team should configure")
        
        if cls.SURGE_THRESHOLD < 1.0:
            errors.append(f"SURGE_THRESHOLD must be >= 1.0 (got {cls.SURGE_THRESHOLD})")
        
        if cls.SURGE_WINDOW_HOURS < 1:
            errors.append(f"SURGE_WINDOW_HOURS must be >= 1 (got {cls.SURGE_WINDOW_HOURS})")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    @classmethod
    def print_status(cls):
        """Print configuration status to console."""
        print("\n" + "="*70)
        print("SURGE DETECTION SYSTEM - CONFIGURATION STATUS")
        print("="*70)
        
        validation = cls.validate()
        
        print("\n🔧 CORE SETTINGS:")
        print(f"   Database: {cls.DATABASE_URL or 'Not configured (backend team)'}")
        print(f"   Collection Interval: {cls.DATA_COLLECTION_INTERVAL}s")
        print(f"   Model Path: {cls.ML_MODEL_PATH}")
        
        print("\n📱 SOCIAL MEDIA APIs:")
        print(f"   Twitter: {'✅' if cls.TWITTER_BEARER_TOKEN else '❌'}")
        print(f"   Eventbrite: {'✅' if cls.EVENTBRITE_API_KEY else '❌'}")
        
        print("\n🚨 SURGE DETECTION:")
        print(f"   Threshold: {cls.SURGE_THRESHOLD}x")
        print(f"   Window: {cls.SURGE_WINDOW_HOURS} hours")
        print(f"   Min Excess: {cls.SURGE_MIN_EXCESS_ITEMS} items/hour")
        print(f"   Cooldown: {cls.SURGE_COOLDOWN_HOURS} hours")
        
        print("\n📊 COST CONTROL:")
        print(f"   Max LLM Cost/Day: ${cls.MAX_DAILY_LLM_COST}")
        print(f"   Max SMS Cost/Day: ${cls.MAX_DAILY_SMS_COST}")
        
        if validation['warnings']:
            print("\n⚠️  WARNINGS:")
            for warning in validation['warnings']:
                print(f"   • {warning}")
        
        if validation['errors']:
            print("\n❌ ERRORS:")
            for error in validation['errors']:
                print(f"   • {error}")
        else:
            print("\n✅ Configuration validated successfully")
        
        print("="*70 + "\n")


# Create singleton instance
config = SurgeDetectionConfig()


if __name__ == "__main__":
    # Demo: print configuration status
    config.print_status()
