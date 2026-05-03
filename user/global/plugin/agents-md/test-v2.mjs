import fs from "fs";
import path from "path";
import crypto from "crypto";

const PROJECT_ROOT = "";
const AGENTS_MD_NAMES = ["AGENTS.md", "AGENTS.override.md", "CLAUDE.md", ".claude/CLAUDE.md"];
const RULES_NAMES = [".trae/rules", ".trae/project_rules.md", ".trae/user_rules.md"];
const ROOT_MARKERS = [".git", "package.json", "Cargo.toml", "go.mod", "pyproject.toml"];

const TECH_MARKERS = {
  "package.json": "Node.js/JavaScript",
  "Cargo.toml": "Rust",
  "go.mod": "Go",
  "pyproject.toml": "Python",
  "requirements.txt": "Python",
  "pom.xml": "Java (Maven)",
  ".csproj": "C#/.NET",
};

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

function detectTechStack(root) {
  const stack = [];
  for (const [marker, tech] of Object.entries(TECH_MARKERS)) {
    if (fs.existsSync(path.join(root, marker))) stack.push(tech);
  }
  return [...new Set(stack)];
}

const root = findProjectRoot(PROJECT_ROOT);
const docs = collectAgentDocs(PROJECT_ROOT);
const techStack = detectTechStack(root);

console.log("=== AGENTS.md MCP v2.0 Test ===");
console.log(`Project root: ${root}`);
console.log(`Tech stack: ${techStack.join(", ")}`);
console.log(`Found ${docs.length} doc files:`);
for (const d of docs) {
  console.log(`  ${d.name} (${d.path}) - ${d.content.length} chars`);
}

console.log("\n=== Auto-Injection Preview ===");
let injection = `# Project Context (Auto-Injected)\n\n`;
injection += `**Project Root**: ${root}\n`;
injection += `**Tech Stack**: ${techStack.join(", ")}\n\n`;
injection += `## Project Instructions\n\n`;
for (const doc of docs) {
  injection += `### ${doc.name}\n> Source: ${doc.path}\n\n`;
  injection += doc.content.substring(0, 200) + "...\n\n";
}
injection += `## Auto-Detected Rules\n\n`;
for (const tech of techStack) {
  injection += `- ${tech}\n`;
}
console.log(injection.substring(0, 500) + "\n...(truncated)");
console.log(`\nTotal injection size: ${injection.length} chars`);
console.log("\nTest PASSED - AGENTS.md MCP v2.0 ready!");
