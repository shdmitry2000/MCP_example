class HebrewEnglishFieldMapper:
    """Maps between Hebrew and English field names with metadata preservation."""
    
    def __init__(self):
        self.hebrew_to_english = {
            # Personal Information
            'תעודת_זהות': 'israeli_id',
            'שם_פרטי': 'first_name', 
            'שם_משפחה': 'last_name',
            'כתובת': 'address',
            'עיר': 'city',
            'טלפון': 'phone',
            'דואר_אלקטרוני': 'email',
            'תאריך_יצירה': 'created_at',
            'תאריך_לידה': 'birth_date',
            
            # Banking Fields
            'מספר_חשבון': 'account_number',
            'מספר_כרטיס': 'card_number',
            'סוג_חשבון': 'account_type',
            'סוג_כרטיס': 'card_type',
            'יתרה': 'balance',
            'מסגרת_אשראי': 'credit_limit',
            'אשראי_זמין': 'available_credit',
            'תשלומים_אחרונים': 'last_payments',
            'דירוג_אשראי': 'credit_score',
            'תוקף': 'expiry_date',
            'תאריך_פתיחה': 'opening_date',
            'תאריך_הנפקה': 'issue_date',
            'סניף_בנק': 'bank_branch',
            
            # Transaction Fields
            'תאריך_עסקה': 'transaction_date',
            'סכום': 'amount',
            'קטגוריה': 'category',
            'שם_עסק': 'merchant_name',
            'סוג_עסקה': 'transaction_type',
            'מספר_תשלומים': 'installments',
            'תיאור': 'description',
            
            # Status Fields
            'סטטוס': 'status'
        }
        
        self.english_to_hebrew = {v: k for k, v in self.hebrew_to_english.items()}
        
        # Friendly display names for UI
        self.display_names = {
            'israeli_id': 'Israeli ID',
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'address': 'Address',
            'city': 'City',
            'phone': 'Phone',
            'email': 'Email',
            'account_number': 'Account Number',
            'card_number': 'Card Number',
            'balance': 'Balance',
            'credit_limit': 'Credit Limit',
            'transaction_date': 'Transaction Date',
            'amount': 'Amount',
            'merchant_name': 'Merchant',
            'status': 'Status'
        }
    
    def get_english_name(self, hebrew_name: str) -> str:
        """Get English field name from Hebrew."""
        return self.hebrew_to_english.get(hebrew_name, hebrew_name)
    
    def get_hebrew_name(self, english_name: str) -> str:
        """Get Hebrew field name from English."""
        return self.english_to_hebrew.get(english_name, english_name)
    
    def get_display_name(self, field_name: str) -> str:
        """Get user-friendly display name."""
        # Try English first, then Hebrew
        if field_name in self.display_names:
            return self.display_names[field_name]
        
        english_name = self.get_english_name(field_name)
        return self.display_names.get(english_name, field_name.replace('_', ' ').title()) 