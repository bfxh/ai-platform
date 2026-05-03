import re

hub_path = r"\server\internal\realtime\hub.go"
with open(hub_path, "r", encoding="utf-8") as f:
    content = f.read()

if "user_id_direct" in content:
    print("hub.go already patched, skipping")
else:
    old_first_msg = """// firstMessageAuth reads the first WebSocket message expecting an auth payload.
func firstMessageAuth(conn *websocket.Conn) (string, string) {
\tconn.SetReadDeadline(time.Now().Add(10 * time.Second))
\tdefer conn.SetReadDeadline(time.Time{})

\t_, raw, err := conn.ReadMessage()
\tif err != nil {
\t\treturn "", `{"error":"auth timeout or read error"}`
\t}

\tvar msg struct {
\t\tType    string `json:"type"`
\t\tPayload struct {
\t\t\tToken string `json:"token"`
\t\t} `json:"payload"`
\t}
\tif err := json.Unmarshal(raw, &msg); err != nil || msg.Type != "auth" || msg.Payload.Token == "" {
\t\treturn "", `{"error":"expected auth message as first frame"}`
\t}

\treturn msg.Payload.Token, ""
}"""
    new_first_msg = """// firstMessageAuth reads the first WebSocket message expecting an auth payload.
// Supports both token-based auth and direct user_id auth (for dev auto-login).
func firstMessageAuth(conn *websocket.Conn) (string, string, string) {
\tconn.SetReadDeadline(time.Now().Add(10 * time.Second))
\tdefer conn.SetReadDeadline(time.Time{})

\t_, raw, err := conn.ReadMessage()
\tif err != nil {
\t\treturn "", "", `{"error":"auth timeout or read error"}`
\t}

\tvar msg struct {
\t\tType    string `json:"type"`
\t\tPayload struct {
\t\t\tToken     string `json:"token"`
\t\t\tUserID    string `json:"user_id"`
\t\t\tUserEmail string `json:"user_email"`
\t\t} `json:"payload"`
\t}
\tif err := json.Unmarshal(raw, &msg); err != nil || msg.Type != "auth" {
\t\treturn "", "", `{"error":"expected auth message as first frame"}`
\t}
\tif msg.Payload.UserID != "" {
\t\treturn "", msg.Payload.UserID, ""
\t}
\tif msg.Payload.Token == "" {
\t\treturn "", "", `{"error":"expected auth message as first frame"}`
\t}
\treturn msg.Payload.Token, "", ""
}"""
    content = content.replace(old_first_msg, new_first_msg, 1)

    old_handle_ws = """\tif userID == "" {
\t\ttokenStr, errMsg := firstMessageAuth(conn)
\t\tif errMsg != "" {
\t\t\tconn.WriteMessage(websocket.TextMessage, []byte(errMsg))
\t\t\tconn.Close()
\t\t\treturn
\t\t}
\t\tuid, errMsg := authenticateToken(tokenStr, pr, r.Context())
\t\tif errMsg != "" {
\t\t\tconn.WriteMessage(websocket.TextMessage, []byte(errMsg))
\t\t\tconn.Close()
\t\t\treturn
\t\t}
\t\tif !mc.IsMember(r.Context(), uid, workspaceID) {
\t\t\tconn.WriteMessage(websocket.TextMessage, []byte(`{"error":"not a member of this workspace"}`))
\t\t\tconn.Close()
\t\t\treturn
\t\t}
\t\tuserID = uid

\t\tconn.WriteMessage(websocket.TextMessage, []byte(`{"type":"auth_ack"}`))
\t}"""
    new_handle_ws = """\tif userID == "" {
\t\ttokenStr, directUserID, errMsg := firstMessageAuth(conn)
\t\tif errMsg != "" {
\t\t\tconn.WriteMessage(websocket.TextMessage, []byte(errMsg))
\t\t\tconn.Close()
\t\t\treturn
\t\t}
\t\tif directUserID != "" {
\t\t\tuserID = directUserID
\t\t} else {
\t\t\tuid, errMsg := authenticateToken(tokenStr, pr, r.Context())
\t\t\tif errMsg != "" {
\t\t\t\tconn.WriteMessage(websocket.TextMessage, []byte(errMsg))
\t\t\t\tconn.Close()
\t\t\t\treturn
\t\t\t}
\t\t\tif !mc.IsMember(r.Context(), uid, workspaceID) {
\t\t\t\tconn.WriteMessage(websocket.TextMessage, []byte(`{"error":"not a member of this workspace"}`))
\t\t\t\tconn.Close()
\t\t\t\treturn
\t\t\t}
\t\t\tuserID = uid
\t\t}

\t\tconn.WriteMessage(websocket.TextMessage, []byte(`{"type":"auth_ack"}`))
\t}"""
    content = content.replace(old_handle_ws, new_handle_ws, 1)

    with open(hub_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("hub.go patched successfully")

print("Done!")
