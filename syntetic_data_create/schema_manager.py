# schema_manager.py

"""
Schema Manager - Handles both Swagger/OpenAPI files and Definition files
Creates databases from either format and can convert between them.
"""

import json
import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import logging
from datetime import datetime

from syntetic_data_create.database_generator import create_generator, DatabaseGenerator
from syntetic_data_create.swagger_db_integration import EnhancedSwaggerSchemaGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SchemaManager:
    """
    Manages schema files and database generation from multiple sources:
    1. Swagger/OpenAPI files (.json, .yaml, .yml)
    2. Definition files (.json) - simplified database schema format
    3. Built-in default schemas
    """
    
    def __init__(self, schemas_dir: str = "schemas"):
        """
        Initialize the Schema Manager.
        
        Args:
            schemas_dir: Directory to store schema files
        """
        self.schemas_dir = Path(schemas_dir)
        self.schemas_dir.mkdir(exist_ok=True)
        
        # Initialize paths
        self.swagger_file = self.schemas_dir / "israeli_banking_swagger.json"
        self.definition_file = self.schemas_dir / "israeli_banking_definition.json"
        
        logger.info(f"Schema Manager initialized with directory: {self.schemas_dir}")
    
    def create_default_files(self) -> Dict[str, str]:
        """
        Create both Swagger and Definition files from the current default schema.
        
        Returns:
            Dictionary with file paths created
        """
        logger.info("Creating default schema files from built-in schema")
        
        # Create Swagger file
        swagger_schema = self._create_default_swagger_schema()
        swagger_path = self._save_swagger_schema(swagger_schema)
        
        # Create Definition file  
        definition_schema = self._create_default_definition_schema()
        definition_path = self._save_definition_schema(definition_schema)
        
        logger.info(f"Created schema files: {swagger_path}, {definition_path}")
        
        return {
            "swagger_file": str(swagger_path),
            "definition_file": str(definition_path)
        }
    
    def _create_default_swagger_schema(self) -> Dict[str, Any]:
        """Create the default Swagger/OpenAPI schema for Israeli banking."""
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "Israeli Banking Data Generator API",
                "description": "API schema for generating Israeli banking synthetic data with Hebrew support",
                "version": "1.0.0",
                "contact": {
                    "name": "Israeli Banking Data Generator",
                    "email": "support@example.com"
                }
            },
            "servers": [
                {
                    "url": "https://api.israelibanking.example.com/v1",
                    "description": "Production server"
                }
            ],
            "components": {
                "schemas": {
                    "User": {
                        "type": "object",
                        "required": ["תעודת_זהות", "שם_פרטי", "שם_משפחה", "טלפון"],
                        "properties": {
                            "תעודת_זהות": {
                                "type": "string",
                                "description": "מספר תעודת זהות ישראלית (9 ספרות)",
                                "pattern": "^[0-9]{9}$",
                                "example": "123456782"
                            },
                            "שם_פרטי": {
                                "type": "string",
                                "description": "שם פרטי בעברית",
                                "maxLength": 50,
                                "example": "דוד"
                            },
                            "שם_משפחה": {
                                "type": "string", 
                                "description": "שם משפחה בעברית",
                                "maxLength": 50,
                                "example": "כהן"
                            },
                            "כתובת": {
                                "type": "string",
                                "description": "כתובת מגורים",
                                "maxLength": 200,
                                "example": "רחוב הרצל 15, תל אביב"
                            },
                            "עיר": {
                                "type": "string",
                                "description": "עיר מגורים",
                                "maxLength": 50,
                                "example": "תל אביב"
                            },
                            "טלפון": {
                                "type": "string",
                                "description": "מספר טלפון ישראלי",
                                "pattern": "^05[0-9]-[0-9]{7}$",
                                "example": "050-1234567"
                            },
                            "דואר_אלקטרוני": {
                                "type": "string",
                                "format": "email",
                                "description": "כתובת דואר אלקטרוני",
                                "example": "david.cohen@example.com"
                            },
                            "תאריך_יצירה": {
                                "type": "string",
                                "format": "date-time",
                                "description": "תאריך יצירת החשבון"
                            },
                            "סטטוס": {
                                "type": "string",
                                "enum": ["פעיל", "לא פעיל", "מושעה"],
                                "description": "סטטוס החשבון",
                                "default": "פעיל"
                            }
                        }
                    },
                    "Account": {
                        "type": "object",
                        "required": ["מספר_חשבון", "תעודת_זהות", "סוג_חשבון"],
                        "properties": {
                            "מספר_חשבון": {
                                "type": "string",
                                "description": "מספר חשבון בנק",
                                "maxLength": 15,
                                "example": "123456789012345"
                            },
                            "תעודת_זהות": {
                                "type": "string",
                                "description": "תעודת זהות בעל החשבון",
                                "pattern": "^[0-9]{9}$"
                            },
                            "סוג_חשבון": {
                                "type": "string", 
                                "enum": ["חשבון פרטי", "חשבון עסקי", "חשבון חיסכון"],
                                "description": "סוג החשבון"
                            },
                            "יתרה": {
                                "type": "number",
                                "format": "float",
                                "description": "יתרת החשבון בשקלים",
                                "minimum": 0,
                                "maximum": 1000000,
                                "example": 15000.50
                            },
                            "מסגרת_אשראי": {
                                "type": "integer",
                                "description": "מסגרת אשראי בשקלים",
                                "minimum": 0,
                                "maximum": 100000,
                                "example": 25000
                            },
                            "אשראי_זמין": {
                                "type": "number",
                                "format": "float", 
                                "description": "אשראי זמין בשקלים",
                                "minimum": 0,
                                "example": 20000.00
                            },
                            "סניף_בנק": {
                                "type": "integer",
                                "description": "מספר סניף הבנק",
                                "minimum": 1,
                                "maximum": 999,
                                "example": 123
                            },
                            "תאריך_פתיחה": {
                                "type": "string",
                                "format": "date",
                                "description": "תאריך פתיחת החשבון"
                            },
                            "סטטוס": {
                                "type": "string",
                                "enum": ["פעיל", "חסום", "סגור"],
                                "description": "סטטוס החשבון",
                                "default": "פעיל"
                            }
                        }
                    },
                    "CreditCard": {
                        "type": "object",
                        "required": ["מספר_כרטיס", "תעודת_זהות", "סוג_כרטיס", "תוקף"],
                        "properties": {
                            "מספר_כרטיס": {
                                "type": "string",
                                "description": "מספר כרטיס האשראי",
                                "maxLength": 19,
                                "example": "4532123456789012"
                            },
                            "תעודת_זהות": {
                                "type": "string",
                                "description": "תעודת זהות בעל הכרטיס",
                                "pattern": "^[0-9]{9}$"
                            },
                            "סוג_כרטיס": {
                                "type": "string",
                                "enum": [
                                    "ויזה רגיל", "ויזה זהב", "ויזה פלטינום",
                                    "מאסטרקארד רגיל", "מאסטרקארד זהב", "מאסטרקארד פלטינום",
                                    "אמריקן אקספרס", "ישראכרט", "דביט רגיל",
                                    "מפתח דיסקונט רגיל", "FLY CARD מפתח דיסקונט"
                                ],
                                "description": "סוג כרטיס האשראי"
                            },
                            "תוקף": {
                                "type": "string",
                                "pattern": "^(0[1-9]|1[0-2])/[0-9]{2}$",
                                "description": "תאריך תפוגה (MM/YY)",
                                "example": "12/28"
                            },
                            "מסגרת_אשראי": {
                                "type": "integer",
                                "description": "מסגרת אשראי בכרטיס",
                                "minimum": 1000,
                                "maximum": 100000,
                                "example": 25000
                            },
                            "יתרה": {
                                "type": "number",
                                "format": "float",
                                "description": "יתרת חיוב נוכחית",
                                "minimum": 0,
                                "maximum": 100000,
                                "example": 3250.75
                            },
                            "תשלומים_אחרונים": {
                                "type": "number",
                                "format": "float",
                                "description": "סכום תשלומים אחרונים",
                                "minimum": 0,
                                "example": 1200.00
                            },
                            "תאריך_הנפקה": {
                                "type": "string",
                                "format": "date",
                                "description": "תאריך הנפקת הכרטיס"
                            },
                            "דירוג_אשראי": {
                                "type": "integer",
                                "description": "דירוג אשראי (300-850)",
                                "minimum": 300,
                                "maximum": 850,
                                "example": 720
                            },
                            "סטטוס": {
                                "type": "string",
                                "enum": ["פעיל", "חסום", "מושעה", "בוטל"],
                                "description": "סטטוס הכרטיס",
                                "default": "פעיל"
                            }
                        }
                    },
                    "Transaction": {
                        "type": "object",
                        "required": ["מספר_כרטיס", "תאריך_עסקה", "סכום", "שם_עסק"],
                        "properties": {
                            "מספר_כרטיס": {
                                "type": "string",
                                "description": "מספר כרטיס שבוצעה בו העסקה",
                                "maxLength": 19
                            },
                            "תאריך_עסקה": {
                                "type": "string",
                                "format": "date",
                                "description": "תאריך ביצוע העסקה"
                            },
                            "סכום": {
                                "type": "number",
                                "format": "float",
                                "description": "סכום העסקה בשקלים",
                                "minimum": 0.01,
                                "maximum": 50000,
                                "example": 150.75
                            },
                            "קטגוריה": {
                                "type": "string",
                                "enum": [
                                    "מזון ומשקאות", "קניות ואופנה", "בידור ותרבות",
                                    "דלק ותחבורה", "חשמל ומים", "תקשורת",
                                    "בריאות ורפואה", "חינוך", "ביטוח", "אחר"
                                ],
                                "description": "קטגוריית העסקה"
                            },
                            "שם_עסק": {
                                "type": "string",
                                "description": "שם בית העסק",
                                "maxLength": 100,
                                "example": "סופרמרקט רמי לוי"
                            },
                            "סוג_עסקה": {
                                "type": "string",
                                "enum": ["רגילה", "תשלומים", "קרדיט", "החזר"],
                                "description": "סוג העסקה",
                                "default": "רגילה"
                            },
                            "מספר_תשלומים": {
                                "type": "integer",
                                "enum": [1, 3, 6, 12, 24, 36],
                                "description": "מספר תשלומים (אם רלוונטי)",
                                "default": 1
                            },
                            "סטטוס": {
                                "type": "string",
                                "enum": ["נרשם", "ממתין", "מאושר", "נדחה", "בוטל"],
                                "description": "סטטוס העסקה",
                                "default": "נרשם"
                            },
                            "תיאור": {
                                "type": "string",
                                "description": "תיאור נוסף של העסקה",
                                "maxLength": 200
                            }
                        }
                    }
                }
            },
            "examples": {
                "SampleUser": {
                    "summary": "דוגמה למשתמש ישראלי",
                    "value": {
                        "תעודת_זהות": "123456782",
                        "שם_פרטי": "דוד",
                        "שם_משפחה": "כהן",
                        "כתובת": "רחוב הרצל 15, תל אביב",
                        "עיר": "תל אביב",
                        "טלפון": "050-1234567",
                        "דואר_אלקטרוני": "david.cohen@example.com",
                        "סטטוס": "פעיל"
                    }
                },
                "SampleCreditCard": {
                    "summary": "דוגמה לכרטיס אשראי",
                    "value": {
                        "מספר_כרטיס": "4532123456789012",
                        "תעודת_זהות": "123456782",
                        "סוג_כרטיס": "ויזא זהב",
                        "תוקף": "12/28",
                        "מסגרת_אשראי": 25000,
                        "יתרה": 3250.75,
                        "דירוג_אשראי": 720,
                        "סטטוס": "פעיל"
                    }
                }
            }
        }
    
    def _create_default_definition_schema(self) -> Dict[str, Any]:
        """Create the default definition schema (simplified format)."""
        return {
            "schema_info": {
                "name": "Israeli Banking Database Schema",
                "version": "1.0.0",
                "description": "Database schema for Israeli banking synthetic data generation",
                "created": datetime.now().isoformat(),
                "locale": "he_IL"
            },
            "tables": {
                "users": {
                    "description": "לקוחות הבנק",
                    "primary_key": "תעודת_זהות",
                    "fields": {
                        "תעודת_זהות": {
                            "type": "string",
                            "constraints": {"max_length": 9},
                            "description": "מספר תעודת זהות ישראלית",
                            "generator": "israeli_id"
                        },
                        "שם_פרטי": {
                            "type": "string",
                            "constraints": {"max_length": 50},
                            "description": "שם פרטי בעברית",
                            "generator": "hebrew_first_name"
                        },
                        "שם_משפחה": {
                            "type": "string",
                            "constraints": {"max_length": 50},
                            "description": "שם משפחה בעברית",
                            "generator": "hebrew_last_name"
                        },
                        "כתובת": {
                            "type": "string",
                            "constraints": {"max_length": 200},
                            "description": "כתובת מגורים",
                            "generator": "hebrew_address"
                        },
                        "עיר": {
                            "type": "string",
                            "constraints": {"max_length": 50},
                            "description": "עיר מגורים",
                            "generator": "hebrew_city"
                        },
                        "טלפון": {
                            "type": "string",
                            "constraints": {"max_length": 15},
                            "description": "מספר טלפון ישראלי",
                            "generator": "israeli_phone"
                        },
                        "דואר_אלקטרוני": {
                            "type": "string",
                            "constraints": {"max_length": 100},
                            "description": "כתובת דואר אלקטרוני",
                            "generator": "email"
                        },
                        "תאריך_יצירה": {
                            "type": "datetime",
                            "description": "תאריך יצירת החשבון",
                            "generator": "past_datetime"
                        },
                        "סטטוס": {
                            "type": "choice",
                            "constraints": {"choices": ["פעיל", "לא פעיל", "מושעה"]},
                            "description": "סטטוס החשבון",
                            "default": "פעיל"
                        }
                    }
                },
                "accounts": {
                    "description": "חשבונות בנק",
                    "primary_key": "מספר_חשבון",
                    "foreign_keys": {
                        "תעודת_זהות": {"references": "users.תעודת_זהות"}
                    },
                    "fields": {
                        "מספר_חשבון": {
                            "type": "string",
                            "constraints": {"max_length": 15},
                            "description": "מספר חשבון בנק",
                            "generator": "account_number"
                        },
                        "תעודת_זהות": {
                            "type": "string",
                            "constraints": {"max_length": 9},
                            "description": "תעודת זהות בעל החשבון"
                        },
                        "סוג_חשבון": {
                            "type": "choice",
                            "constraints": {"choices": ["חשבון פרטי", "חשבון עסקי", "חשבון חיסכון"]},
                            "description": "סוג החשבון"
                        },
                        "יתרה": {
                            "type": "float",
                            "constraints": {"min": 0, "max": 1000000},
                            "description": "יתרת החשבון בשקלים"
                        },
                        "מסגרת_אשראי": {
                            "type": "integer",
                            "constraints": {"min": 0, "max": 100000},
                            "description": "מסגרת אשראי בשקלים"
                        },
                        "אשראי_זמין": {
                            "type": "float",
                            "constraints": {"min": 0, "max": 100000},
                            "description": "אשראי זמין בשקלים"
                        },
                        "סניף_בנק": {
                            "type": "integer",
                            "constraints": {"min": 1, "max": 999},
                            "description": "מספר סניף הבנק"
                        },
                        "תאריך_פתיחה": {
                            "type": "date",
                            "description": "תאריך פתיחת החשבון",
                            "generator": "past_date"
                        },
                        "סטטוס": {
                            "type": "choice",
                            "constraints": {"choices": ["פעיל", "חסום", "סגור"]},
                            "description": "סטטוס החשבון",
                            "default": "פעיל"
                        }
                    }
                },
                "credit_cards": {
                    "description": "כרטיסי אשראי",
                    "primary_key": "מספר_כרטיס",
                    "foreign_keys": {
                        "תעודת_זהות": {"references": "users.תעודת_זהות"}
                    },
                    "fields": {
                        "מספר_כרטיס": {
                            "type": "string",
                            "constraints": {"max_length": 19},
                            "description": "מספר כרטיס האשראי",
                            "generator": "credit_card_number"
                        },
                        "תעודת_זהות": {
                            "type": "string",
                            "constraints": {"max_length": 9},
                            "description": "תעודת זהות בעל הכרטיס"
                        },
                        "סוג_כרטיס": {
                            "type": "choice",
                            "constraints": {
                                "choices": [
                                    "ויזה רגיל", "ויזה זהב", "ויזה פלטינום",
                                    "מאסטרקארד רגיל", "מאסטרקארד זהב", "מאסטרקארד פלטינום",
                                    "אמריקן אקספרס", "ישראכרט", "דביט רגיל",
                                    "מפתח דיסקונט רגיל", "FLY CARD מפתח דיסקונט"
                                ]
                            },
                            "description": "סוג כרטיס האשראי"
                        },
                        "תוקף": {
                            "type": "string",
                            "constraints": {"max_length": 5},
                            "description": "תאריך תפוגה (MM/YY)",
                            "generator": "credit_card_expiry"
                        },
                        "מסגרת_אשראי": {
                            "type": "integer",
                            "constraints": {"min": 1000, "max": 100000},
                            "description": "מסגרת אשראי בכרטיס"
                        },
                        "יתרה": {
                            "type": "float",
                            "constraints": {"min": 0, "max": 100000},
                            "description": "יתרת חיוב נוכחית"
                        },
                        "תשלומים_אחרונים": {
                            "type": "float",
                            "constraints": {"min": 0, "max": 10000},
                            "description": "סכום תשלומים אחרונים"
                        },
                        "תאריך_הנפקה": {
                            "type": "date",
                            "description": "תאריך הנפקת הכרטיס",
                            "generator": "past_date"
                        },
                        "דירוג_אשראי": {
                            "type": "integer",
                            "constraints": {"min": 300, "max": 850},
                            "description": "דירוג אשראי"
                        },
                        "סטטוס": {
                            "type": "choice",
                            "constraints": {"choices": ["פעיל", "חסום", "מושעה", "בוטל"]},
                            "description": "סטטוס הכרטיס",
                            "default": "פעיל"
                        }
                    }
                },
                "transactions": {
                    "description": "עסקאות כרטיסי אשראי",
                    "primary_key": "id",
                    "foreign_keys": {
                        "מספר_כרטיס": {"references": "credit_cards.מספר_כרטיס"}
                    },
                    "fields": {
                        "מספר_כרטיס": {
                            "type": "string",
                            "constraints": {"max_length": 19},
                            "description": "מספר כרטיס שבוצעה בו העסקה"
                        },
                        "תאריך_עסקה": {
                            "type": "date",
                            "description": "תאריך ביצוع העסקה",
                            "generator": "recent_date"
                        },
                        "סכום": {
                            "type": "float",
                            "constraints": {"min": 1, "max": 10000},
                            "description": "סכום העסקה בשקלים"
                        },
                        "קטגוריה": {
                            "type": "choice",
                            "constraints": {
                                "choices": [
                                    "מזון ומשקאות", "קניות ואופנה", "בידור ותרבות",
                                    "דלק ותחבורה", "חשמל ומים", "תקשורת",
                                    "בריאות ורפואה", "חינוך", "ביטוח", "אחר"
                                ]
                            },
                            "description": "קטגוריית העסקה"
                        },
                        "שם_עסק": {
                            "type": "string",
                            "constraints": {"max_length": 100},
                            "description": "שם בית העסק",
                            "generator": "hebrew_business_name"
                        },
                        "סוג_עסקה": {
                            "type": "choice",
                            "constraints": {"choices": ["רגילה", "תשלומים", "קרדיט", "החזר"]},
                            "description": "סוג העסקה",
                            "default": "רגילה"
                        },
                        "מספר_תשלומים": {
                            "type": "choice",
                            "constraints": {"choices": [1, 3, 6, 12, 24, 36]},
                            "description": "מספר תשלומים (אם רלוונטי)",
                            "default": 1
                        },
                        "סטטוס": {
                            "type": "choice",
                            "constraints": {"choices": ["נרשם", "ממתין", "מאושר", "נדחה", "בוטל"]},
                            "description": "סטטוס העסקה",
                            "default": "נרשם"
                        },
                        "תיאור": {
                            "type": "string",
                            "constraints": {"max_length": 200},
                            "description": "תיאור נוסף של העסקה"
                        }
                    }
                }
            },
            "generation_settings": {
                "default_locale": "he_IL",
                "default_records_per_table": 1000,
                "relationships": {
                    "users_to_accounts": "1:N",
                    "users_to_credit_cards": "1:N", 
                    "credit_cards_to_transactions": "1:N"
                }
            }
        }
    
    def _save_swagger_schema(self, schema: Dict[str, Any]) -> Path:
        """Save Swagger schema to file."""
        with open(self.swagger_file, 'w', encoding='utf-8') as f:
            json.dump(schema, f, ensure_ascii=False, indent=2)
        return self.swagger_file
    
    def _save_definition_schema(self, schema: Dict[str, Any]) -> Path:
        """Save definition schema to file."""
        with open(self.definition_file, 'w', encoding='utf-8') as f:
            json.dump(schema, f, ensure_ascii=False, indent=2)
        return self.definition_file
    
    def load_swagger_schema(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load Swagger/OpenAPI schema from file.
        
        Args:
            file_path: Path to Swagger file (JSON or YAML)
            
        Returns:
            Loaded schema dictionary
        """
        if file_path:
            schema_path = Path(file_path)
        else:
            schema_path = self.swagger_file
        
        if not schema_path.exists():
            raise FileNotFoundError(f"Swagger schema file not found: {schema_path}")
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            if schema_path.suffix.lower() in ['.yaml', '.yml']:
                import yaml
                schema = yaml.safe_load(f)
            else:
                schema = json.load(f)
        
        logger.info(f"Loaded Swagger schema from: {schema_path}")
        return schema
    
    def load_definition_schema(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load definition schema from file.
        
        Args:
            file_path: Path to definition file (JSON)
            
        Returns:
            Loaded schema dictionary
        """
        if file_path:
            schema_path = Path(file_path)
        else:
            schema_path = self.definition_file
            
        if not schema_path.exists():
            raise FileNotFoundError(f"Definition schema file not found: {schema_path}")
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        
        logger.info(f"Loaded definition schema from: {schema_path}")
        return schema
    
    def convert_swagger_to_definition(self, swagger_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Swagger/OpenAPI schema to definition schema format.
        
        Args:
            swagger_schema: Swagger schema dictionary
            
        Returns:
            Definition schema dictionary
        """
        logger.info("Converting Swagger schema to definition format")
        
        definition_schema = {
            "schema_info": {
                "name": swagger_schema.get("info", {}).get("title", "Converted Schema"),
                "version": swagger_schema.get("info", {}).get("version", "1.0.0"),
                "description": swagger_schema.get("info", {}).get("description", ""),
                "created": datetime.now().isoformat(),
                "locale": "he_IL"
            },
            "tables": {},
            "generation_settings": {
                "default_locale": "he_IL",
                "default_records_per_table": 1000,
                "relationships": {}
            }
        }
        
        # Extract schemas from components
        components = swagger_schema.get("components", {})
        schemas = components.get("schemas", {})
        
        # Convert each schema to a table
        for schema_name, schema_def in schemas.items():
            table_name = self._schema_name_to_table_name(schema_name)
            
            # Skip if not a table-like schema
            if schema_def.get("type") != "object":
                continue
            
            table_def = {
                "description": schema_def.get("description", f"Table for {schema_name}"),
                "fields": {}
            }
            
            # Convert properties to fields
            properties = schema_def.get("properties", {})
            required_fields = schema_def.get("required", [])
            
            for prop_name, prop_def in properties.items():
                field_def = self._convert_swagger_property_to_field(prop_name, prop_def)
                table_def["fields"][prop_name] = field_def
            
            # Set primary key (usually the first field or ID field)
            if "תעודת_זהות" in table_def["fields"]:
                table_def["primary_key"] = "תעודת_זהות"
            elif "מספר_כרטיס" in table_def["fields"]:
                table_def["primary_key"] = "מספר_כרטיס"
            elif "מספר_חשבון" in table_def["fields"]:
                table_def["primary_key"] = "מספר_חשבון"
            else:
                # Default to first field
                first_field = list(table_def["fields"].keys())[0] if table_def["fields"] else "id"
                table_def["primary_key"] = first_field
            
            definition_schema["tables"][table_name] = table_def
        
        return definition_schema
    
    def convert_definition_to_swagger(self, definition_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert definition schema to Swagger/OpenAPI format.
        
        Args:
            definition_schema: Definition schema dictionary
            
        Returns:
            Swagger schema dictionary
        """
        logger.info("Converting definition schema to Swagger format")
        
        schema_info = definition_schema.get("schema_info", {})
        
        swagger_schema = {
            "openapi": "3.0.0",
            "info": {
                "title": schema_info.get("name", "Generated API"),
                "version": schema_info.get("version", "1.0.0"),
                "description": schema_info.get("description", "Generated from definition schema")
            },
            "components": {
                "schemas": {}
            }
        }
        
        # Convert tables to schemas
        tables = definition_schema.get("tables", {})
        
        for table_name, table_def in tables.items():
            schema_name = self._table_name_to_schema_name(table_name)
            
            schema_def = {
                "type": "object",
                "description": table_def.get("description", f"Schema for {table_name}"),
                "properties": {},
                "required": []
            }
            
            # Convert fields to properties
            fields = table_def.get("fields", {})
            primary_key = table_def.get("primary_key")
            
            for field_name, field_def in fields.items():
                prop_def = self._convert_field_to_swagger_property(field_name, field_def)
                schema_def["properties"][field_name] = prop_def
                
                # Add to required if it's a primary key or has no default
                if field_name == primary_key or not field_def.get("default"):
                    schema_def["required"].append(field_name)
            
            swagger_schema["components"]["schemas"][schema_name] = schema_def
        
        return swagger_schema
    
    def _schema_name_to_table_name(self, schema_name: str) -> str:
        """Convert schema name to table name."""
        name_mapping = {
            'User': 'users',
            'Account': 'accounts', 
            'CreditCard': 'credit_cards',
            'Transaction': 'transactions'
        }
        return name_mapping.get(schema_name, schema_name.lower())
    
    def _table_name_to_schema_name(self, table_name: str) -> str:
        """Convert table name to schema name."""
        name_mapping = {
            'users': 'User',
            'accounts': 'Account',
            'credit_cards': 'CreditCard', 
            'transactions': 'Transaction'
        }
        return name_mapping.get(table_name, table_name.capitalize())
    
    def _convert_swagger_property_to_field(self, prop_name: str, prop_def: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Swagger property to definition field."""
        field_def = {
            "type": prop_def.get("type", "string"),
            "description": prop_def.get("description", "")
        }
        
        # Handle constraints
        constraints = {}
        
        if "maxLength" in prop_def:
            constraints["max_length"] = prop_def["maxLength"]
        if "minimum" in prop_def:
            constraints["min"] = prop_def["minimum"]
        if "maximum" in prop_def:
            constraints["max"] = prop_def["maximum"]
        if "enum" in prop_def:
            field_def["type"] = "choice"
            constraints["choices"] = prop_def["enum"]
        
        if constraints:
            field_def["constraints"] = constraints
        
        # Handle format conversions
        if prop_def.get("format") == "date":
            field_def["type"] = "date"
        elif prop_def.get("format") == "date-time":
            field_def["type"] = "datetime"
        elif prop_def.get("format") == "email":
            field_def["generator"] = "email"
        
        # Set generator based on field name and type
        if "תעודת_זהות" in prop_name:
            field_def["generator"] = "israeli_id"
        elif "טלפון" in prop_name:
            field_def["generator"] = "israeli_phone"
        elif "שם_פרטי" in prop_name:
            field_def["generator"] = "hebrew_first_name"
        elif "שם_משפחה" in prop_name:
            field_def["generator"] = "hebrew_last_name"
        elif "כתובת" in prop_name:
            field_def["generator"] = "hebrew_address"
        elif "מספר_כרטיס" in prop_name:
            field_def["generator"] = "credit_card_number"
        
        return field_def
    
    def _convert_field_to_swagger_property(self, field_name: str, field_def: Dict[str, Any]) -> Dict[str, Any]:
        """Convert definition field to Swagger property."""
        prop_def = {
            "type": field_def.get("type", "string"),
            "description": field_def.get("description", "")
        }
        
        # Handle constraints
        constraints = field_def.get("constraints", {})
        
        if "max_length" in constraints:
            prop_def["maxLength"] = constraints["max_length"]
        if "min" in constraints:
            prop_def["minimum"] = constraints["min"]
        if "max" in constraints:
            prop_def["maximum"] = constraints["max"]
        if "choices" in constraints:
            prop_def["enum"] = constraints["choices"]
        
        # Handle type conversions
        if field_def.get("type") == "date":
            prop_def["format"] = "date"
        elif field_def.get("type") == "datetime":
            prop_def["format"] = "date-time"
        elif field_def.get("type") == "choice":
            prop_def["type"] = "string"
        
        # Add examples based on field name
        if "תעודת_זהות" in field_name:
            prop_def["example"] = "123456782"
        elif "טלפון" in field_name:
            prop_def["example"] = "050-1234567"
        elif "שם_פרטי" in field_name:
            prop_def["example"] = "דוד"
        elif "מספר_כרטיס" in field_name:
            prop_def["example"] = "4532123456789012"
        
        return prop_def
    
    def generate_database_from_swagger(self, swagger_file: str, num_records: int = 1000, db_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate database from Swagger schema file.
        
        Args:
            swagger_file: Path to Swagger schema file
            num_records: Number of records to generate
            db_url: Database URL (optional)
            
        Returns:
            Generation results
        """
        logger.info(f"Generating database from Swagger file: {swagger_file}")
        
        # Load Swagger schema
        swagger_schema = self.load_swagger_schema(swagger_file)
        
        # Create enhanced generator with Swagger schema
        generator = EnhancedSwaggerSchemaGenerator(
            schema_file_path=swagger_file,
            db_url=db_url
        )
        
        # Generate database
        result = generator.generate_database(num_records=num_records, strategy='faker')
        
        logger.info(f"Database generated from Swagger schema: {result.get('database_url')}")
        return result
    
    def generate_database_from_definition(self, definition_file: str, num_records: int = 1000, db_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate database from definition schema file.
        
        Args:
            definition_file: Path to definition schema file
            num_records: Number of records to generate
            db_url: Database URL (optional)
            
        Returns:
            Generation results
        """
        logger.info(f"Generating database from definition file: {definition_file}")
        
        try:
            # Load and validate definition schema
            with open(definition_file, 'r', encoding='utf-8') as f:
                definition_schema = json.load(f)
            
            logger.info(f"Loaded definition schema from: {definition_file}")
            
            # Convert to database schema
            db_schema = self._convert_definition_to_db_schema(definition_schema)
            
            # Generate database
            generator = create_generator('faker', db_url=db_url)
            result = generator.generate_and_store(db_schema, num_records)
            
            # Export to SQL if requested
            if db_url:
                sql_dir = Path(self.schemas_dir) / "sql"
                sql_dir.mkdir(parents=True, exist_ok=True)
                generator.export_data(['sql'], str(sql_dir))
            
            logger.info(f"Database generated from definition schema: {db_url}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate database from definition: {e}", exc_info=True)
            raise
    
    def _convert_definition_to_db_schema(self, definition_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Convert definition schema to database generator schema format."""
        db_schema = {}
        
        tables = definition_schema.get("tables", {})
        
        for table_name, table_def in tables.items():
            db_schema[table_name] = {
                "fields": {},
                "metadata": {
                    "description": table_def.get("description", ""),
                    "primary_key": table_def.get("primary_key"),
                    "foreign_keys": table_def.get("foreign_keys", {})
                }
            }
            
            # Convert fields
            for field_name, field_def in table_def.get("fields", {}).items():
                # Check if this is a Hebrew field name that needs to be converted
                english_name = self._hebrew_to_english_field_name(field_name)
                if english_name != field_name:
                    field_def['hebrew_name'] = field_name
                    field_name = english_name
                
                db_schema[table_name]["fields"][field_name] = field_def
        
        return db_schema
    
    def _hebrew_to_english_field_name(self, field_name: str) -> str:
        """Convert Hebrew field names to English equivalents."""
        hebrew_to_english = {
            'תעודת_זהות': 'id_number',
            'שם_פרטי': 'first_name',
            'שם_משפחה': 'last_name',
            'כתובת': 'address',
            'עיר': 'city',
            'טלפון': 'phone',
            'דואר_אלקטרוני': 'email',
            'תאריך_יצירה': 'creation_date',
            'סטטוס': 'status',
            'מספר_חשבון': 'account_number',
            'סוג_חשבון': 'account_type',
            'יתרה': 'balance',
            'מסגרת_אשראי': 'credit_limit',
            'אשראי_זמין': 'available_credit',
            'סניף_בנק': 'bank_branch',
            'תאריך_פתיחה': 'opening_date',
            'מספר_כרטיס': 'card_number',
            'סוג_כרטיס': 'card_type',
            'תוקף': 'expiry_date',
            'תשלומים_אחרונים': 'last_payments',
            'תאריך_הנפקה': 'issue_date',
            'דירוג_אשראי': 'credit_score',
            'תאריך_עסקה': 'transaction_date',
            'סכום': 'amount',
            'קטגוריה': 'category',
            'שם_עסק': 'business_name',
            'סוג_עסקה': 'transaction_type',
            'מספר_תשלומים': 'installments',
            'תיאור': 'description'
        }
        return hebrew_to_english.get(field_name, field_name)
    
    def list_available_schemas(self) -> Dict[str, Any]:
        """List all available schema files in the schemas directory."""
        schema_files = {
            "swagger_files": [],
            "definition_files": [],
            "other_files": []
        }
        
        for file_path in self.schemas_dir.glob("*"):
            if file_path.is_file():
                if file_path.suffix.lower() in ['.json', '.yaml', '.yml']:
                    try:
                        # Try to determine if it's a Swagger or definition file
                        with open(file_path, 'r', encoding='utf-8') as f:
                            if file_path.suffix.lower() in ['.yaml', '.yml']:
                                content = yaml.safe_load(f)
                            else:
                                content = json.load(f)
                        
                        if "openapi" in content or "swagger" in content:
                            schema_files["swagger_files"].append({
                                "name": file_path.name,
                                "path": str(file_path),
                                "type": "swagger"
                            })
                        elif "tables" in content and "schema_info" in content:
                            schema_files["definition_files"].append({
                                "name": file_path.name,
                                "path": str(file_path),
                                "type": "definition"
                            })
                        else:
                            schema_files["other_files"].append({
                                "name": file_path.name,
                                "path": str(file_path),
                                "type": "unknown"
                            })
                    except Exception as e:
                        logger.warning(f"Could not parse schema file {file_path}: {e}")
                        schema_files["other_files"].append({
                            "name": file_path.name,
                            "path": str(file_path),
                            "type": "error"
                        })
        
        return schema_files


def main():
    """Demonstrate the Schema Manager functionality."""
    print("=" * 80)
    print("SCHEMA MANAGER - SWAGGER AND DEFINITION FILE SUPPORT")
    print("=" * 80)
    
    # Initialize Schema Manager
    print("\n1. Initializing Schema Manager...")
    manager = SchemaManager()
    
    # Create default schema files
    print("\n2. Creating default schema files...")
    created_files = manager.create_default_files()
    print(f"✅ Created Swagger file: {created_files['swagger_file']}")
    print(f"✅ Created Definition file: {created_files['definition_file']}")
    
    # List available schemas
    print("\n3. Available schema files:")
    available_schemas = manager.list_available_schemas()
    
    for swagger_file in available_schemas["swagger_files"]:
        print(f"   📄 Swagger: {swagger_file['name']}")
        
    for definition_file in available_schemas["definition_files"]:
        print(f"   📋 Definition: {definition_file['name']}")
    
    # Generate database from Swagger file
    print("\n4. Generating database from Swagger file...")
    swagger_result = manager.generate_database_from_swagger(
        swagger_file=created_files['swagger_file'],
        num_records=100,
        db_url="sqlite:///israeli_banking_from_swagger.db"
    )
    print(f"✅ Swagger DB: {swagger_result.get('database_url')}")
    print(f"   Tables: {swagger_result.get('tables_created')}")
    
    # Generate database from Definition file
    print("\n5. Generating database from Definition file...")
    definition_result = manager.generate_database_from_definition(
        definition_file=created_files['definition_file'],
        num_records=100,
        db_url="sqlite:///israeli_banking_from_definition.db"
    )
    print(f"✅ Definition DB: {definition_result.get('database_url')}")
    print(f"   Tables: {definition_result.get('tables_created')}")
    
    # Convert between formats
    print("\n6. Converting between formats...")
    
    # Load Swagger and convert to Definition
    swagger_schema = manager.load_swagger_schema()
    converted_definition = manager.convert_swagger_to_definition(swagger_schema)
    
    # Save converted definition
    converted_def_file = manager.schemas_dir / "converted_from_swagger.json"
    with open(converted_def_file, 'w', encoding='utf-8') as f:
        json.dump(converted_definition, f, ensure_ascii=False, indent=2)
    print(f"✅ Converted Swagger → Definition: {converted_def_file}")
    
    # Load Definition and convert to Swagger
    definition_schema = manager.load_definition_schema()
    converted_swagger = manager.convert_definition_to_swagger(definition_schema)
    
    # Save converted swagger
    converted_swagger_file = manager.schemas_dir / "converted_from_definition.json"
    with open(converted_swagger_file, 'w', encoding='utf-8') as f:
        json.dump(converted_swagger, f, ensure_ascii=False, indent=2)
    print(f"✅ Converted Definition → Swagger: {converted_swagger_file}")
    
    print("\n" + "=" * 80)
    print("SCHEMA MANAGER DEMONSTRATION COMPLETE!")
    print("=" * 80)
    
    print(f"\n📁 Generated Files in {manager.schemas_dir}:")
    for file_path in manager.schemas_dir.glob("*"):
        if file_path.is_file():
            file_size = file_path.stat().st_size / 1024  # KB
            print(f"   • {file_path.name} ({file_size:.1f} KB)")
    
    print("\n🚀 Usage Examples:")
    print("   # Generate from Swagger file")
    print("   python schema_manager.py --swagger schemas/israeli_banking_swagger.json")
    print("   # Generate from Definition file")
    print("   python schema_manager.py --definition schemas/israeli_banking_definition.json")
    print("   # Convert Swagger to Definition")
    print("   python schema_manager.py --convert swagger-to-definition")
    
    return manager


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Schema Manager - Handle Swagger and Definition files')
    parser.add_argument('--swagger', type=str, help='Generate database from Swagger file')
    parser.add_argument('--definition', type=str, help='Generate database from Definition file')
    parser.add_argument('--convert', type=str, choices=['swagger-to-definition', 'definition-to-swagger'], help='Convert between formats')
    parser.add_argument('--records', type=int, default=1000, help='Number of records to generate')
    parser.add_argument('--db-url', type=str, help='Database URL')
    parser.add_argument('--create-defaults', action='store_true', help='Create default schema files')
    
    args = parser.parse_args()
    
    manager = SchemaManager()
    
    if args.create_defaults:
        created_files = manager.create_default_files()
        print(f"Created default files: {created_files}")
    
    elif args.swagger:
        result = manager.generate_database_from_swagger(
            swagger_file=args.swagger,
            num_records=args.records,
            db_url=args.db_url
        )
        print(f"Generated database from Swagger: {result}")
    
    elif args.definition:
        result = manager.generate_database_from_definition(
            definition_file=args.definition,
            num_records=args.records,
            db_url=args.db_url
        )
        print(f"Generated database from Definition: {result}")
    
    elif args.convert:
        if args.convert == 'swagger-to-definition':
            swagger_schema = manager.load_swagger_schema()
            definition_schema = manager.convert_swagger_to_definition(swagger_schema)
            output_file = manager.schemas_dir / "converted_swagger_to_definition.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(definition_schema, f, ensure_ascii=False, indent=2)
            print(f"Converted Swagger to Definition: {output_file}")
        
        elif args.convert == 'definition-to-swagger':
            definition_schema = manager.load_definition_schema()
            swagger_schema = manager.convert_definition_to_swagger(definition_schema)
            output_file = manager.schemas_dir / "converted_definition_to_swagger.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(swagger_schema, f, ensure_ascii=False, indent=2)
            print(f"Converted Definition to Swagger: {output_file}")
    
    else:
        # Run the main demonstration
        main()