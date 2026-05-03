import { WebSocketServer } from "ws";
import http from "http";
import fs from "fs";
import path from "path";

const OLLAMA_BASE = process.env.OLLAMA_BASE || "http://localhost:11434";
const WS_PORT = parseInt(process.env.WS_PORT || "11435");
const HTTP_PORT = parseInt(process.env.HTTP_PORT || "11436");
const DEFAULT_MODEL = process.env.DEFAULT_MODEL || "qwen2.5-coder:7b";
const PROJECT_ROOT = process.env.PROJECT_ROOT || "";

const AGENTS_MD_NAMES = ["AGENTS.md", "AGENTS.override.md", "CLAUDE.md", ".claude/CLAUDE.md"];
const RULES_NAMES = [".trae/rules", ".trae/project_rules.md", ".trae/user_rules.md"];
const ROOT_MARKERS = [".git", "package.json", "Cargo.toml", "go.mod", "pyproject.toml"];

function findProjectRoot(startDir) {
  let dir = startDir;
  for (let i = 0; i < 20; i++) {
    for (const marker of ROOT_MARKERS) {
      if (fs.existsSync(path.join(dir, marker))) return dir;
    }
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return startDir;
}

function collectAgentDocs(cwd) {
  const docs = [];
  const root = findProjectRoot(cwd);
  const dirs = [];
  let d = cwd;
  while (true) {
    dirs.unshift(d);
    if (d === root) break;
    const parent = path.dirname(d);
    if (parent === d) break;
    d = parent;
  }
  for (const dir of dirs) {
    for (const name of AGENTS_MD_NAMES) {
      const fp = path.join(dir, name);
      if (fs.existsSync(fp)) {
        try {
          const content = fs.readFileSync(fp, "utf-8").trim();
          if (content) docs.push({ path: fp, content, name });
        } catch {}
      }
    }
  }
  for (const name of RULES_NAMES) {
    const fp = path.join(root, name);
    if (fs.existsSync(fp)) {
      try {
        const stat = fs.statSync(fp);
        if (stat.isFile()) {
          const content = fs.readFileSync(fp, "utf-8").trim();
          if (content) docs.push({ path: fp, content, name });
        }
      } catch {}
    }
  }
  return docs;
}

function buildSystemPrompt(projectDir) {
  const docs = collectAgentDocs(projectDir || PROJECT_ROOT);
  let system = "You are an AI coding assistant integrated into TRAE IDE.\n\n";
  if (docs.length > 0) {
    system += "=== Project Instructions ===\n\n";
    for (const doc of docs) {
      system += `--- ${doc.name} ---\n${doc.content}\n\n`;
    }
  }
  system += "Follow the project instructions above when responding. Use the appropriate tools and follow coding conventions specified in the project rules.";
  return system;
}

async function ollamaChat(messages, model, stream = false) {
  const body = {
    model: model || DEFAULT_MODEL,
    messages,
    stream,
    options: {
      temperature: 0.7,
      top_p: 0.9,
    },
  };

  const url = `${OLLAMA_BASE}/api/chat`;
  const resp = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!resp.ok) {
    const errText = await resp.text();
    throw new Error(`Ollama API error ${resp.status}: ${errText}`);
  }

  return resp;
}

async function ollamaChatStream(messages, model, onChunk) {
  const body = {
    model: model || DEFAULT_MODEL,
    messages,
    stream: true,
    options: {
      temperature: 0.7,
      top_p: 0.9,
    },
  };

  const url = `${OLLAMA_BASE}/api/chat`;
  const resp = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!resp.ok) {
    const errText = await resp.text();
    throw new Error(`Ollama API error ${resp.status}: ${errText}`);
  }

  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (!line.trim()) continue;
      try {
        const chunk = JSON.parse(line);
        if (chunk.message?.content) {
          await onChunk(chunk.message.content, chunk.done || false);
        }
        if (chunk.done) return;
      } catch {}
    }
  }
}

async function ollamaGenerate(prompt, model) {
  const body = {
    model: model || DEFAULT_MODEL,
    prompt,
    stream: false,
  };

  const url = `${OLLAMA_BASE}/api/generate`;
  const resp = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!resp.ok) {
    const errText = await resp.text();
    throw new Error(`Ollama generate error ${resp.status}: ${errText}`);
  }

  return await resp.json();
}

async function listModels() {
  try {
    const resp = await fetch(`${OLLAMA_BASE}/api/tags`);
    if (!resp.ok) return [];
    const data = await resp.json();
    return (data.models || []).map((m) => ({
      name: m.name,
      size: m.size,
      modified: m.modified_at,
    }));
  } catch {
    return [];
  }
}

function convertTraeWsMessage(data) {
  let msg;
  try {
    msg = typeof data === "string" ? JSON.parse(data) : data;
  } catch {
    return null;
  }

  if (msg.messages && Array.isArray(msg.messages)) {
    const messages = msg.messages.map((m) => ({
      role: m.role || "user",
      content: m.content || "",
    }));

    if (!messages.some((m) => m.role === "system")) {
      messages.unshift({
        role: "system",
        content: buildSystemPrompt(msg.projectDir),
      });
    }

    return {
      type: "chat",
      messages,
      model: msg.model || DEFAULT_MODEL,
      stream: msg.stream !== false,
      requestId: msg.requestId || msg.id || Date.now().toString(),
    };
  }

  if (msg.prompt) {
    return {
      type: "generate",
      prompt: msg.prompt,
      model: msg.model || DEFAULT_MODEL,
      requestId: msg.requestId || msg.id || Date.now().toString(),
    };
  }

  if (msg.action === "list_models" || msg.type === "list_models") {
    return { type: "list_models", requestId: msg.requestId || Date.now().toString() };
  }

  if (msg.action === "ping" || msg.type === "ping") {
    return { type: "ping", requestId: msg.requestId || Date.now().toString() };
  }

  return null;
}

const wss = new WebSocketServer({ port: WS_PORT });

wss.on("connection", (ws, req) => {
  const origin = req.headers.origin || "";
  const allowed = ["http://localhost", "http://127.0.0.1", "null"];
  if (origin && !allowed.some(o => origin.startsWith(o))) {
    ws.close(403, "Forbidden origin");
    return;
  }
  const clientIp = req.socket.remoteAddress;
  console.log(`[WS] Client connected: ${clientIp}`);

  ws.on("message", async (raw) => {
    const parsed = convertTraeWsMessage(raw);
    if (!parsed) {
      ws.send(JSON.stringify({ error: "Invalid message format", requestId: null }));
      return;
    }

    console.log(`[WS] Request: type=${parsed.type} model=${parsed.model || "default"}`);

    try {
      switch (parsed.type) {
        case "chat": {
          if (parsed.stream) {
            await ollamaChatStream(parsed.messages, parsed.model, async (content, done) => {
              ws.send(
                JSON.stringify({
                  type: "chunk",
                  content,
                  done,
                  requestId: parsed.requestId,
                })
              );
            });
          } else {
            const resp = await ollamaChat(parsed.messages, parsed.model, false);
            const data = await resp.json();
            ws.send(
              JSON.stringify({
                type: "response",
                content: data.message?.content || "",
                model: data.model,
                requestId: parsed.requestId,
                done: true,
              })
            );
          }
          break;
        }
        case "generate": {
          const result = await ollamaGenerate(parsed.prompt, parsed.model);
          ws.send(
            JSON.stringify({
              type: "response",
              content: result.response || "",
              model: result.model,
              requestId: parsed.requestId,
              done: true,
            })
          );
          break;
        }
        case "list_models": {
          const models = await listModels();
          ws.send(
            JSON.stringify({
              type: "models",
              models,
              requestId: parsed.requestId,
            })
          );
          break;
        }
        case "ping": {
          ws.send(
            JSON.stringify({
              type: "pong",
              requestId: parsed.requestId,
            })
          );
          break;
        }
      }
    } catch (err) {
      console.error(`[WS] Error: ${err.message}`);
      ws.send(
        JSON.stringify({
          type: "error",
          error: err.message,
          requestId: parsed.requestId,
        })
      );
    }
  });

  ws.on("close", () => {
    console.log(`[WS] Client disconnected: ${clientIp}`);
  });

  ws.send(
    JSON.stringify({
      type: "welcome",
      message: "Ollama-WS Bridge ready",
      defaultModel: DEFAULT_MODEL,
      models: "Use list_models to query",
    })
  );
});

const httpServer = http.createServer(async (req, res) => {
  const origin = req.headers.origin || "";
  const allowed = ["http://localhost", "http://127.0.0.1", "null"];
  if (allowed.some(o => origin.startsWith(o)) || !origin) {
    res.setHeader("Access-Control-Allow-Origin", origin || "http://localhost");
  }
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");

  if (req.method === "OPTIONS") {
    res.writeHead(204);
    res.end();
    return;
  }

  if (req.url === "/health" && req.method === "GET") {
    const models = await listModels();
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(
      JSON.stringify({
        status: "ok",
        ollama: OLLAMA_BASE,
        defaultModel: DEFAULT_MODEL,
        wsPort: WS_PORT,
        modelsAvailable: models.length,
        models: models.map((m) => m.name),
      })
    );
    return;
  }

  if (req.url === "/models" && req.method === "GET") {
    const models = await listModels();
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ models }));
    return;
  }

  if (req.url === "/chat" && req.method === "POST") {
    let body = "";
    req.on("data", (chunk) => (body += chunk));
    req.on("end", async () => {
      try {
        const { messages, model, projectDir } = JSON.parse(body);
        const allMessages = [...messages];
        if (!allMessages.some((m) => m.role === "system")) {
          allMessages.unshift({ role: "system", content: buildSystemPrompt(projectDir) });
        }
        const resp = await ollamaChat(allMessages, model, false);
        const data = await resp.json();
        res.writeHead(200, { "Content-Type": "application/json" });
        res.end(JSON.stringify(data));
      } catch (err) {
        res.writeHead(500, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ error: err.message }));
      }
    });
    return;
  }

  res.writeHead(404);
  res.end("Not found");
});

httpServer.listen(HTTP_PORT, () => {
  console.log(`[HTTP] REST API on http://localhost:${HTTP_PORT}`);
  console.log(`  GET  /health  - Bridge status`);
  console.log(`  GET  /models  - List Ollama models`);
  console.log(`  POST /chat    - Chat completion`);
});

console.log("=".repeat(60));
console.log("  Ollama-WS Bridge for TRAE");
console.log("=".repeat(60));
console.log(`  Ollama API:  ${OLLAMA_BASE}`);
console.log(`  WS Endpoint: ws://localhost:${WS_PORT}`);
console.log(`  HTTP API:    http://localhost:${HTTP_PORT}`);
console.log(`  Default Model: ${DEFAULT_MODEL}`);
console.log(`  AGENTS.md:   Auto-injection enabled`);
console.log("=".repeat(60));
console.log("Waiting for connections...");
