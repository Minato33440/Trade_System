// Usage:
//   node .\configs\grok_api_call.js
//   node .\configs\grok_api_call.js "Rexとして、短編のプロット案を3つ出して"
//
// Requirements:
//   - REX_Trade_System\.env に XAI_API_KEY=... を設定

const fs = require("fs");
const path = require("path");
const readline = require("readline");

function loadDotEnv(dotEnvPath) {
  if (!fs.existsSync(dotEnvPath)) return;
  const raw = fs.readFileSync(dotEnvPath, "utf8");
  for (const line of raw.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const eq = trimmed.indexOf("=");
    if (eq <= 0) continue;
    const key = trimmed.slice(0, eq).trim();
    let value = trimmed.slice(eq + 1).trim();
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }
    if (!process.env[key]) process.env[key] = value;
  }
}

function ensureDirExists(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

function readTextIfExists(p) {
  try {
    if (!fs.existsSync(p)) return null;
    return fs.readFileSync(p, "utf8");
  } catch {
    return null;
  }
}

function parsePositiveInt(value, fallback) {
  const n = Number.parseInt(String(value ?? ""), 10);
  return Number.isFinite(n) && n > 0 ? n : fallback;
}

function atomicWriteFileSync(filePath, content) {
  const dir = path.dirname(filePath);
  ensureDirExists(dir);
  const tmpPath = path.join(
    dir,
    `.${path.basename(filePath)}.${process.pid}.${Date.now()}.tmp`,
  );
  fs.writeFileSync(tmpPath, content, "utf8");
  fs.renameSync(tmpPath, filePath);
}

function loadConversationHistory(historyPath) {
  const raw = readTextIfExists(historyPath);
  if (!raw) return null;
  const trimmed = raw.trim();
  if (!trimmed) return null;

  try {
    const json = JSON.parse(trimmed);
    const messages = Array.isArray(json?.messages) ? json.messages : null;
    if (!messages) return null;

    const cleaned = [];
    for (const m of messages) {
      if (!m || typeof m !== "object") continue;
      const role = m.role;
      const content = m.content;
      if (
        (role === "system" || role === "user" || role === "assistant") &&
        typeof content === "string" &&
        content.trim() !== ""
      ) {
        cleaned.push({ role, content });
      }
    }
    return cleaned.length ? cleaned : null;
  } catch (e) {
    // Preserve the corrupted file for debugging.
    try {
      const dir = path.dirname(historyPath);
      const backup = path.join(dir, `conversation_history.corrupt.${Date.now()}.json`);
      ensureDirExists(dir);
      fs.renameSync(historyPath, backup);
      process.stderr.write(
        `WARN: conversation_history.json が壊れていたため退避しました: ${backup}\n`,
      );
    } catch {
      // ignore
    }
    return null;
  }
}

function saveConversationHistory(historyPath, messages, { model }) {
  const maxMessages = parsePositiveInt(process.env.XAI_HISTORY_MAX_MESSAGES, 200);
  const trimmed = messages.length > maxMessages ? messages.slice(-maxMessages) : messages;

  const payload = {
    version: 1,
    model,
    updated_at: new Date().toISOString(),
    messages: trimmed,
  };
  atomicWriteFileSync(historyPath, JSON.stringify(payload, null, 2) + "\n");
}

async function callGrokChatCompletions({ apiKey, model, messages }) {
  const res = await fetch("https://api.x.ai/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model,
      messages,
    }),
  });

  const json = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = JSON.stringify(json);
    throw new Error(`HTTP ${res.status} ${res.statusText}: ${detail}`);
  }

  const text = json?.choices?.[0]?.message?.content;
  if (typeof text !== "string") {
    throw new Error(`Unexpected response: ${JSON.stringify(json)}`);
  }
  return text;
}

async function main() {
  const repoRoot = path.resolve(__dirname, "..");
  loadDotEnv(path.join(repoRoot, ".env"));

  const apiKey = process.env.XAI_API_KEY;
  if (!apiKey) {
    console.error("ERROR: XAI_API_KEY が見つかりません。.env か環境変数に設定してください。");
    process.exitCode = 2;
    return;
  }

  const model = process.env.XAI_MODEL || "grok-4";

  const historyPath =
    process.env.XAI_HISTORY_FILE ||
    path.join(repoRoot, "logs", "text_log", "conversation_history.json");

  const rexPromptPath =
    process.env.REX_PROMPT_FILE || path.join(repoRoot, "Rex_Prompt..txt");
  const systemPrompt = readTextIfExists(rexPromptPath);

  const baseMessages = [];
  if (systemPrompt) baseMessages.push({ role: "system", content: systemPrompt });
  else baseMessages.push({ role: "system", content: "You are a helpful assistant. Answer in Japanese." });

  // Load persisted history and continue the same conversation.
  // If the loaded history already contains a system message, prefer it.
  const loaded = loadConversationHistory(historyPath);
  const messages =
    loaded?.some((m) => m.role === "system") ? [...loaded] : [...baseMessages, ...(loaded || [])];

  const argPrompt = process.argv.slice(2).join(" ").trim();
  if (argPrompt) {
    messages.push({ role: "user", content: argPrompt });
    const text = await callGrokChatCompletions({ apiKey, model, messages });
    messages.push({ role: "assistant", content: text });
    saveConversationHistory(historyPath, messages, { model });
    process.stdout.write(String(text).trim() + "\n");
    return;
  }

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: true,
  });

  const question = (q) => new Promise((resolve) => rl.question(q, resolve));

  process.stdout.write(`Grok Assistant ready (model=${model}). Empty line to exit.\n`);

  while (true) {
    const prompt = (await question("> ")).trim();
    if (!prompt) break;

    messages.push({ role: "user", content: prompt });
    try {
      const text = await callGrokChatCompletions({ apiKey, model, messages });
      messages.push({ role: "assistant", content: text });
      saveConversationHistory(historyPath, messages, { model });
      process.stdout.write(String(text).trim() + "\n\n");
    } catch (e) {
      process.stderr.write(`ERROR: ${e?.message || String(e)}\n\n`);
    }
  }

  // Save on exit as well (in case last turn errored).
  try {
    saveConversationHistory(historyPath, messages, { model });
  } catch {
    // ignore
  }
  rl.close();
}

main().catch((e) => {
  console.error(`FATAL: ${e?.message || String(e)}`);
  process.exitCode = 1;
});

