import { expect, test, type Page } from "@playwright/test";
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

async function waitForRender(page: Page): Promise<void> {
  const canvas = page.locator('[data-role="viewport"] canvas').first();
  await expect(canvas).toBeVisible();
  await expect.poll(async () => {
    const box = await canvas.boundingBox();
    return box ? Math.min(box.width, box.height) : 0;
  }).toBeGreaterThan(240);
  await expect.poll(async () => (
    page.locator('[data-role="division-gate"]').textContent()
  )).not.toContain("loading");
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
      const firstFrame = await canvas.screenshot();
      await page.waitForTimeout(650);
      const secondFrame = await canvas.screenshot();
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
});
