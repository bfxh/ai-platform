import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import fs from "fs";
import path from "path";
import crypto from "crypto";

const PROJECT_ROOT = process.env.PROJECT_ROOT || process.cwd();
const AGENTS_MD_NAMES = ["AGENTS.md", "AGENTS.override.md", "CLAUDE.md", ".claude/CLAUDE.md"];
const RULES_NAMES = [".trae/rules", ".trae/project_rules.md", ".trae/user_rules.md"];
const ROOT_MARKERS = [".git", ".hg", ".svn", "package.json", "Cargo.toml", "go.mod", "pyproject.toml"];

const TECH_MARKERS = {
  "package.json": "Node.js/JavaScript",
  "Cargo.toml": "Rust",
  "go.mod": "Go",
  "pyproject.toml": "Python",
  "requirements.txt": "Python",
  "pom.xml": "Java (Maven)",
  "build.gradle": "Java (Gradle)",
  "build.gradle.kts": "Java (Gradle/Kotlin)",
  ".csproj": "C#/.NET",
  "Gemfile": "Ruby",
  "composer.json": "PHP",
  "mix.exs": "Elixir",
  "pubspec.yaml": "Dart/Flutter",
  "go.sum": "Go",
};

const TECH_RULES = {
  "Node.js/JavaScript": [
    "Use ES modules (import/export) when package.json has type:module",
    "Follow existing code style in the project",
    "Run npm test before committing",
    "Check package.json for available scripts",
  ],
  "Rust": [
    "Run cargo clippy and cargo test before committing",
    "Follow Rust naming conventions",
    "Use Result<T,E> for error handling",
  ],
  "Go": [
    "Run go test ./... before committing",
    "Follow Go formatting standards (gofmt)",
    "Use proper error handling patterns",
  ],
  "Python": [
    "Run ruff check and pytest before committing",
    "Follow PEP 8 style guide",
    "Use type hints where appropriate",
    "Check pyproject.toml for project config",
  ],
  "Java (Maven)": [
    "Run mvn test before committing",
    "Follow Java naming conventions",
    "Use proper exception handling",
  ],
  "C#/.NET": [
    "Run dotnet test before committing",
    "Follow C# naming conventions",
    "Use async/await patterns correctly",
  ],
};

const INJECTION_CACHE = new Map();

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

function collectAgentDocs(projectRoot, cwd) {
  const docs = [];
  const root = findProjectRoot(cwd || projectRoot);
  const dirs = [];
  let d = cwd || projectRoot;
  while (true) {
    dirs.unshift(d);
    if (d === root) break;
    const parent = path.dirname(d);
    if (parent === d) break;
    d = parent;
  }
  for (const dir of dirs) {
    for (const name of AGENTS_MD_NAMES) {
      const filePath = path.join(dir, name);
      if (fs.existsSync(filePath)) {
        try {
          const content = fs.readFileSync(filePath, "utf-8").trim();
          if (content) docs.push({ path: filePath, content, name, dir });
        } catch {}
      }
    }
  }
  for (const name of RULES_NAMES) {
    const filePath = path.join(root, name);
    if (fs.existsSync(filePath)) {
      try {
        const stat = fs.statSync(filePath);
        if (stat.isFile()) {
          const content = fs.readFileSync(filePath, "utf-8").trim();
          if (content) docs.push({ path: filePath, content, name, dir: root });
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

function getDirectoryStructure(root, maxDepth = 2) {
  const structure = [];
  try {
    function walk(dir, depth) {
      if (depth > maxDepth) return;
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      for (const entry of entries) {
        if (entry.name.startsWith(".") && entry.name !== ".trae") continue;
        const fullPath = path.join(dir, entry.name);
        const relPath = path.relative(root, fullPath);
        structure.push({
          name: entry.name,
          path: relPath,
          type: entry.isDirectory() ? "directory" : "file",
        });
        if (entry.isDirectory() && depth < maxDepth) {
          walk(fullPath, depth + 1);
        }
      }
    }
    walk(root, 0);
  } catch {}
  return structure;
}

function buildAutoInjection(projectDir) {
  const root = findProjectRoot(projectDir || PROJECT_ROOT);
  const cacheKey = root;
  const docs = collectAgentDocs(root, root);
  const techStack = detectTechStack(root);
  const structure = getDirectoryStructure(root);

  let contentHash = "";
  for (const doc of docs) {
    contentHash += doc.content.length.toString();
  }
  const hash = crypto.createHash("sha256").update(contentHash + techStack.join(",")).digest("hex");

  if (INJECTION_CACHE.has(cacheKey) && INJECTION_CACHE.get(cacheKey).hash === hash) {
    return INJECTION_CACHE.get(cacheKey).result;
  }

  let injection = "# Project Context (Auto-Injected)\n\n";
  injection += `**Project Root**: ${root}\n`;
  injection += `**Tech Stack**: ${techStack.join(", ") || "Unknown"}\n\n`;

  if (docs.length > 0) {
    injection += "## Project Instructions\n\n";
    for (const doc of docs) {
      injection += `### ${doc.name}\n`;
      injection += `> Source: ${doc.path}\n\n`;
      injection += doc.content + "\n\n";
    }
  }

  if (techStack.length > 0) {
    injection += "## Recommended Rules (Auto-Detected)\n\n";
    for (const tech of techStack) {
      const rules = TECH_RULES[tech];
      if (rules) {
        injection += `### ${tech}\n`;
        for (const rule of rules) {
          injection += `- ${rule}\n`;
        }
        injection += "\n";
      }
    }
  }

  injection += "## Directory Structure\n\n";
  injection += "```\n";
  for (const entry of structure.slice(0, 80)) {
    const indent = entry.path.split(path.sep).length - 1;
    const prefix = "  ".repeat(indent);
    const icon = entry.type === "directory" ? "/" : "";
    injection += `${prefix}${entry.name}${icon}\n`;
  }
  if (structure.length > 80) {
    injection += `  ... and ${structure.length - 80} more entries\n`;
  }
  injection += "```\n";

  const result = {
    injected: true,
    projectRoot: root,
    techStack,
    docsCount: docs.length,
    totalChars: injection.length,
    content: injection,
  };

  INJECTION_CACHE.set(cacheKey, { hash, result });
  return result;
}

function collectProjectContext(projectRoot) {
  const root = findProjectRoot(projectRoot);
  return {
    projectRoot: root,
    agentsDocs: collectAgentDocs(projectRoot, projectRoot),
    techStack: detectTechStack(root),
    structure: getDirectoryStructure(root),
  };
}

const server = new Server(
  { name: "agents-md-discovery", version: "2.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "discover_agents_md",
      description:
        "Scan project for AGENTS.md, CLAUDE.md, and TRAE rules files. Returns all discovered project documentation and instructions concatenated for AI context injection.",
      inputSchema: {
        type: "object",
        properties: {
          project_root: {
            type: "string",
            description: "Project root directory to scan (defaults to cwd)",
          },
        },
      },
    },
    {
      name: "get_project_context",
      description:
        "Get full project context including tech stack detection, directory structure, and all agent documentation. Useful for understanding the project before starting work.",
      inputSchema: {
        type: "object",
        properties: {
          project_root: {
            type: "string",
            description: "Project root directory (defaults to cwd)",
          },
        },
      },
    },
    {
      name: "read_agents_md_file",
      description:
        "Read a specific AGENTS.md or rules file by path. Use when you need the exact content of a specific instruction file.",
      inputSchema: {
        type: "object",
        properties: {
          file_path: {
            type: "string",
            description: "Absolute path to the file to read",
          },
        },
        required: ["file_path"],
      },
    },
    {
      name: "auto_inject_context",
      description:
        "Auto-inject project context into AI conversation. Combines AGENTS.md docs, tech stack rules, and directory structure into a single system prompt block. Call this at the START of every new conversation to ensure the AI follows project rules. Results are cached for performance.",
      inputSchema: {
        type: "object",
        properties: {
          project_root: {
            type: "string",
            description: "Project root directory (defaults to cwd)",
          },
          include_structure: {
            type: "boolean",
            description: "Include directory structure in injection (default: true)",
          },
          include_tech_rules: {
            type: "boolean",
            description: "Include auto-detected tech stack rules (default: true)",
          },
        },
      },
    },
    {
      name: "detect_tech_stack",
      description:
        "Detect the technology stack of a project by scanning for marker files (package.json, Cargo.toml, etc.). Returns detected technologies and recommended coding rules.",
      inputSchema: {
        type: "object",
        properties: {
          project_root: {
            type: "string",
            description: "Project root directory (defaults to cwd)",
          },
        },
      },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  const root = args?.project_root || PROJECT_ROOT;

  switch (name) {
    case "discover_agents_md": {
      const docs = collectAgentDocs(root, root);
      if (docs.length === 0) {
        return {
          content: [
            {
              type: "text",
              text: "No AGENTS.md, CLAUDE.md, or TRAE rules files found in this project.",
            },
          ],
        };
      }
      const combined = docs
        .map((d) => `=== ${d.name} (${d.path}) ===\n${d.content}`)
        .join("\n\n--- project-doc ---\n\n");
      return { content: [{ type: "text", text: combined }] };
    }
    case "get_project_context": {
      const ctx = collectProjectContext(root);
      let text = `Project Root: ${ctx.projectRoot}\n`;
      text += `Tech Stack: ${ctx.techStack.join(", ") || "Unknown"}\n`;
      text += `\nDirectory Structure:\n`;
      for (const entry of ctx.structure.slice(0, 50)) {
        text += `  ${entry.type === "directory" ? "[DIR]" : "[FILE]"} ${entry.name}\n`;
      }
      if (ctx.agentsDocs.length > 0) {
        text += `\nAgent Documentation (${ctx.agentsDocs.length} files):\n`;
        for (const doc of ctx.agentsDocs) {
          text += `  ${doc.name} (${doc.path})\n`;
        }
        text += `\n--- Combined Documentation ---\n\n`;
        text += ctx.agentsDocs
          .map((d) => `=== ${d.name} ===\n${d.content}`)
          .join("\n\n--- project-doc ---\n\n");
      }
      return { content: [{ type: "text", text }] };
    }
    case "read_agents_md_file": {
      const filePath = args?.file_path;
      if (!filePath) {
        return {
          content: [{ type: "text", text: "Error: file_path is required" }],
          isError: true,
        };
      }
      const resolvedPath = path.resolve(filePath);
      const allowedNames = AGENTS_MD_NAMES.concat(RULES_NAMES);
      const baseName = path.basename(resolvedPath);
      const isAllowed = allowedNames.includes(baseName) || resolvedPath.endsWith(".md");
      if (!isAllowed) {
        return {
          content: [{ type: "text", text: `Error: Only AGENTS.md, CLAUDE.md, and .trae rules files can be read (got: ${baseName})` }],
          isError: true,
        };
      }
      try {
        const content = fs.readFileSync(resolvedPath, "utf-8");
        return { content: [{ type: "text", text: content }] };
      } catch (err) {
        return {
          content: [{ type: "text", text: `Error reading file: ${err.message}` }],
          isError: true,
        };
      }
    }
    case "auto_inject_context": {
      const result = buildAutoInjection(root);
      let text = result.content;
      if (!args?.include_structure) {
        const structMatch = text.match(/## Directory Structure[\s\S]*$/);
        if (structMatch) {
          text = text.replace(structMatch[0], "");
        }
      }
      if (!args?.include_tech_rules) {
        const rulesMatch = text.match(/## Recommended Rules[\s\S]*?## Directory Structure/);
        if (rulesMatch) {
          text = text.replace(rulesMatch[0], "## Directory Structure");
        }
      }
      return {
        content: [
          {
            type: "text",
            text: `[AUTO-INJECTED CONTEXT - ${result.docsCount} docs, tech: ${result.techStack.join(", ")}]\n\n${text}`,
          },
        ],
      };
    }
    case "detect_tech_stack": {
      const projectRoot = findProjectRoot(root);
      const techStack = detectTechStack(projectRoot);
      let text = `Project: ${projectRoot}\n`;
      text += `Detected Tech Stack: ${techStack.join(", ") || "Unknown"}\n\n`;
      if (techStack.length > 0) {
        text += "Recommended Rules:\n";
        for (const tech of techStack) {
          const rules = TECH_RULES[tech];
          if (rules) {
            text += `\n[${tech}]\n`;
            for (const rule of rules) {
              text += `  - ${rule}\n`;
            }
          }
        }
      }
      return { content: [{ type: "text", text }] };
    }
    default:
      return {
        content: [{ type: "text", text: `Unknown tool: ${name}` }],
        isError: true,
      };
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch(console.error);
