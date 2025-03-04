import os

def clean_database():
    db_path = 'plastic_world.db'
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print("✅ تم حذف قاعدة البيانات بنجاح")
        except Exception as e:
            print(f"❌ حدث خطأ أثناء حذف قاعدة البيانات: {str(e)}")
    else:
        print("ℹ️ قاعدة البيانات غير موجودة")

if __name__ == '__main__':
    clean_database()
