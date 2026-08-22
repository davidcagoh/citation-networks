import { mkdir } from "node:fs/promises";

import { expect, test } from "@playwright/test";

import { WorkbenchPage } from "./pages/WorkbenchPage";

const claim =
  "To reduce interference in unfiltered episodic stores, reflective consolidation compresses related experiences into durable summaries, trading task detail for cleaner recall.";

test("creates a fixture review and traces a synthesized claim to exact evidence", async ({ page }) => {
  const artifacts = "test-results/artifacts";
  await mkdir(artifacts, { recursive: true });

  const workbench = new WorkbenchPage(page);
  await workbench.open();
  await workbench.createAndRun(
    `E2E provenance ${Date.now()}`,
    "How do persistent-agent memory systems trade recall quality for complexity?",
  );
  await workbench.openReview();

  const evidenceResponse = page.waitForResponse(
    (response) =>
      response.url().includes("/claims/") &&
      response.url().endsWith("/evidence") &&
      response.status() === 200,
  );
  await workbench.claim(claim).click();
  await evidenceResponse;

  const inspector = page.getByRole("complementary");
  await expect(inspector.getByText("cross source synthesis", { exact: true })).toBeVisible();
  await expect(
    inspector.getByText(
      "Long-running language agents lose task context as interactions accumulate. Episodic retrieval stores compact interaction traces and recalls them by semantic similarity. On multi-session tasks, retrieval improved goal completion but occasionally surfaced stale observations.",
      { exact: true },
    ),
  ).toBeVisible();
  await expect(
    inspector.getByText(
      "Unfiltered episodic stores accumulate redundant traces and retrieval interference. Reflective consolidation clusters related experiences into durable summaries before later retrieval. Consolidation reduced interference on long-horizon planning, although summarization removed some task-specific detail.",
      { exact: true },
    ),
  ).toBeVisible();
  await expect(inspector.getByText("2", { exact: true })).toBeVisible();

  await page.screenshot({ path: `${artifacts}/review-evidence.png`, fullPage: true });
});
