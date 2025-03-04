from app import app, db, User

def create_admin():
    # التحقق من وجود المستخدم
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            password='admin123',
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print('تم إنشاء حساب المسؤول بنجاح')
    else:
        print('حساب المسؤول موجود بالفعل')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_admin()
