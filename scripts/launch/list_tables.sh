#!/bin/bash
docker exec multica-postgres psql -U multica -d multica -c "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;" 
