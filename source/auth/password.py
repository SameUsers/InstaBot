import asyncio
import bcrypt
from loguru import logger

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password_income: str, user_hash_pass: str) -> bool:
    return bcrypt.checkpw(
        password_income.encode('utf-8'),
        user_hash_pass.encode('utf-8')
    )

async def async_hash_password(password: str) -> str:
    """Асинхронная обёртка для hash_password, выполняет операцию в thread pool."""
    logger.debug("Hashing password")
    try:
        result = await asyncio.to_thread(hash_password, password)
        logger.debug("Password hashed successfully")
        return result
    except Exception as exc:
        logger.exception("Failed to hash password: {error}", error=str(exc))
        raise

async def async_verify_password(password_income: str, user_hash_pass: str) -> bool:
    """Асинхронная обёртка для verify_password, выполняет операцию в thread pool."""
    logger.debug("Verifying password")
    try:
        result = await asyncio.to_thread(verify_password, password_income, user_hash_pass)
        logger.debug("Password verification result: {result}", result=result)
        return result
    except Exception as exc:
        logger.exception("Failed to verify password: {error}", error=str(exc))
        raise