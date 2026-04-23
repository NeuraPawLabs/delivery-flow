import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function getRepoRoot({ worktree, directory } = {}) {
  if (typeof worktree === "string" && worktree.length > 0) {
    return path.resolve(worktree);
  }

  return path.resolve(__dirname, "..", "..");
}

function resolveSkillsCandidate(repoRoot, candidate) {
  if (typeof candidate !== "string" || candidate.length === 0) {
    return null;
  }

  if (!path.isAbsolute(candidate)) {
    return null;
  }

  return path.resolve(repoRoot, candidate);
}

function getBootstrapContract(repoRoot) {
  return normalizeBootstrap(
    fs.readFileSync(
      path.join(repoRoot, "skills", "using-delivery-flow", "bootstrap-contract.md"),
      "utf8",
    ),
  );
}

function normalizeBootstrap(text) {
  return text.replace(/\r\n/g, "\n").trim();
}

function canonicalizeBootstrap(text) {
  return normalizeBootstrap(text)
    .split("\n")
    .map((line) => line.trim())
    .join("\n");
}

function ensureSkillsPath(config, repoRoot, skillsPath) {
  const nextSkills = config.skills ? { ...config.skills } : {};
  const nextPaths = Array.isArray(nextSkills.paths) ? [...nextSkills.paths] : [];

  const hasSkillsPath = nextPaths.some(
    (candidate) => resolveSkillsCandidate(repoRoot, candidate) === skillsPath,
  );

  if (!hasSkillsPath) {
    nextPaths.push(skillsPath);
  }

  nextSkills.paths = nextPaths;
  config.skills = nextSkills;
}

function appendSystemBootstrap(output, repoRoot) {
  const bootstrap = getBootstrapContract(repoRoot);
  const canonicalBootstrap = canonicalizeBootstrap(bootstrap);

  if (!Array.isArray(output.system)) {
    output.system = [];
  }

  const hasBootstrap = output.system.some(
    (part) =>
      typeof part === "string" &&
      canonicalizeBootstrap(part).includes(canonicalBootstrap),
  );

  if (!hasBootstrap) {
    output.system.push(bootstrap);
  }
}

export default async function deliveryFlowPlugin(context = {}) {
  const repoRoot = getRepoRoot(context);
  const skillsPath = path.join(repoRoot, "skills");

  return {
    async config(config) {
      ensureSkillsPath(config, repoRoot, skillsPath);
    },
    async "experimental.chat.system.transform"(_input, output) {
      appendSystemBootstrap(output, repoRoot);
    },
  };
}
