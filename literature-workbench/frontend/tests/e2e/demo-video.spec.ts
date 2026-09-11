import { copyFileSync } from "node:fs";

import { expect, test, type Page } from "@playwright/test";

import { WorkbenchPage } from "./pages/WorkbenchPage";

const recording = !process.env.DEMO_REHEARSE;
const output = "/Users/davidgoh/LocalFiles/2025-26-Ongoing/citation-networks/literature-workbench-demo-v2.webm";

test.use({
  video: recording ? "on" : "off",
  viewport: { width: 1280, height: 720 },
});

async function injectOverlays(page: Page) {
  await page.evaluate(() => {
    if (!document.getElementById("demo-cursor")) {
      const cursor = document.createElement("div");
      cursor.id = "demo-cursor";
      cursor.innerHTML = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M5 3L19 12L12 13L9 20L5 3Z" fill="white" stroke="black" stroke-width="1.5" stroke-linejoin="round"/></svg>`;
      cursor.style.cssText = "position:fixed;z-index:999999;pointer-events:none;width:24px;height:24px;transition:left .1s,top .1s;filter:drop-shadow(1px 1px 2px rgba(0,0,0,.3));";
      document.body.appendChild(cursor);
      document.addEventListener("mousemove", (event) => {
        cursor.style.left = `${event.clientX}px`;
        cursor.style.top = `${event.clientY}px`;
      });
    }
    if (!document.getElementById("demo-subtitle")) {
      const bar = document.createElement("div");
      bar.id = "demo-subtitle";
      bar.style.cssText = "position:fixed;bottom:0;left:0;right:0;z-index:999998;text-align:center;padding:12px 24px;background:rgba(0,0,0,.78);color:white;font-family:-apple-system,Segoe UI,sans-serif;font-size:16px;font-weight:500;letter-spacing:.3px;pointer-events:none;";
      document.body.appendChild(bar);
    }
  });
}

async function subtitle(page: Page, text: string, pause = 1400) {
  await page.evaluate((value: string) => {
    const bar = document.getElementById("demo-subtitle");
    if (bar) bar.textContent = value;
  }, text);
  await page.waitForTimeout(pause);
}

async function moveAndClick(page: Page, locator: import("@playwright/test").Locator, label: string) {
  const element = locator.first();
  await expect(element, label).toBeVisible();
  await element.scrollIntoViewIfNeeded();
  const box = await element.boundingBox();
  if (!box) throw new Error(`No bounding box for ${label}`);
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2, { steps: 10 });
  await page.waitForTimeout(450);
  await element.click();
  await page.waitForTimeout(1200);
}

async function pan(page: Page, selector: string, count = 5) {
  const elements = await page.locator(selector).all();
  for (const element of elements.slice(0, count)) {
    const box = await element.boundingBox();
    if (box && box.y < 680) {
      await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2, { steps: 8 });
      await page.waitForTimeout(500);
    }
  }
}

test("records a researcher-facing literature review walkthrough", async ({ page }) => {
  test.setTimeout(120_000);
  const video = page.video();
  const workbench = new WorkbenchPage(page);

  await workbench.open();
  await injectOverlays(page);
  await subtitle(page, "A review engine for researchers in any field", 1800);
  await pan(page, "h1, h2, label", 6);

  await subtitle(page, "1 — Choose the coverage contract", 1100);
  await workbench.title.fill("Persistent-agent memory systems");
  await workbench.brief.fill("How do memory systems help language agents retain useful experience over long tasks?");
  const reviewMode = page.locator("select").first();
  await reviewMode.scrollIntoViewIfNeeded();
  await page.mouse.wheel(0, 420);
  await page.waitForTimeout(800);
  await reviewMode.selectOption("comprehensive");
  await page.waitForTimeout(900);
  await subtitle(page, "A comprehensive survey searches broadly and records why it stopped", 1600);

  await moveAndClick(page, page.getByRole("button", { name: "Preview scope" }), "preview scope");
  await expect(page.getByRole("region", { name: "Scope preview" })).toBeVisible();
  await pan(page, '[aria-label="Scope preview"] strong, [aria-label="Scope preview"] li', 5);
  await subtitle(page, "Before searching: see the planned sources, calls, tokens, and cost", 1800);

  await moveAndClick(page, page.getByRole("button", { name: "Create and run fixture" }), "create fixture review");
  await subtitle(page, "2 — Inspect the gathered corpus before synthesis", 1300);
  await moveAndClick(page, page.getByRole("tab", { name: "Corpus" }), "corpus tab");
  await pan(page, '[aria-label="Corpus checkpoint audit"] span, [aria-label="PRISMA flow report"] span, [aria-label="Corpus papers"] th', 8);
  await subtitle(page, "The corpus records source provenance, dates, citations, and missing text", 2000);
  await moveAndClick(page, page.getByRole("button", { name: "Approve corpus checkpoint" }), "approve corpus checkpoint");
  await expect(page.getByRole("tab", { name: "Structure" })).toHaveAttribute("aria-selected", "true");
  await moveAndClick(page, page.getByRole("tab", { name: "Structure" }), "structure tab");
  await pan(page, ".outline h2, .outline p, .evidenceMeter", 6);
  await subtitle(page, "3 — Approve an argument map before prose is written", 1700);
  await moveAndClick(page, page.getByRole("button", { name: "Approve structure checkpoint" }), "approve structure checkpoint");

  await expect(page.getByRole("tab", { name: "Review" })).toHaveAttribute("aria-selected", "true");
  await subtitle(page, "4 — Read claims with their source trail attached", 1500);
  await pan(page, '[aria-label="Generated review"] p, .inspectorTitle, .claimMeta', 6);
  const claim = page.getByRole("button", { name: /To reduce interference in unfiltered episodic stores/ });
  await moveAndClick(page, claim, "inspect synthesized claim");
  await expect(page.getByRole("complementary").getByText("Evidence inspector")).toBeVisible();
  await pan(page, '[aria-label="Evidence inspector"] h3, .quote, .claimMeta strong', 7);
  await subtitle(page, "Each highlighted claim opens the exact passages and character locations used", 2200);

  await moveAndClick(page, page.getByRole("button", { name: "Run verification" }), "run verification");
  await subtitle(page, "Verification checks that the generated review is still grounded", 1700);

  await moveAndClick(page, page.getByRole("tab", { name: "Run / Costs" }), "run and costs tab");
  await pan(page, "table th, table td", 8);
  await subtitle(page, "5 — Audit the execution ledger", 1500);
  await subtitle(page, "The result is a review you can inspect, revise, and reproduce", 2200);

  await page.close();
  if (recording && video) {
    const source = await video.path();
    copyFileSync(source, output);
    console.log(`Video saved: ${output}`);
  }
});
