import os

auth_file = r"\server\internal\middleware\auth.go"
with open(auth_file, 'r', encoding='utf-8') as f:
    content = f.read()

old = '''func Auth(queries *db.Queries) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			tokenString, fromCookie := extractToken(r)
			if tokenString == "" {
				slog.Debug("auth: no token found", "path", r.URL.Path)
				http.Error(w, `{"error":"missing authorization"}`, http.StatusUnauthorized)
				return
			}'''

new = '''func Auth(queries *db.Queries) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			tokenString, fromCookie := extractToken(r)
			if tokenString == "" {
				defaultUserID := os.Getenv("DEFAULT_USER_ID")
				if defaultUserID != "" {
					r.Header.Set("X-User-ID", defaultUserID)
					r.Header.Set("X-User-Email", "default@multica.local")
					next.ServeHTTP(w, r)
					return
				}
				slog.Debug("auth: no token found", "path", r.URL.Path)
				http.Error(w, `{"error":"missing authorization"}`, http.StatusUnauthorized)
				return
			}'''

content = content.replace(old, new)

if 'os.Getenv("DEFAULT_USER_ID")' not in content:
    print("ERROR: Failed to patch auth.go")
    exit(1)

if '"os"' not in content:
    content = content.replace('"strings"', '"os"\n\t"strings"', 1)

with open(auth_file, 'w', encoding='utf-8') as f:
    f.write(content)

print("auth.go patched successfully")

handler_file = r"\server\internal\handler\handler.go"
with open(handler_file, 'r', encoding='utf-8') as f:
    content = f.read()

old2 = '''func requireUserID(w http.ResponseWriter, r *http.Request) (string, bool) {
	userID := requestUserID(r)
	if userID == "" {
		writeError(w, http.StatusUnauthorized, "user not authenticated")
		return "", false
	}
	return userID, true
}'''

new2 = '''func requireUserID(w http.ResponseWriter, r *http.Request) (string, bool) {
	userID := requestUserID(r)
	if userID == "" {
		defaultUserID := os.Getenv("DEFAULT_USER_ID")
		if defaultUserID != "" {
			return defaultUserID, true
		}
		writeError(w, http.StatusUnauthorized, "user not authenticated")
		return "", false
	}
	return userID, true
}'''

content = content.replace(old2, new2)

if 'os.Getenv("DEFAULT_USER_ID")' not in content:
    print("ERROR: Failed to patch handler.go")
    exit(1)

if '"os"' not in content:
    content = content.replace('"encoding/json"', '"encoding/json"\n\t"os"', 1)

with open(handler_file, 'w', encoding='utf-8') as f:
    f.write(content)

print("handler.go patched successfully")
