import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const ROUTING_BOOTSTRAP = [
  "Use `using-delivery-flow` as the root routing skill when the request may belong to ongoing delivery threads.",
  "Keep this bootstrap routing-only: decide whether to route into `delivery-flow` or yield to the normal skill ecosystem.",
  "Do not duplicate `delivery-flow` execution semantics here.",
].join("\n");

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

function appendSystemBootstrap(output) {
  if (!Array.isArray(output.system)) {
    output.system = [];
  }

  const hasBootstrap = output.system.some(
    (part) => typeof part === "string" && part.includes(ROUTING_BOOTSTRAP),
  );

  if (!hasBootstrap) {
    output.system.push(ROUTING_BOOTSTRAP);
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
      appendSystemBootstrap(output);
    },
  };
}
