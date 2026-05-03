import fs from "fs";
import path from "path";

const PROJECT_ROOT = "";
const AGENTS_MD_NAMES = ["AGENTS.md", "AGENTS.override.md", "CLAUDE.md"];
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

const docs = collectAgentDocs(PROJECT_ROOT);
console.log("=== AGENTS.md Discovery Test ===");
console.log(`Project root: ${findProjectRoot(PROJECT_ROOT)}`);
console.log(`Found ${docs.length} doc files:`);
for (const d of docs) {
  console.log(`  ${d.name} (${d.path}) - ${d.content.length} chars`);
}
if (docs.length === 0) {
  console.log("No AGENTS.md/CLAUDE.md/TRAE rules found - this is normal for first run");
  console.log("The MCP server will work once you create AGENTS.md in your projects");
}
