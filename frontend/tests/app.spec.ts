import { expect, test } from "@playwright/test";

const tinyPng = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y2hXWQAAAAASUVORK5CYII=",
  "base64"
);

test("dashboard query and history flow renders", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /Move from plan selection to a confident planning brief/i })).toBeVisible();
  await expect(page.getByText("Provider Optional")).toBeVisible();
  await expect(page.getByText("Scraper Unvalidated")).toBeVisible();
  await expect(page.locator(".hero-metrics .stat-tile").filter({ hasText: "Vector DB" }).getByText("Healthy")).toBeVisible();
  await page.locator(".workspace-search .list-card--button").first().click();
  await expect(page.getByText("Selected project", { exact: true })).toBeVisible();
  await expect(page.getByText("Shareable brief")).toBeVisible();
  await page.getByRole("button", { name: "Ask about this project" }).click();
  await expect(page.getByText("Relevant source regulations")).toBeVisible();
});

test("workspace shell stays usable on a mobile viewport", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 2, name: /Move the current project forward with less context switching/i })).toBeVisible();
  await expect(page.getByText("Current project", { exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: /Operations Runtime health/i })).toBeVisible();
  await expect(page.getByRole("button", { name: "Ask about this project" })).toBeVisible();
});

test("workspace supports explicit live iPlan search mode", async ({ page }) => {
  await page.route("**/api/plans/search**", async (route) => {
    await route.fulfill({
      json: {
        plans: [
          {
            plan: {
              id: "LIVE-101",
              name: "Live Test Plan",
              location: "Tel Aviv",
              region: "Tel Aviv District",
              status: "approved",
              zone_type: "residential",
              plan_type: "local",
              document_url: "https://example.com/live-plan"
            },
            vision_analysis: null,
            image_bytes: null
          }
        ],
        total_found: 1,
        query: {
          plan_id: null,
          location: "Tel Aviv",
          keyword: null,
          status: null,
          include_vision_analysis: false,
          max_results: 8
        },
        execution_time_ms: 8,
        warning: "Live iPlan search is currently degraded. Upstream requests failed, so results may be empty or incomplete.",
        warning_code: "live_search_unavailable"
      }
    });
  });

  await page.goto("/");
  await page.getByRole("button", { name: "Live iPlan" }).click();
  await expect(page.getByText("Live search is explicit and bounded")).toBeVisible();
  await expect(page.getByText("Live iPlan search is degraded")).toBeVisible();
  await expect(page.getByText(/results may be empty or incomplete/i)).toBeVisible();
  await page.getByPlaceholder("City / municipality").fill("Tel Aviv");
  await expect(page.getByRole("button", { name: /LIVE-101/i })).toBeVisible();
  await page.getByRole("button", { name: /LIVE-101/i }).click();
  await expect(page.getByText("Selected from live iPlan")).toBeVisible();
});

test("map workspace loads plan cards", async ({ page }) => {
  await page.goto("/map");
  await expect(page.getByRole("heading", { level: 2, name: /Inspect the site, geometry, and evidence in one place/i })).toBeVisible();
  await expect(page.getByRole("heading", { level: 4, name: "Selected site on the planning canvas" })).toBeVisible();
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
  await expect(
    page.getByText(/Vision analysis is unavailable|Upload analysis failed|Description/).first()
  ).toBeVisible();
});

test("data ops supports vector search and regulation authoring", async ({ page }) => {
  let overviewCalls = 0;
  await page.route("**/api/health", async (route) => {
    await route.fulfill({
      json: {
        status: "degraded",
        provider: {
          configured: false,
          base_url: "http://localhost",
          text: { healthy: false, detail: "Mock provider blocked" },
          vision: { healthy: false, detail: "Mock vision blocked" }
        },
        scraping: {
          available: true,
          status: overviewCalls > 0 ? "ready" : "unvalidated",
          runtime_ready: overviewCalls > 0,
          detail: overviewCalls > 0
            ? "Bounded probe succeeded."
            : "Run Validate scraper to perform a bounded live probe."
        }
      }
    });
  });
  await page.route("**/api/operations/overview", async (route) => {
    overviewCalls += 1;
    const ready = overviewCalls > 1;
    await route.fulfill({
      json: {
        provider: {
          configured: false,
          base_url: "http://localhost",
          text: { healthy: false, detail: "Mock provider blocked" }
        },
        scraper: {
          available: true,
          status: ready ? "ready" : "unvalidated",
          runtime_ready: ready,
          detail: ready
            ? "Bounded probe succeeded."
            : "Run Validate scraper to perform a bounded live probe.",
          last_probe_at: ready ? "2026-03-11T10:00:00+00:00" : null,
          last_probe_duration_ms: ready ? 1234 : null
        },
        data_store: { total_plans: 1, by_district: {}, by_city: {}, by_status: {}, metadata: {} },
        vector_db: { status: "healthy", health: "healthy" },
        inventory: { total_plans: 1, districts: 1, cities: 1, statuses: 1 },
        freshness: {
          source: "Mock",
          endpoint: "Mock endpoint",
          probe_status: ready ? "ready" : "unvalidated",
          probe_detail: ready ? "Bounded probe succeeded." : "Run Validate scraper to perform a bounded live probe.",
          last_probe_at: ready ? "2026-03-11T10:00:00+00:00" : null,
          last_probe_duration_ms: ready ? 1234 : null
        },
        recommended_actions: [ready ? "Runtime looks healthy." : "Validate the scraper path before running a bounded data refresh."]
      }
    });
  });
  await page.route("**/api/data/fetcher-health**", async (route) => {
    await route.fulfill({
      json: {
        available: true,
        status: "ready",
        runtime_ready: true,
        detail: "Bounded probe succeeded.",
        last_probe_at: "2026-03-11T10:00:00+00:00",
        last_probe_duration_ms: 1234,
        last_probe_count: 1,
        count: 1,
        metadata: {}
      }
    });
  });

  await page.goto("/data");
  await expect(page.getByRole("heading", { level: 2, name: /Keep data, provider health, and regulations trustworthy/i })).toBeVisible();
  await expect(page.getByText("Scraper has not been validated")).toBeVisible();
  await expect(
    page.locator(".operations-data .detail-item").filter({ hasText: "Probe result" }).getByText("Unvalidated")
  ).toBeVisible();
  await page.getByRole("button", { name: "Validate scraper" }).click();
  await expect(page.getByText("Scraper probe is ready")).toBeVisible();
  await page.getByRole("textbox").first().fill("parking");
  await page.getByRole("button", { name: "Search vector DB" }).click();
  await expect(page.getByText(/parking/i).first()).toBeVisible();

  await page.getByPlaceholder("Title").fill("Playwright Regulation");
  await page.getByPlaceholder("Content").fill("Regulation added through browser automation.");
  await page.getByRole("button", { name: "Add regulation" }).click();
  await expect(page.getByPlaceholder("Title")).toHaveValue("");
});
