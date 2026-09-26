import { test, expect } from "@playwright/test";

test("landing and dashboard are navigable, responsive and free of client exceptions", async ({
  page,
}, testInfo) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: /Banking, a little/ }),
  ).toBeVisible();
  await page.screenshot({
    path: testInfo.outputPath("landing-desktop.png"),
    fullPage: true,
  });
  await page
    .getByRole("link", { name: "Explore banking", exact: true })
    .click();
  await expect(page).toHaveURL(/\/register$/);
  await expect(
    page.getByRole("heading", { name: "Create your account" }),
  ).toBeVisible();
  await page.goto("/portal/dashboard");
  await expect(
    page.getByRole("heading", { name: /Good morning, Akhil Doshi/ }),
  ).toBeVisible();
  await page.screenshot({
    path: testInfo.outputPath("dashboard-desktop.png"),
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(
    page.getByRole("button", { name: "Open navigation", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Open navigation", exact: true })
    .click();
  await page.getByRole("link", { name: "My accounts", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "A home for your everyday." }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page.goto("/portal/dashboard");
  await page.screenshot({
    path: testInfo.outputPath("dashboard-mobile.png"),
    fullPage: true,
  });
  await page.goto("/");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page.screenshot({
    path: testInfo.outputPath("landing-mobile.png"),
    fullPage: true,
  });
  expect(errors).toEqual([]);
});

test("account filters combine and show useful empty states", async ({
  page,
}) => {
  await page.goto("/portal/accounts");
  await page.getByRole("button", { name: /Everyday Savings/ }).click();
  await page
    .getByRole("textbox", { name: "Search transactions" })
    .fill("Amazon");
  await expect(page.getByRole("cell", { name: /Amazon India/ })).toBeVisible();
  await expect(page.getByRole("cell", { name: /Tata Power/ })).toHaveCount(0);
  await page.getByLabel("Transaction type").selectOption("credit");
  await expect(
    page.getByRole("heading", { name: "No transactions found" }),
  ).toBeVisible();
  await page.getByLabel("Transaction type").selectOption("all");
  await page.getByRole("textbox", { name: "Search transactions" }).fill("");
  await page.getByLabel("Minimum ₹").fill("60000");
  await expect(
    page.getByRole("cell", { name: /September salary/ }),
  ).toBeVisible();
  await expect(page.getByRole("cell", { name: /Amazon India/ })).toHaveCount(0);
});

test("transfer validates funds, preserves paise, reviews and checks sample OTP", async ({
  page,
}) => {
  await page.goto("/portal/payments");
  await expect(page.locator("main > div[aria-busy]")).toHaveAttribute(
    "aria-busy",
    "false",
  );
  await page.getByLabel("Amount (₹)").fill("200000");
  await page.getByRole("button", { name: "Review transfer" }).click();
  await expect(page.locator("main").getByRole("alert")).toContainText(
    "exceeds your sample account balance",
  );
  await page.getByLabel("Amount (₹)").fill("1000.50");
  await page.getByRole("button", { name: "Review transfer" }).click();
  await expect(page.getByText("₹1,000.50", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Continue", exact: true }).click();
  await page.getByLabel("6-digit sample code").fill("111111");
  await page.getByRole("button", { name: "Confirm simulation" }).click();
  await expect(page.locator("main").getByRole("alert")).toContainText(
    "Use 123456",
  );
  await page.getByLabel("6-digit sample code").fill("123456");
  await page.getByRole("button", { name: "Confirm simulation" }).click();
  await expect(page.getByRole("status")).toContainText("No money moved");
});

test("bill shortcut selects bill flow without hydration errors", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/portal/payments?tab=bills");
  await expect(
    page.getByRole("heading", { name: "Your bills, taken care of." }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Internet", exact: true }).click();
  await page.getByLabel("Consumer / bill reference").fill("SAMPLE123");
  await page.getByLabel("Amount (₹)").fill("999");
  await page.getByRole("button", { name: "Review payment" }).click();
  await expect(page.getByText("Internet · SAMPLE123")).toBeVisible();
  expect(errors).toEqual([]);
});

test("payees can be previewed, edited and removed with confirmation", async ({
  page,
}) => {
  await page.goto("/portal/payees");
  await page.getByRole("button", { name: "Add payee" }).click();
  await page.getByLabel("Full name").fill("Test Person");
  await page.getByLabel("Bank name").fill("Sample Bank");
  await page.getByLabel("Account last four digits").fill("1234");
  await page.getByRole("button", { name: "Save preview" }).click();
  await expect(
    page.getByRole("heading", { name: "Test Person" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Delete Test Person" }).click();
  await expect(
    page.getByText("Remove Test Person from this sample list?"),
  ).toBeVisible();
  await page.getByRole("button", { name: "Confirm removal" }).click();
  await expect(page.getByRole("heading", { name: "Test Person" })).toHaveCount(
    0,
  );
});

test("statement custom period validates and filters records", async ({
  page,
}) => {
  await page.goto("/portal/statements");
  await expect(page.locator("main > div[aria-busy]")).toHaveAttribute(
    "aria-busy",
    "false",
  );
  await page
    .getByRole("combobox", { name: "Period", exact: true })
    .selectOption("custom");
  await expect(
    page.getByRole("button", { name: "View statement" }),
  ).toBeDisabled();
  await page.getByLabel("From", { exact: true }).fill("2026-09-25");
  await page.getByLabel("To", { exact: true }).fill("2026-09-25");
  await page.getByRole("button", { name: "View statement" }).click();
  await expect(page.getByRole("cell", { name: /Amazon India/ })).toBeVisible();
  await expect(
    page.getByRole("cell", { name: /September salary/ }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Print / save as PDF" }),
  ).toBeVisible();
});

test("EMI handles zero interest and comparison is capped at three products", async ({
  page,
}) => {
  await page.goto("/portal/loans");
  await expect(page.locator("main > div[aria-busy]")).toHaveAttribute(
    "aria-busy",
    "false",
  );
  await page
    .getByRole("slider", { name: "Annual interest rate", exact: true })
    .fill("0");
  await expect(page.getByText("₹8,333", { exact: true })).toBeVisible();
  await expect(page.getByText(/Total interest: ₹0/)).toBeVisible();
  await page.goto("/portal/wealth");
  const checks = page.getByRole("checkbox", { name: "Compare product" });
  await checks.nth(0).check();
  await checks.nth(1).check();
  await checks.nth(2).check();
  await expect(checks.nth(3)).toBeDisabled();
  await expect(
    page.getByRole("heading", { name: "A clearer comparison" }),
  ).toBeVisible();
  await checks.nth(1).uncheck();
  await expect(checks.nth(3)).toBeEnabled();
});

test("assistant gives honest sample responses and starts a new conversation", async ({
  page,
}) => {
  await page.goto("/portal/dashboard");
  await page.getByRole("button", { name: "Ask Credora" }).click();
  await page.getByRole("button", { name: "How much did I spend?" }).click();
  await expect(page.getByText(/September spending is ₹34,200/)).toBeVisible();
  await page.getByRole("button", { name: "New conversation" }).click();
  await expect(
    page.getByRole("button", { name: "How much did I spend?" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Close assistant" }).click();
  await expect(
    page.getByRole("region", { name: "Sample banking assistant" }),
  ).toHaveCount(0);
});

test("customer login, sign-up and admin login remain separate", async ({
  page,
}) => {
  await page.goto("/login");
  await expect(
    page.getByRole("heading", { name: "Customer login" }),
  ).toBeVisible();
  await page.getByLabel("Email address").fill("sample@example.com");
  await page.getByLabel("Password", { exact: true }).fill("SampleOnly123");
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await expect(page).toHaveURL(/\/portal\/dashboard$/);
  await expect(page.getByText(/exploring with sample data/)).toBeVisible();
  await page.goto("/login");
  await page.getByRole("link", { name: "Sign up", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Create your account" }),
  ).toBeVisible();
  await page.getByLabel("First name").fill("Sample");
  await page.getByLabel("Last name").fill("Customer");
  await page.getByLabel("Email address").fill("sample@example.com");
  await page.getByLabel("Password", { exact: true }).fill("SampleOnly123");
  await page.getByRole("button", { name: "Sign up", exact: true }).click();
  await expect(page.locator("main").getByRole("alert")).toContainText(
    "no account has been created",
  );
  await page
    .getByRole("navigation", { name: "Login type" })
    .getByRole("link", { name: "Admin", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Admin login" }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Sign up", exact: true }),
  ).toHaveCount(0);
  await page.getByLabel("Administrator email").fill("admin@example.com");
  await page.getByLabel("Password", { exact: true }).fill("SampleOnly123");
  await page.getByRole("button", { name: "Admin login", exact: true }).click();
  await expect(page.locator("main").getByRole("alert")).toContainText(
    "Admin sign-in is not connected yet",
  );
  await expect(page).toHaveURL(/\/admin\/login$/);
  await expect(page.locator("body")).not.toContainText(/demo/i);
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page.goto("/portal/not-a-real-section");
  await expect(
    page.getByRole("heading", { name: "Let’s get you back on track." }),
  ).toBeVisible();
});

for (const section of [
  "scheduled",
  "analytics",
  "recommendations",
  "notifications",
  "settings",
]) {
  test(`${section} loads directly on a narrow viewport`, async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    const errors: string[] = [];
    page.on("pageerror", (error) => errors.push(error.message));
    const response = await page.goto(`/portal/${section}`);
    expect(response?.status()).toBe(200);
    await expect(page.locator("main h1")).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBeTruthy();
    expect(errors).toEqual([]);
  });
}
