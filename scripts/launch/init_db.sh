#!/bin/bash
docker exec multica-postgres psql -U multica -d multica -c "INSERT INTO \"user\" (email, name) VALUES ('default@multica.local', 'User') ON CONFLICT (email) DO NOTHING;"

USER_ID=$(docker exec multica-postgres psql -U multica -d multica -t -A -c "SELECT id FROM \"user\" WHERE email = 'default@multica.local';")
echo "DEFAULT_USER_ID=$USER_ID"

docker exec multica-postgres psql -U multica -d multica -c "INSERT INTO workspace (name, slug, issue_prefix) VALUES ('My Workspace', 'default', 'MUL') ON CONFLICT (slug) DO NOTHING;"

WS_ID=$(docker exec multica-postgres psql -U multica -d multica -t -A -c "SELECT id FROM workspace WHERE slug = 'default';")
echo "DEFAULT_WORKSPACE_ID=$WS_ID"

if [ -n "$USER_ID" ] && [ -n "$WS_ID" ]; then
    docker exec multica-postgres psql -U multica -d multica -c "INSERT INTO member (user_id, workspace_id, role) VALUES ('$USER_ID', '$WS_ID', 'owner') ON CONFLICT DO NOTHING;"
    echo "Member created"
fi

echo "DONE"
