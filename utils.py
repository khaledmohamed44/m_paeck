def validate_settings(form_data):
    """التحقق من صحة بيانات الإعدادات"""
    errors = []
    
    # التحقق من الأرقام
    phone_fields = ['phone1', 'phone2', 'whatsapp']
    for field in phone_fields:
        if field in form_data:
            if not form_data[field].startswith('+965'):
                errors.append(f'يجب أن يبدأ {field} بـ +965')
    
    # التحقق من وجود البريد الإلكتروني
    if 'email' in form_data and not form_data['email']:
        errors.append('البريد الإلكتروني مطلوب')
    
    return errors
