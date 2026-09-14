import sys

with open('app/seed/seed_data.py', 'r') as f:
    content = f.read()

# Replace emails
content = content.replace('alice.chen@zerogate.internal', 'alice@zerogate.local')
content = content.replace('bob.martinez@zerogate.internal', 'bob@zerogate.local')
content = content.replace('carol.vance@zerogate.internal', 'carol@zerogate.local')
content = content.replace('david.kim@zerogate.internal', 'admin@zerogate.local')
content = content.replace('vendor01@contractor.zerogate.internal', 'vendor01@zerogate.local')

# Rename david to admin
content = content.replace('\'username\': \'david\'', '\'username\': \'admin\'')
content = content.replace('\"username\": \"david\"', '\"username\": \"admin\"')
content = content.replace('existing_users[\"david\"]', 'existing_users[\"admin\"]')
content = content.replace('users.get(\"david\")', 'users.get(\"admin\")')
content = content.replace('\"display_name\": \"David Kim\"', '\"display_name\": \"David Kim (Admin)\"')
content = content.replace('\"David Admin Terminal\"', '\"Admin Terminal\"')

# Add passwords
imports_and_hashes = '''from app.core.security import get_password_hash
from app.core.config import settings

def seed_database(db: Session):
    """Seed the database with deterministic demo users, devices, resources, and access contexts."""
    
    # 1. Seed Users if not already present
    existing_users = {u.username: u for u in db.query(User).all()}
    
    user_password_hash = get_password_hash(settings.DEMO_USER_PASSWORD)
    admin_password_hash = get_password_hash(settings.ADMIN_PASSWORD)

    user_definitions = ['''

content = content.replace('''def seed_database(db: Session):
    """Seed the database with deterministic demo users, devices, resources, and access contexts."""
    
    # 1. Seed Users if not already present
    existing_users = {u.username: u for u in db.query(User).all()}
    
    user_definitions = [''', imports_and_hashes)

content = content.replace('"email": "alice@zerogate.local",', '"email": "alice@zerogate.local",\n            "hashed_password": user_password_hash,')
content = content.replace('"email": "bob@zerogate.local",', '"email": "bob@zerogate.local",\n            "hashed_password": user_password_hash,')
content = content.replace('"email": "carol@zerogate.local",', '"email": "carol@zerogate.local",\n            "hashed_password": user_password_hash,')
content = content.replace('"email": "admin@zerogate.local",', '"email": "admin@zerogate.local",\n            "hashed_password": admin_password_hash,')
content = content.replace('"email": "vendor01@zerogate.local",', '"email": "vendor01@zerogate.local",\n            "hashed_password": user_password_hash,')

with open('app/seed/seed_data.py', 'w') as f:
    f.write(content)
