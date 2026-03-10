import { expect, test } from "@playwright/test";

const tinyPng = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y2hXWQAAAAASUVORK5CYII=",
  "base64"
);

test("dashboard query and history flow renders", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Intelligence cockpit")).toBeVisible();
  await page.getByRole("button", { name: "Run query" }).click();
  await expect(page.getByText("Answer")).toBeVisible();
  await expect(page.getByText("Session history")).toBeVisible();
});

test("map workspace loads plan cards", async ({ page }) => {
  await page.goto("/map");
  await expect(page.getByText("Geo-browse local plan data")).toBeVisible();
  await expect(page.getByText("plans matched")).toBeVisible();
});

test("analyzer renders rights metrics and upload error/result surface", async ({ page }) => {
  await page.goto("/analyzer");
  await expect(page.getByText("Program comparison and compliance")).toBeVisible();
  await expect(page.getByText("Max floors")).toBeVisible();
  await page.locator('input[type="file"]').setInputFiles({
    name: "tiny.png",
    mimeType: "image/png",
    buffer: tinyPng
  });
  await expect(
    page.getByText(/Upload a file to run OCR|Vision service is unavailable|Upload analysis failed|Description/)
  ).toBeVisible();
});

test("data ops supports vector search and regulation authoring", async ({ page }) => {
  await page.goto("/data");
  await expect(page.getByText("Local plan inventory")).toBeVisible();
  await page.getByRole("textbox").nth(1).fill("parking");
  await page.getByRole("button", { name: "Search vector DB" }).click();
  await expect(page.getByText("Parking Space Requirements").first()).toBeVisible();

  await page.getByPlaceholder("Title").fill("Playwright Regulation");
  await page.getByPlaceholder("Content").fill("Regulation added through browser automation.");
  await page.getByRole("button", { name: "Add regulation" }).click();
  await expect(page.getByPlaceholder("Title")).toHaveValue("");
});
