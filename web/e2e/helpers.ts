import AxeBuilder from "@axe-core/playwright";
import { expect, type Page } from "@playwright/test";

export async function expectNoAxeViolations(page: Page) {
  const results = await new AxeBuilder({ page }).exclude("iframe").analyze();
  expect(results.violations.map((v) => `${v.id}: ${v.help}`)).toEqual([]);
}

export async function openSample(page: Page) {
  await page.goto("/");
  await page.getByRole("button", { name: "Try the sample report" }).click();
  await expect(page).toHaveURL(/\/d\/[a-f0-9]+$/);
  await expect(page.getByRole("region", { name: "Page 1" })).toBeVisible();
}

export async function register(page: Page) {
  const email = `e2e-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@example.com`;
  await page.goto("/account");
  await page.getByRole("button", { name: "Create an account instead" }).click();
  await page.getByLabel("Email").fill(email);
  await page.getByLabel(/^Password/).fill("a long enough password");
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page.getByRole("heading", { name: "Your documents" })).toBeVisible();
  return email;
}
