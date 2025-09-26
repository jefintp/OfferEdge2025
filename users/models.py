from mongoengine import Document, StringField, BooleanField
import bcrypt

class User(Document):
    userid = StringField(required=True, unique=True)
    passwordHash = StringField(required=True)

    # 🔐 Role flags
   
    is_admin = BooleanField(default=False)
    is_banned = BooleanField(default=False)

    def set_password(self, raw_password):
        self.passwordHash = bcrypt.hashpw(raw_password.encode(), bcrypt.gensalt()).decode()

    def check_password(self, raw_password):
        return bcrypt.checkpw(raw_password.encode(), self.passwordHash.encode())