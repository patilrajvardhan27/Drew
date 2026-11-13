import { expect, test } from "@playwright/test";
import { expectNoAxeViolations, openSample, register } from "./helpers";

test("split a paragraph at the cursor, then merge it back", async ({ page }) => {
  await openSample(page);
  const first = page.getByRole("region", { name: "Page 1" });

  await first.getByRole("button", { name: /^Field teams visited/ }).click();
  const editor = first.getByRole("textbox", { name: "Edit paragraph" });
  await editor.evaluate((el: HTMLTextAreaElement) => {
    const at = el.value.indexOf("Response");
    el.setSelectionRange(at, at);
  });
  await first.getByRole("button", { name: "Split at cursor" }).click();

  await expect(first.getByRole("button", { name: /^Field teams visited .* open requests\.$/ })).toBeVisible();
  const tail = first.getByRole("button", { name: /^Response times improved/ });
  await expect(tail).toBeVisible();

  const tailCard = first.getByRole("article").filter({ hasText: "Response times improved" });
  await tailCard.getByRole("button", { name: "Merge up" }).click();
  await expect(first.getByRole("button", { name: /^Field teams visited .* except the coast\.$/ })).toBeVisible();
});

test("keyboard shortcut undoes the last change", async ({ page }) => {
  await openSample(page);
  const second = page.getByRole("region", { name: "Page 2" });
  await second.getByRole("article", { name: "Paragraph" }).getByRole("button", { name: "Delete" }).click();
  await expect(second.getByText("Figures are counted")).toHaveCount(0);

  await page.locator("body").click({ position: { x: 5, y: 5 } });
  await page.keyboard.press("ControlOrMeta+z");
  await expect(second.getByText("Figures are counted")).toBeVisible();
});

test("original pages show beside the blocks", async ({ page }) => {
  await openSample(page);
  await page.getByRole("button", { name: "Show original" }).click();

  const image = page.getByRole("img", { name: "Original page 1 of the uploaded PDF" });
  await expect(image).toBeVisible();
  expect(await image.evaluate((img: HTMLImageElement) => img.naturalWidth)).toBeGreaterThan(500);
  await expectNoAxeViolations(page);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(
    page.viewportSize()!.width,
  );
});

test("a signed-in upload is kept and listed, and signing out hides it", async ({ page }) => {
  await register(page);
  await openSample(page);
  await expect(page.getByText("Saved to your account.")).toBeVisible();
  const url = page.url();

  await page.getByRole("link", { name: "Your documents" }).click();
  await expect(page.getByRole("link", { name: "northwind-field-report.pdf" })).toBeVisible();
  await expectNoAxeViolations(page);

  await page.getByRole("button", { name: "Sign out" }).click();
  await page.goto(url);
  await expect(page.getByText("Document not found")).toBeVisible();
});

test("an anonymous document can be kept after signing in", async ({ page }) => {
  await openSample(page);
  const url = page.url();
  await page.getByRole("link", { name: "Sign in to keep it" }).click();
  await page.getByRole("button", { name: "Create an account instead" }).click();
  await page.getByLabel("Email").fill(`keep-${Date.now()}@example.com`);
  await page.getByLabel(/^Password/).fill("a long enough password");
  await page.getByRole("button", { name: "Create account" }).click();

  await expect(page).toHaveURL(url);
  await page.getByRole("button", { name: "Keep it in my account" }).click();
  await expect(page.getByText("Saved to your account.")).toBeVisible();
});

test("an Express link is created for the add-on", async ({ page }) => {
  await openSample(page);
  await page.getByRole("button", { name: "Create Express link" }).click();

  const link = page.getByLabel("Express link");
  await expect(link).toHaveValue(/\/api\/express\/[a-f0-9]+\?expires=\d+&signature=[a-f0-9]{64}$/);
});
