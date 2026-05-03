@echo off
set DATABASE_URL=postgres://multica:multica@localhost:5432/multica?sslmode=disable
set DEFAULT_USER_ID=0b65b159-5606-4060-9270-627d8bfa7832
set MULTICA_DEV_VERIFICATION_CODE=888888
set JWT_SECRET=dev-secret-key-12345
set ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3002,http://localhost:5173,http://localhost:5174
set FRONTEND_ORIGIN=http://localhost:3000
set MULTICA_APP_URL=http://localhost:3000
set ALLOW_SIGNUP=true
cd /d "\server"
go run -buildvcs=false ./cmd/server/
