// Captures documentation screenshots of the running Credora stack (http://localhost:8080).
// Uses the demo accounts created by backend/scripts/seed.py and the locally installed Edge.
//
//   node scripts/capture-screens.mjs ../docs/images/screens
import { chromium } from "playwright-core";
import { mkdirSync } from "node:fs";
import { join } from "node:path";

const BASE = process.env.CREDORA_URL ?? "http://localhost:8080";
const OUT = process.argv[2] ?? "screens";
const PASSWORD = "PBIP@Demo123";
mkdirSync(OUT, { recursive: true });

async function token(email) {
  const res = await fetch(`${BASE}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password: PASSWORD }),
  });
  if (!res.ok) throw new Error(`login failed for ${email}: ${res.status}`);
  return (await res.json()).access_token;
}

const browser = await chromium.launch({ channel: "msedge", headless: true });

async function shoot(pages, { key, value } = {}) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
  if (key) await context.addInitScript(([k, v]) => localStorage.setItem(k, v), [key, value]);
  const page = await context.newPage();
  for (const [file, path, action] of pages) {
    await page.goto(`${BASE}${path}`, { waitUntil: "networkidle" });
    if (action) await action(page);
    await page.waitForTimeout(1500);
    await page.screenshot({ path: join(OUT, `${file}.png`) });
    console.log("captured", file);
  }
  await context.close();
}

// Public pages
await shoot([
  ["landing", "/"],
  ["customer-login", "/login"],
  ["admin-login", "/admin/login"],
]);

// Customer portal
await shoot(
  [
    ["portal-dashboard", "/portal/dashboard"],
    ["portal-accounts", "/portal/accounts"],
    ["portal-payments", "/portal/payments"],
    ["portal-payees", "/portal/payees"],
    ["portal-statements", "/portal/statements"],
    ["portal-loans", "/portal/loans"],
    ["portal-wealth", "/portal/wealth"],
    ["portal-analytics", "/portal/analytics"],
    ["portal-recommendations", "/portal/recommendations"],
    [
      "portal-ai-assistant",
      "/portal/dashboard",
      async (page) => {
        const button = page.getByRole("button", { name: /assistant|credora ai|ask/i }).first();
        if (await button.count()) await button.click();
      },
    ],
  ],
  { key: "customer_token", value: await token("customer@pbip.demo") },
);

// Internal banking workspace
await shoot(
  [
    ["admin-dashboard", "/admin/dashboard"],
    ["admin-customers", "/admin/customers"],
    ["admin-analytics", "/admin/analytics"],
    ["admin-fraud", "/admin/fraud"],
    ["admin-investigations", "/admin/investigations"],
    ["admin-compliance", "/admin/compliance"],
    ["admin-audit-logs", "/admin/audit-logs"],
  ],
  { key: "admin_token", value: await token("admin@pbip.demo") },
);

await browser.close();
