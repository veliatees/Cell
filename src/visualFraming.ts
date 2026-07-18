export type PerspectiveFrameInput = {
  frameRadius: number;
  cameraDistance: number;
  elevationFactor: number;
  verticalFovDegrees: number;
  aspect: number;
  margin?: number;
  minimumScale?: number;
  maximumScale?: number;
};

export function perspectiveFrameScale({
  frameRadius,
  cameraDistance,
  elevationFactor,
  verticalFovDegrees,
  aspect,
  margin = 0.82,
  minimumScale = 0.05,
  maximumScale = 1.05
}: PerspectiveFrameInput): number {
  if (![frameRadius, cameraDistance, elevationFactor, verticalFovDegrees, aspect, margin].every(Number.isFinite)) {
    throw new Error("perspective frame inputs must be finite");
  }
  if (frameRadius <= 0 || cameraDistance <= 0 || aspect <= 0 || verticalFovDegrees <= 0 || verticalFovDegrees >= 180) {
    throw new Error("perspective frame dimensions must be positive and the FOV must be below 180 degrees");
  }
  if (margin <= 0 || margin > 1 || minimumScale <= 0 || maximumScale < minimumScale) {
    throw new Error("perspective frame margins and scale bounds are invalid");
  }

  const viewDistance = cameraDistance * Math.hypot(1, elevationFactor);
  const verticalHalfExtent = viewDistance * Math.tan((verticalFovDegrees * Math.PI) / 360);
  const horizontalHalfExtent = verticalHalfExtent * aspect;
  const fittedScale = (Math.min(verticalHalfExtent, horizontalHalfExtent) * margin) / frameRadius;
  return Math.min(maximumScale, Math.max(minimumScale, fittedScale));
}
