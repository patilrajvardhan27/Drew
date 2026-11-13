import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { expect, test } from "@playwright/test";
import { expectNoAxeViolations, openSample, register } from "./helpers";

// Playwright runs from web/, and the API server it starts writes mail under the repo root.
const MAIL = join(process.cwd(), "../data/e2e-files/mail");

function resetLinkFor(email: string): string {
  const messages = readdirSync(MAIL)
    .sort()
    .reverse()
    .map((name) => readFileSync(join(MAIL, name), "utf8"));
  const message = messages.find((text) => text.startsWith(`To: ${email}\n`));
  const link = message?.match(/https?:\/\/\S+\/reset\?token=\S+/)?.[0];
  if (!link) throw new Error(`No reset email for ${email}`);
  return new URL(link).pathname + new URL(link).search;
}

test("a stale tab loads the newer version instead of overwriting it", async ({ page, context }) => {
  await openSample(page);
  const other = await context.newPage();
  await other.goto(page.url());
  await expect(other.getByRole("region", { name: "Page 2" })).toBeVisible();

  const second = page.getByRole("region", { name: "Page 2" });
  await second.getByRole("article", { name: "Paragraph" }).getByRole("button", { name: "Delete" }).click();
  await expect(second.getByText("Figures are counted")).toHaveCount(0);

  const stale = other.getByRole("region", { name: "Page 1" });
  await stale.getByRole("article").first().getByRole("button", { name: "Delete" }).click();

  await expect(other.getByRole("alert")).toContainText("changed in another tab");
  await expect(other.getByRole("region", { name: "Page 2" }).getByText("Figures are counted")).toHaveCount(0);
  await expect(stale.getByRole("button", { name: "Northwind Field Report" })).toBeVisible();
});

test("a forgotten password can be reset from the emailed link", async ({ page }) => {
  const email = await register(page);
  await page.getByRole("button", { name: "Sign out" }).click();

  await page.goto("/account");
  await page.getByRole("link", { name: "Forgot your password?" }).click();
  await expectNoAxeViolations(page);
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Send reset link" }).click();
  await expect(page.getByRole("status")).toContainText("reset link is on its way");

  await page.goto(resetLinkFor(email));
  await page.getByLabel(/^New password/).fill("my brand new passphrase");
  await expectNoAxeViolations(page);
  await page.getByRole("button", { name: "Save password" }).click();
  await expect(page.getByRole("heading", { name: "Your documents" })).toBeVisible();

  await page.getByRole("button", { name: "Sign out" }).click();
  await page.goto("/account");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel(/^Password/).fill("my brand new passphrase");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Your documents" })).toBeVisible();
});
