import bcrypt

def hash_password(pwd):
    return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()

print(hash_password("admin123"))
print(hash_password("hr@123"))