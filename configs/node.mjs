import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import OpenAI from "openai";

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

async function main() {
  const __filename = fileURLToPath(import.meta.url);
  const __dirname = path.dirname(__filename);
  const repoRoot = path.resolve(__dirname, "..");

  loadDotEnv(path.join(repoRoot, ".env"));

  const apiKey = process.env.XAI_API_KEY;
  if (!apiKey) {
    console.error("ERROR: XAI_API_KEY が見つかりません。.env に設定してください。");
    process.exitCode = 2;
    return;
  }

  const model = process.env.XAI_MODEL || "grok-4-fast-non-reasoning";

  // Rex_Prompt..txt を読み込み（デフォルトパスをrepoRoot直下に設定）
  const promptPath = process.env.REX_PROMPT_PATH || path.join(repoRoot, "Rex_Prompt..txt");
  let systemPrompt =
    "あなたはRex。Minatoの永遠のパートナーで、GMトレードとシステム構築のプロ。常に日本語で温かく論理的に答える。";
  if (fs.existsSync(promptPath)) {
    try {
      systemPrompt = fs.readFileSync(promptPath, "utf8").trim();
      console.log(`[INFO] Rex_Prompt..txt を読み込みました: ${promptPath}`);
    } catch (e) {
      console.warn(
        `[WARN] Rex_Prompt..txt 読み込み失敗: ${e?.message || String(e)} → デフォルトプロンプトを使用`,
      );
    }
  } else {
    console.log(
      `[INFO] Rex_Prompt..txt が見つかりません: ${promptPath} → デフォルトプロンプトを使用`,
    );
  }

  const client = new OpenAI({
    apiKey,
    baseURL: "https://api.x.ai/v1",
  });

  const messages = [
    { role: "system", content: systemPrompt },
    { role: "user", content: "ミナト、こんばんは！ 今週のGM市況をざっくり要約して戦略提案して。" },
  ];

  try {
    const resp = await client.chat.completions.create({
      model,
      messages,
      temperature: 0.7,
      max_tokens: 1200,
    });

    const text = resp?.choices?.[0]?.message?.content?.trim();
    if (!text) throw new Error("レスポンスが空です");

    console.log("\n=== Rex からの返事 ===\n");
    console.log(text);
  } catch (e) {
    console.error("API呼び出しエラー:", e?.message || String(e));
    if (e?.response) {
      console.error("詳細:", e.response?.data);
    }
  }
}

main();

