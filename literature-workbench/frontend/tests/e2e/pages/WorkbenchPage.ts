import { expect, type Locator, type Page } from "@playwright/test";

export class WorkbenchPage {
  readonly page: Page;
  readonly title: Locator;
  readonly brief: Locator;
  readonly runButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.title = page.getByLabel("Project title");
    this.brief = page.getByLabel("Research brief");
    this.runButton = page.getByRole("button", { name: "Create and run fixture" });
  }

  async open() {
    await this.page.goto("/");
    await expect(this.page.getByRole("heading", { name: "Frame the inquiry." })).toBeVisible();
  }

  async createAndRun(title: string, brief: string) {
    await this.title.fill(title);
    await this.brief.fill(brief);
    await this.runButton.click();
    await expect(this.page.getByRole("tab", { name: "Corpus" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    await expect(this.page.getByText("5 papers", { exact: true })).toBeVisible();
  }

  async openReview() {
    await this.page.getByRole("tab", { name: "Review" }).click();
    await expect(this.page.getByRole("heading", { name: "Read through the evidence." })).toBeVisible();
  }

  claim(text: string) {
    return this.page.getByRole("button", { name: text, exact: true });
  }
}
