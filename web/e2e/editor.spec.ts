import { expect, test } from "@playwright/test";
import { expectNoAxeViolations, openSample } from "./helpers";

test("landing and site pages pass axe", async ({ page }) => {
  for (const path of ["/", "/terms", "/privacy", "/copyright", "/account"]) {
    await page.goto(path);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expectNoAxeViolations(page);
  }
});

test("upload, edit, reorder and add a terms page", async ({ page }) => {
  await openSample(page);
  const firstPage = page.getByRole("region", { name: "Page 1" });
  await expect(page.getByText("Column 'Q2 visits' mixes numbers and text")).toBeVisible();
  await expectNoAxeViolations(page);

  await firstPage.getByRole("button", { name: /^Field teams visited/ }).click();
  const editor = firstPage.getByRole("textbox", { name: "Edit paragraph" });
  await editor.fill("Teams covered every site on the list.");
  await editor.blur();
  await expect(firstPage.getByRole("button", { name: "Teams covered every site on the list." })).toBeVisible();

  const handle = firstPage.getByRole("button", { name: "Move paragraph block" }).first();
  await handle.focus();
  for (const key of ["Space", "ArrowUp", "ArrowUp", "Space"]) {
    await page.keyboard.press(key);
    await page.waitForTimeout(150);
  }
  const cards = firstPage.getByRole("article");
  await expect(cards.nth(0)).toHaveAccessibleName("Paragraph");

  await page.getByRole("button", { name: "Add page" }).click();
  await page.getByLabel("Company name").fill("Northwind Ltd");
  await page.getByLabel("Contact email").fill("legal@example.com");
  await page.getByLabel("Jurisdiction").fill("Ontario");
  await page.getByRole("button", { name: "Insert page" }).click();
  const terms = page.getByRole("region", { name: "Page 3 · Terms of Service" });
  await expect(terms.getByText("Template text. Not legal advice. Review before publishing.")).toBeVisible();

  await page.reload();
  await expect(page.getByRole("button", { name: "Teams covered every site on the list." })).toBeVisible();
  await expect(page.getByRole("region", { name: "Page 3 · Terms of Service" })).toBeVisible();
});

test("delete and undo restore a block, even after a reload", async ({ page }) => {
  await openSample(page);
  const second = page.getByRole("region", { name: "Page 2" });
  await second.getByRole("article", { name: "Paragraph" }).getByRole("button", { name: "Delete" }).click();
  await expect(second.getByText("Figures are counted")).toHaveCount(0);

  await page.reload();
  await expect(second.getByText("Figures are counted")).toHaveCount(0);
  await page.getByRole("button", { name: "Undo", exact: true }).click();
  await expect(second.getByText("Figures are counted")).toBeVisible();
});

test("export explains offline mode instead of failing silently", async ({ page }) => {
  await openSample(page);
  await page.getByRole("button", { name: "Export PDF" }).click();
  await expect(page.getByRole("alert")).toContainText("PDF export needs Adobe credentials");
});
