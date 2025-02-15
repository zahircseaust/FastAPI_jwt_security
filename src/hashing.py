import hashlib
import bcrypt

def hash_sha256(password: str) -> str:
    """Hashes a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def hash_bcrypt(password: str) -> str:
    """Hashes a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()

def verify_bcrypt(password: str, hashed_password: str) -> bool:
    """Verifies a password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode(), hashed_password.encode())

# Example Usage
if __name__ == "__main__":
    password = "securepassword"
    
    sha256_hash = hash_sha256(password)
    print("SHA-256 Hash:", sha256_hash)

    bcrypt_hash = hash_bcrypt(password)
    print("Bcrypt Hash:", bcrypt_hash)

    is_valid = verify_bcrypt(password, bcrypt_hash)
    print("Password Valid:", is_valid)
