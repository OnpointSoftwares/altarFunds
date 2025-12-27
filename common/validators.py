import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from phonenumbers import parse, is_valid_number, format_number, PhoneNumberFormat
from datetime import datetime


def validate_phone_number(phone_number):
    """Validate Kenyan phone number"""
    try:
        # Parse phone number with Kenya country code
        parsed = parse(phone_number, "KE")
        
        if not is_valid_number(parsed):
            raise ValidationError(_("Invalid phone number format"))
        
        # Format to E.164 format
        formatted = format_number(parsed, PhoneNumberFormat.E164)
        
        # Check if it's a Kenyan number (starts with +254)
        if not formatted.startswith('+254'):
            raise ValidationError(_("Only Kenyan phone numbers are allowed"))
        
        return formatted
        
    except Exception as e:
        raise ValidationError(_("Invalid phone number format"))


def validate_id_number(id_number):
    """Validate Kenyan ID number"""
    if not id_number:
        return
    
    # Remove any spaces or dashes
    id_number = re.sub(r'[\s-]', '', id_number)
    
    # Kenyan ID numbers are typically 7-8 digits
    if not re.match(r'^\d{7,8}$', id_number):
        raise ValidationError(_("Invalid Kenyan ID number format"))
    
    return id_number


def validate_kra_pin(kra_pin):
    """Validate KRA PIN format"""
    if not kra_pin:
        return
    
    # Remove spaces
    kra_pin = kra_pin.replace(' ', '')
    
    # KRA PIN format: A/P + 9 digits + letter (e.g., A123456789P)
    if not re.match(r'^[AP]\d{9}[A-Z]$', kra_pin):
        raise ValidationError(_("Invalid KRA PIN format"))
    
    return kra_pin


def validate_amount(amount):
    """Validate transaction amount"""
    if amount <= 0:
        raise ValidationError(_("Amount must be greater than 0"))
    
    if amount > 10000000:  # 10 million KES limit
        raise ValidationError(_("Amount exceeds maximum allowed limit"))
    
    return amount


def validate_church_name(name):
    """Validate church name"""
    if not name or len(name.strip()) < 3:
        raise ValidationError(_("Church name must be at least 3 characters long"))
    
    # Check for valid characters (letters, numbers, spaces, hyphens, apostrophes)
    if not re.match(r'^[a-zA-Z0-9\s\-\'\.]+$', name):
        raise ValidationError(_("Church name contains invalid characters"))
    
    return name.strip()


def validate_bank_account_number(account_number):
    """Validate bank account number"""
    if not account_number:
        return
    
    # Remove spaces and dashes
    account_number = re.sub(r'[\s-]', '', account_number)
    
    # Kenyan bank account numbers are typically 6-13 digits
    if not re.match(r'^\d{6,13}$', account_number):
        raise ValidationError(_("Invalid bank account number format"))
    
    return account_number


def validate_paybill_number(paybill_number):
    """Validate M-Pesa Paybill number"""
    if not paybill_number:
        return
    
    # Paybill numbers are 5-7 digits
    if not re.match(r'^\d{5,7}$', paybill_number):
        raise ValidationError(_("Invalid Paybill number format"))
    
    return paybill_number


def validate_till_number(till_number):
    """Validate M-Pesa Till number"""
    if not till_number:
        return
    
    # Till numbers start with 7 and are 6-7 digits
    if not re.match(r'^7\d{5,6}$', till_number):
        raise ValidationError(_("Invalid Till number format"))
    
    return till_number


def validate_email_domain(email):
    """Validate email domain for business emails"""
    if not email:
        return None
    
    # List of common personal email domains to restrict for church accounts
    restricted_domains = [
        'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
        'aol.com', 'icloud.com', 'mail.com'
    ]
    
    domain = email.split('@')[-1].lower()
    
    # For church registrations, prefer business domains
    # This is optional and can be adjusted based on requirements
    return domain


def validate_financial_year(year):
    """Validate financial year format (YYYY)"""
    current_year = datetime.now().year
    
    try:
        year_int = int(year)
        
        if year_int < 2020 or year_int > current_year + 1:
            raise ValidationError(_("Invalid financial year"))
        
        return year_int
        
    except (ValueError, TypeError):
        raise ValidationError(_("Financial year must be a valid year"))


def validate_percentage(value):
    """Validate percentage values (0-100)"""
    if not 0 <= value <= 100:
        raise ValidationError(_("Percentage must be between 0 and 100"))
    
    return value


class PasswordValidator:
    """Custom password validator for church financial systems"""
    
    @staticmethod
    def validate_password_strength(password):
        """Validate password strength for financial systems"""
        errors = []
        
        if len(password) < 12:
            errors.append(_("Password must be at least 12 characters long"))
        
        if not re.search(r'[A-Z]', password):
            errors.append(_("Password must contain at least one uppercase letter"))
        
        if not re.search(r'[a-z]', password):
            errors.append(_("Password must contain at least one lowercase letter"))
        
        if not re.search(r'\d', password):
            errors.append(_("Password must contain at least one digit"))
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append(_("Password must contain at least one special character"))
        
        # Check for common patterns
        common_patterns = [
            r'123456', r'password', r'qwerty', r'abc123',
            r'church', r'pastor', r'treasure', r'altar'
        ]
        
        for pattern in common_patterns:
            if re.search(pattern, password.lower()):
                errors.append(_("Password contains common patterns that are not allowed"))
        
        if errors:
            raise ValidationError(errors)
        
        return password
