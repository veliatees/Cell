import { expect, test, type Locator, type Page } from "@playwright/test";
import { PNG } from "pngjs";

type PixelStats = {
  width: number;
  height: number;
  meanLuma: number;
  lumaStandardDeviation: number;
  nonDarkRatio: number;
  coloredRatio: number;
  quantizedColorCount: number;
};

function summarizePixels(buffer: Buffer): PixelStats {
  const image = PNG.sync.read(buffer);
  const quantizedColors = new Set<number>();
  let lumaSum = 0;
  let lumaSquaredSum = 0;
  let nonDark = 0;
  let colored = 0;
  const pixelCount = image.width * image.height;

  for (let offset = 0; offset < image.data.length; offset += 4) {
    const red = image.data[offset];
    const green = image.data[offset + 1];
    const blue = image.data[offset + 2];
    const luma = 0.2126 * red + 0.7152 * green + 0.0722 * blue;
    lumaSum += luma;
    lumaSquaredSum += luma * luma;
    if (luma > 24) nonDark += 1;
    if (Math.max(red, green, blue) - Math.min(red, green, blue) > 18) colored += 1;
    quantizedColors.add(((red >> 4) << 8) | ((green >> 4) << 4) | (blue >> 4));
  }

  const meanLuma = lumaSum / pixelCount;
  const variance = Math.max(0, lumaSquaredSum / pixelCount - meanLuma * meanLuma);
  return {
    width: image.width,
    height: image.height,
    meanLuma,
    lumaStandardDeviation: Math.sqrt(variance),
    nonDarkRatio: nonDark / pixelCount,
    coloredRatio: colored / pixelCount,
    quantizedColorCount: quantizedColors.size
  };
}

function changedPixelRatio(firstBuffer: Buffer, secondBuffer: Buffer): number {
  const first = PNG.sync.read(firstBuffer);
  const second = PNG.sync.read(secondBuffer);
  if (first.width !== second.width || first.height !== second.height) {
    throw new Error("render comparison frames must have identical dimensions");
  }
  let changed = 0;
  const pixelCount = first.width * first.height;
  for (let offset = 0; offset < first.data.length; offset += 4) {
    const channelDelta = Math.max(
      Math.abs(first.data[offset] - second.data[offset]),
      Math.abs(first.data[offset + 1] - second.data[offset + 1]),
      Math.abs(first.data[offset + 2] - second.data[offset + 2])
    );
    if (channelDelta >= 8) changed += 1;
  }
  return changed / pixelCount;
}

async function captureStableFramePair(
  canvas: Locator,
  page: Page
): Promise<[Buffer, Buffer]> {
  for (let attempt = 0; attempt < 3; attempt += 1) {
    const first = await canvas.screenshot();
    await page.waitForTimeout(650);
    const second = await canvas.screenshot();
    const firstImage = PNG.sync.read(first);
    const secondImage = PNG.sync.read(second);
    if (
      firstImage.width === secondImage.width &&
      firstImage.height === secondImage.height
    ) {
      return [first, second];
    }
    await page.waitForTimeout(400);
  }
  throw new Error("canvas dimensions did not settle across three frame pairs");
}

async function waitForRender(page: Page): Promise<void> {
  const canvas = page.locator('[data-role="viewport"] canvas').first();
  await expect(canvas).toBeVisible();
  await expect.poll(async () => {
    const box = await canvas.boundingBox();
    return box ? Math.min(box.width, box.height) : 0;
  }, { timeout: 90_000 }).toBeGreaterThan(240);
  await expect.poll(async () => (
    page.locator('[data-role="division-gate"]').textContent()
  ), { timeout: 90_000 }).not.toContain("loading");
  await page.waitForTimeout(1_200);
}

const viewportCases = [
  { name: "desktop", width: 1280, height: 720 },
  { name: "mobile", width: 390, height: 844 }
] as const;

test.describe("hepatocyte render integrity", () => {
  for (const viewport of viewportCases) {
    test(`${viewport.name} canvas remains visible, populated and moving`, async ({ page }, testInfo) => {
      const runtimeErrors: string[] = [];
      page.on("console", (message) => {
        if (message.type() === "error") runtimeErrors.push(`console: ${message.text()}`);
      });
      page.on("pageerror", (error) => runtimeErrors.push(`page: ${error.message}`));

      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.goto("/");
      await waitForRender(page);

      const layout = await page.evaluate(() => {
        const root = document.documentElement;
        const viewportElement = document.querySelector<HTMLElement>('[data-role="viewport"]');
        const canvas = viewportElement?.querySelector<HTMLCanvasElement>("canvas");
        const canvasRect = canvas?.getBoundingClientRect();
        const viewportRect = viewportElement?.getBoundingClientRect();
        const clippedControls = Array.from(document.querySelectorAll<HTMLElement>(
          "button, select, .panel-title, .metric, .phh-profile__head"
        )).filter((element) => {
          if (element.offsetParent === null || element.clientWidth === 0) return false;
          const style = getComputedStyle(element);
          if (style.overflowX === "auto" || style.overflowX === "scroll") return false;
          return element.scrollWidth > element.clientWidth + 2;
        }).map((element) => element.textContent?.trim().slice(0, 80) ?? element.tagName);
        return {
          horizontalOverflow: root.scrollWidth > window.innerWidth + 1,
          verticalOverflow: root.scrollHeight > window.innerHeight + 1,
          verticalOverflowPolicy: getComputedStyle(document.body).overflowY,
          canvasInsideViewport: Boolean(
            canvasRect && viewportRect &&
            canvasRect.left >= viewportRect.left - 1 &&
            canvasRect.top >= viewportRect.top - 1 &&
            canvasRect.right <= viewportRect.right + 1 &&
            canvasRect.bottom <= viewportRect.bottom + 1
          ),
          clippedControls
        };
      });

      expect(layout.horizontalOverflow).toBe(false);
      if (viewport.name === "mobile") {
        expect(layout.verticalOverflow).toBe(true);
        expect(["auto", "scroll", "visible"]).toContain(layout.verticalOverflowPolicy);
      } else {
        expect(layout.verticalOverflow).toBe(false);
      }
      expect(layout.canvasInsideViewport).toBe(true);
      expect(layout.clippedControls).toEqual([]);
      expect(runtimeErrors).toEqual([]);

      const canvas = page.locator('[data-role="viewport"] canvas').first();
      const [firstFrame, secondFrame] = await captureStableFramePair(
        canvas,
        page
      );
      const pixelStats = summarizePixels(firstFrame);
      const motionRatio = changedPixelRatio(firstFrame, secondFrame);

      expect(pixelStats.width).toBeGreaterThan(300);
      expect(pixelStats.height).toBeGreaterThan(240);
      expect(pixelStats.meanLuma).toBeGreaterThan(8);
      expect(pixelStats.lumaStandardDeviation).toBeGreaterThan(12);
      expect(pixelStats.nonDarkRatio).toBeGreaterThan(0.04);
      expect(pixelStats.coloredRatio).toBeGreaterThan(0.015);
      expect(pixelStats.quantizedColorCount).toBeGreaterThan(64);
      expect(motionRatio).toBeGreaterThan(0.002);
      expect(motionRatio).toBeLessThan(0.98);

      await testInfo.attach(`${viewport.name}-canvas.png`, {
        body: firstFrame,
        contentType: "image/png"
      });
      await testInfo.attach(`${viewport.name}-pixel-diagnostics.json`, {
        body: Buffer.from(JSON.stringify({ ...pixelStats, motionRatio }, null, 2)),
        contentType: "application/json"
      });
    });
  }

  test("canonical snapshot pauses and sanitizes the browser-local fixture", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto("/");
    await waitForRender(page);

    const report = page.locator(".report-panel").first();
    await expect(report).toHaveAttribute(
      "data-python-snapshot-availability",
      "loaded"
    );
    await expect(report).toHaveAttribute(
      "data-local-fixture-execution",
      "paused_for_python_snapshot"
    );
    await expect(report.locator(".report-status")).toContainText(
      "PAUSED - Python snapshot is the state source"
    );
    await expect(report.locator(".report-rows")).toContainText(
      "Local organelle activity"
    );
    await expect(report.locator(".report-flows")).toContainText(
      "neutral topology"
    );

    const publicText = await report.innerText();
    expect(publicText).not.toMatch(/%\/h|median fate|local ETA|Cell is dying/i);
  });

  test("offscreen mobile viewport suspends and resumes the render loop", async ({ page }) => {
    const runtimeErrors: string[] = [];
    page.on("console", (message) => {
      if (message.type() === "error") runtimeErrors.push(`console: ${message.text()}`);
    });
    page.on("pageerror", (error) => runtimeErrors.push(`page: ${error.message}`));

    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/");
    await waitForRender(page);
    const root = page.locator("html");
    await expect(root).toHaveAttribute("data-cell-render-suspended", "none");

    await page.evaluate(() => {
      window.scrollTo(0, document.documentElement.scrollHeight);
    });
    await expect.poll(
      () => root.getAttribute("data-cell-render-suspended")
    ).toBe("viewport_not_intersecting");

    await page.evaluate(() => {
      window.scrollTo(0, 0);
    });
    await expect.poll(
      () => root.getAttribute("data-cell-render-suspended")
    ).toBe("none");
    expect(runtimeErrors).toEqual([]);
  });

  test("deferred scientific and protein modules activate on demand", async ({ page }, testInfo) => {
    const runtimeErrors: string[] = [];
    const loadedUrls = new Set<string>();
    page.on("console", (message) => {
      if (message.type() === "error") runtimeErrors.push(`console: ${message.text()}`);
    });
    page.on("pageerror", (error) => runtimeErrors.push(`page: ${error.message}`));
    page.on("response", (response) => {
      if (response.ok()) loadedUrls.add(new URL(response.url()).pathname);
    });

    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto("/");
    await waitForRender(page);

    await expect.poll(() => (
      [...loadedUrls].some((url) => url.includes("engineSnapshot"))
    )).toBe(true);
    await expect.poll(async () => {
      const bloomLoaded = [...loadedUrls].some((url) =>
        url.includes("UnrealBloomPass")
      );
      const quality = await page.locator("html").getAttribute(
        "data-cell-render-quality"
      );
      return bloomLoaded || quality === "balanced" || quality === "essential";
    }, { timeout: 20_000 }).toBe(true);

    await page.getByLabel("Hepatic zone", { exact: true }).selectOption("periportal");
    await page.getByLabel("Nutritional state", { exact: true }).selectOption("fed_peak");
    await page.getByLabel("Engine experiment", { exact: true }).selectOption("bsep_loss");
    await expect(page.locator("[data-role='cell-context']")).toContainText(
      "hepatocyte · periportal · fed peak"
    );
    await expect(page.locator(".report-response")).toContainText("bsep export loss");
    await expect(page.locator(".report-response")).toContainText("0.00×");

    const sceneControl = page.locator("[data-control='scene']");
    await sceneControl.selectOption("glucokinase-structure");
    await expect(sceneControl).toHaveValue(
      "glucokinase-structure"
    );
    await expect.poll(() => (
      [...loadedUrls].some((url) => url.toLowerCase().includes("pdbloader"))
    )).toBe(true);
    await expect.poll(() => (
      page.locator("html").getAttribute("data-cell-protein-scene-state")
    ), { timeout: 20_000 }).toBe("ready");

    const canvas = page.locator('[data-role="viewport"] canvas').first();
    let proteinFrame = await canvas.screenshot();
    let proteinStats = summarizePixels(proteinFrame);
    const sampledProteinStats = [proteinStats];
    // The molecule rotates continuously. Sample a short bounded window so the
    // integrity gate is not coupled to one edge-on orientation or upload frame.
    for (let sample = 0; sample < 3; sample += 1) {
      await page.waitForTimeout(250);
      const candidateFrame = await canvas.screenshot();
      const candidateStats = summarizePixels(candidateFrame);
      sampledProteinStats.push(candidateStats);
      if (candidateStats.lumaStandardDeviation > proteinStats.lumaStandardDeviation) {
        proteinFrame = candidateFrame;
        proteinStats = candidateStats;
      }
    }
    const performanceState = await page.locator("html").evaluate((element) => ({
      renderQuality: element.getAttribute("data-cell-render-quality"),
      fps: element.getAttribute("data-cell-perf-fps"),
      averageWorkMs: element.getAttribute("data-cell-perf-work-ms"),
      maximumWorkMs: element.getAttribute("data-cell-perf-max-work-ms"),
      fluidStepHz: element.getAttribute("data-cell-perf-fluid-step-hz"),
      suspended: element.getAttribute("data-cell-render-suspended"),
      stages: element.getAttribute("data-cell-perf-stages")
    }));
    await testInfo.attach("deferred-glucokinase-canvas.png", {
      body: proteinFrame,
      contentType: "image/png"
    });
    await testInfo.attach("deferred-module-diagnostics.json", {
      body: Buffer.from(JSON.stringify({
        loadedUrls: [...loadedUrls].sort(),
        performanceState,
        proteinStats,
        sampledProteinStats
      }, null, 2)),
      contentType: "application/json"
    });
    expect(proteinStats.meanLuma).toBeGreaterThan(2);
    // Balanced/essential tiers intentionally disable bloom. Keep the full-tier
    // contrast gate strict while using a bloom-free floor together with explicit
    // loader readiness, color diversity and non-dark coverage on lower tiers.
    const minimumContrast = performanceState.renderQuality === "full" ? 7.5 : 5.5;
    expect(proteinStats.lumaStandardDeviation).toBeGreaterThan(minimumContrast);
    expect(proteinStats.nonDarkRatio).toBeGreaterThan(0.005);
    expect(proteinStats.coloredRatio).toBeGreaterThan(0.01);
    expect(proteinStats.quantizedColorCount).toBeGreaterThan(64);
    expect(runtimeErrors).toEqual([]);
    const renderQuality = performanceState.renderQuality;
    expect(["full", "balanced", "essential"]).toContain(renderQuality);
    expect(performanceState.suspended).toBe("none");
  });
});
