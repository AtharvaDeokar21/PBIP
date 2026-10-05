import { test, expect } from "@playwright/test";

test("internal dashboard is navigable and has no client errors", async ({ page }, testInfo) => {
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.goto("/admin/dashboard");
  await expect(page.getByRole("heading", { name: "Dashboard", exact: true })).toBeVisible();
  await expect(page.getByRole("region", { name: "Recent alerts" })).toBeVisible();
  await expect(page.getByText("FA-2041", { exact: true })).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("admin-dashboard-desktop.png"), fullPage: true });
  await page.getByRole("link", { name: "Review customers" }).click();
  await expect(page).toHaveURL(/alerts=active/);
  await expect(page.getByRole("heading", { name: "Customers", exact: true })).toBeVisible();
  expect(errors).toEqual([]);
});

test("customer filters, pagination, sorting and detail round-trip work", async ({ page }, testInfo) => {
  await page.goto("/admin/customers");
  const directory = page.getByRole("region", { name: "Customer directory", exact: true });
  await expect(directory.getByRole("row")).toHaveCount(6);
  await page.getByRole("button", { name: "Next page" }).click();
  await expect(page.getByText("6–10 of 12 customers")).toBeVisible();
  await page.getByLabel("Risk level", { exact: true }).selectOption("High");
  await expect(directory.getByRole("row")).toHaveCount(4);
  await expect(page.getByText("1–3 of 3 customers")).toBeVisible();
  await page.getByLabel("Sort by", { exact: true }).selectOption("risk");
  await expect(directory.getByRole("row").nth(1)).toContainText("Diya Mehta");
  await page.getByLabel("Search customers by name, ID or email").fill("no-such-customer");
  await expect(page.getByRole("heading", { name: "No matching records" })).toBeVisible();
  await page.getByRole("button", { name: "Clear filters", exact: true }).first().click();
  await expect(directory.getByRole("row")).toHaveCount(6);
  await page.getByLabel("Search customers by name, ID or email").fill("C1002");
  await expect(directory.getByRole("row")).toHaveCount(2);
  await page.screenshot({ path: testInfo.outputPath("admin-customers.png"), fullPage: true });
  await page.getByRole("link", { name: "View details for Diya Mehta" }).click();
  await expect(page.getByRole("heading", { name: "Diya Mehta", exact: true })).toBeVisible();
  await expect(page.getByRole("region", { name: "Customer accounts" })).toContainText("•••• ••••");
  await expect(page.getByRole("region", { name: "Customer transactions" })).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("admin-customer-details.png"), fullPage: true });
  await page.getByRole("link", { name: "View full behaviour analytics" }).first().click();
  await expect(page).toHaveURL(/customer=C1002/);
  await expect(page.getByLabel("Customer", { exact: true })).toHaveValue("C1002");
  const behaviour = page.getByRole("region", { name: "Customer behaviour", exact: true });
  await expect(behaviour.getByRole("row")).toHaveCount(2);
  await page.getByRole("link", { name: "View customer Diya Mehta", exact: true }).click();
  await expect(page).toHaveURL(/\/admin\/customers\/C1002$/);
});

test("analytics combines period, segment, product and customer filters", async ({ page }, testInfo) => {
  await page.goto("/admin/analytics");
  await expect(page.getByRole("heading", { name: "Behaviour analytics", exact: true })).toBeVisible();
  await page.getByLabel("Customer segment", { exact: true }).selectOption("Premium");
  await page.getByLabel("Product interest", { exact: true }).selectOption("Loans");
  const behaviour = page.getByRole("region", { name: "Customer behaviour", exact: true });
  await expect(behaviour.getByRole("row")).toHaveCount(2);
  await expect(behaviour).toContainText("Ishaan Patel");
  await expect(behaviour).not.toContainText("Diya Mehta");
  await page.getByLabel("Date range", { exact: true }).selectOption("custom");
  await page.getByLabel("Analytics from date").fill("2026-06-01");
  await page.getByLabel("Analytics to date").fill("2026-06-30");
  await expect(page.getByRole("heading", { name: "No matching records" })).toBeVisible();
  await page.getByRole("button", { name: "Reset filters" }).click();
  await expect(page.getByRole("region", { name: "Customer behaviour", exact: true }).getByRole("row")).toHaveCount(13);
  await page.screenshot({ path: testInfo.outputPath("admin-analytics.png"), fullPage: true });
});

test("admin sign-in opens the internal workspace and missing customer is handled", async ({ page }) => {
  await page.goto("/admin/login");
  await page.getByLabel("Administrator email").fill("admin@example.com");
  await page.getByLabel("Password", { exact: true }).fill("SampleOnly123");
  await page.getByRole("button", { name: "Admin login", exact: true }).click();
  await expect(page).toHaveURL(/\/admin\/dashboard$/);
  await expect(page.getByRole("heading", { name: "Dashboard", exact: true })).toBeVisible();
  await page.goto("/admin/customers/unknown");
  await expect(page.getByRole("heading", { name: "Customer not found" })).toBeVisible();
  await page.getByRole("link", { name: "Back to Customers" }).click();
  await expect(page).toHaveURL(/\/admin\/customers$/);
});

test("tablet and mobile admin pages contain table overflow and support navigation", async ({ page }, testInfo) => {
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.setViewportSize({ width: 900, height: 1024 });
  for (const route of ["/admin/dashboard", "/admin/customers", "/admin/customers/C1002", "/admin/analytics"]) {
    await page.goto(route);
    await expect(page.locator("main h1")).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
  }
  await page.screenshot({ path: testInfo.outputPath("admin-analytics-tablet.png"), fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/admin/dashboard");
  await expect(page.getByRole("heading", { name: "Dashboard", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Open admin navigation" }).click();
  await page.getByRole("navigation", { name: "Internal banking navigation" }).getByRole("link", { name: "Customers", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Customers", exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
  await page.screenshot({ path: testInfo.outputPath("admin-customers-mobile.png"), fullPage: true });
  expect(errors).toEqual([]);
});
