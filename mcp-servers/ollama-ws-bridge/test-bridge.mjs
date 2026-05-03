import { WebSocket } from "ws";

const WS_URL = "ws://localhost:11435";
const HTTP_URL = "http://localhost:11436";

async function testHTTP() {
  console.log("=== Testing HTTP API ===");
  try {
    const resp = await fetch(`${HTTP_URL}/health`);
    const data = await resp.json();
    console.log("Health:", JSON.stringify(data, null, 2));
  } catch (e) {
    console.log("HTTP test failed:", e.message);
    console.log("Make sure the bridge is running: node bridge.mjs");
  }
}

async function testWS() {
  console.log("\n=== Testing WebSocket ===");
  return new Promise((resolve) => {
    const ws = new WebSocket(WS_URL);

    ws.on("open", () => {
      console.log("Connected to WS bridge");
      ws.send(JSON.stringify({ type: "ping" }));
    });

    ws.on("message", (raw) => {
      const msg = JSON.parse(raw.toString());
      console.log("Received:", msg.type, msg.message || msg.content?.substring(0, 100) || "");

      if (msg.type === "pong") {
        console.log("Ping/pong OK! Now listing models...");
        ws.send(JSON.stringify({ type: "list_models" }));
      }

      if (msg.type === "models") {
        console.log(
          "Available models:",
          msg.models.map((m) => m.name).join(", ") || "None - run: ollama pull qwen2.5-coder:7b"
        );
        if (msg.models.length > 0) {
          console.log("\nSending test chat...");
          ws.send(
            JSON.stringify({
              messages: [{ role: "user", content: "Say hello in one sentence." }],
              model: msg.models[0].name,
              stream: false,
              requestId: "test-001",
            })
          );
        } else {
          console.log("No models available. Install one first:");
          console.log("  ollama pull qwen2.5-coder:7b");
          ws.close();
          resolve();
        }
      }

      if (msg.type === "response") {
        console.log("AI Response:", msg.content);
        ws.close();
        resolve();
      }

      if (msg.type === "chunk") {
        process.stdout.write(msg.content);
        if (msg.done) {
          console.log("\n[Stream complete]");
          ws.close();
          resolve();
        }
      }

      if (msg.type === "error") {
        console.log("Error:", msg.error);
        ws.close();
        resolve();
      }
    });

    ws.on("error", (err) => {
      console.log("WS connection failed:", err.message);
      console.log("Make sure the bridge is running: node bridge.mjs");
      resolve();
    });

    setTimeout(() => {
      ws.close();
      resolve();
    }, 15000);
  });
}

await testHTTP();
await testWS();
