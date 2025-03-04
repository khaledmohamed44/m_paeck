import os
from app import app, db, User, Settings

def reset_database():
    # حذف قاعدة البيانات القديمة
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plastic_world.db')
    if os.path.exists(db_path):
        os.remove(db_path)
        print("تم حذف قاعدة البيانات القديمة")

    # إنشاء قاعدة البيانات الجديدة
    with app.app_context():
        db.create_all()
        
        # إنشاء الإعدادات الافتراضية
        default_settings = Settings(
            background_image='/static/images/default-background.jpg',
            primary_color='#139694',
            header_text='شركة عالم البلاستك',
            header_description='نقدم أفضل المنتجات البلاستيكية والورقية بجودة عالية'
        )
        db.session.add(default_settings)
        
        # إنشاء حساب المسؤول
        admin = User(
            username='admin',
            password='admin123',
            is_admin=True
        )
        db.session.add(admin)
        
        db.session.commit()
        print("تم إنشاء قاعدة البيانات الجديدة مع الإعدادات الافتراضية وحساب المسؤول")

if __name__ == '__main__':
    reset_database()
