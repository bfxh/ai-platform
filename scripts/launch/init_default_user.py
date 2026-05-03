import os
import sys
import urllib.request
import json

db_url = os.environ.get('DATABASE_URL', 'postgres://multica:multica@localhost:5432/multica?sslmode=disable')

try:
    import psycopg2
except ImportError:
    print("Installing psycopg2...")
    os.system(f'{sys.executable} -m pip install psycopg2-binary -q')
    import psycopg2

conn = psycopg2.connect(db_url.replace('sslmode=disable', ''))
conn.autocommit = True
cur = conn.cursor()

default_email = 'default@multica.local'
default_name = 'Default User'

cur.execute("SELECT id FROM users WHERE email = %s", (default_email,))
user = cur.fetchone()

if user:
    user_id = str(user[0])
    print(f"Default user exists: {user_id}")
else:
    cur.execute(
        "INSERT INTO users (email, name) VALUES (%s, %s) RETURNING id",
        (default_email, default_name)
    )
    user_id = str(cur.fetchone()[0])
    print(f"Created default user: {user_id}")

cur.execute("SELECT id FROM workspaces WHERE slug = 'default'")
workspace = cur.fetchone()

if workspace:
    workspace_id = str(workspace[0])
    print(f"Default workspace exists: {workspace_id}")
else:
    cur.execute(
        "INSERT INTO workspaces (name, slug, issue_prefix) VALUES ('My Workspace', 'default', 'MUL') RETURNING id"
    )
    workspace_id = str(cur.fetchone()[0])
    print(f"Created default workspace: {workspace_id}")

cur.execute(
    "SELECT id FROM members WHERE user_id = %s AND workspace_id = %s",
    (user_id, workspace_id)
)
member = cur.fetchone()

if not member:
    cur.execute(
        "INSERT INTO members (user_id, workspace_id, role) VALUES (%s, %s, 'owner')",
        (user_id, workspace_id)
    )
    print(f"Added default user as owner of default workspace")

cur.close()
conn.close()

print(f"\nDEFAULT_USER_ID={user_id}")
print(f"DEFAULT_WORKSPACE_ID={workspace_id}")
