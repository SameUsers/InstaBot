import bcrypt

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password_income: str, user_hash_pass: str) -> bool:
    return bcrypt.checkpw(
        password_income.encode('utf-8'),
        user_hash_pass.encode('utf-8')
    )