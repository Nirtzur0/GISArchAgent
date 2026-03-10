import { expect, test } from "@playwright/test";

const tinyPng = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y2hXWQAAAAASUVORK5CYII=",
  "base64"
);

test("dashboard query and history flow renders", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /Start from a site or plan/i })).toBeVisible();
  await page.getByRole("button", { name: "Ask about this project" }).click();
  await expect(page.getByText("Relevant source regulations")).toBeVisible();
  await expect(page.getByText(/^Project dossier:/)).toBeVisible();
});

test("map workspace loads plan cards", async ({ page }) => {
  await page.goto("/map");
  await expect(page.getByText("Browse planning geometry with the selected project kept in focus")).toBeVisible();
  await expect(page.getByText("Selected site")).toBeVisible();
});

test("analyzer renders rights metrics and upload error/result surface", async ({ page }) => {
  await page.goto("/analyzer");
  await expect(page.getByText("Feasibility inputs")).toBeVisible();
  await expect(page.getByText("Allowed floors")).toBeVisible();
  await page.locator('input[type="file"]').setInputFiles({
    name: "tiny.png",
    mimeType: "image/png",
    buffer: tinyPng
  });
  await expect(page.getByText(/MockChat vision unavailable|Upload analysis failed|Description/).first()).toBeVisible();
});

test("data ops supports vector search and regulation authoring", async ({ page }) => {
  await page.goto("/data");
  await expect(page.getByText("Runtime dependencies and scrape validation")).toBeVisible();
  await page.getByRole("textbox").first().fill("parking");
  await page.getByRole("button", { name: "Search vector DB" }).click();
  await expect(page.getByText(/parking/i).first()).toBeVisible();

  await page.getByPlaceholder("Title").fill("Playwright Regulation");
  await page.getByPlaceholder("Content").fill("Regulation added through browser automation.");
  await page.getByRole("button", { name: "Add regulation" }).click();
  await expect(page.getByPlaceholder("Title")).toHaveValue("");
});
