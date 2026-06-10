# Platform Recommendation

## Recommendation

Start with a browser-based TypeScript application using Three.js for 3D visuals,
with a path toward WebGPU compute and WebGL fallback. Use Vite for fast local
iteration.

## Why This Fits The Project

- It is lightweight enough for an Apple Silicon M1 Mac.
- It supports fast iteration on research visualizations.
- It can ship as an interactive research notebook-like app later.
- Three.js gives a strong 3D ecosystem without locking the project into a heavy
  game engine early.
- WebGPU is becoming important because it supports both 3D graphics and
  general-purpose GPU computation from the browser.

## Alternatives

### Unity

Good for a polished simulation app, editor tooling, physics packages, and
cross-platform builds. It is a serious candidate if the project grows into a
large standalone application.

Tradeoff: heavier workflow, more engine lock-in, and a larger project footprint.

### Godot

Good for open-source development and lighter native projects. Godot's Apple
Silicon direction is improving, especially around Metal support.

Tradeoff: scientific simulation tooling and ecosystem are not as deep as the web
scientific stack or Unity ecosystem.

### Unreal Engine

Excellent for cinematic visuals, but too heavy for the first research prototype
on an M1 Mac. Some advanced rendering features have Mac/Apple Silicon
limitations or caveats.

## Current Platform Notes

- Unity 6.4 officially lists macOS Ventura 13 or newer and Apple M1 or above
  for Apple Silicon-based processors.
- Unreal Engine 5.7 documentation lists Apple Silicon M2+ beta support for
  Nanite and Apple Silicon M1+ for Temporal Super Resolution.
- Godot's public development notes describe a native Metal backend for Apple
  Silicon devices and report early performance improvements over Vulkan through
  MoltenVK.
- Apple's WebGPU material describes WebGPU as useful for high-performance 3D
  graphics and general-purpose GPU computation, with mapping to Metal on Apple
  platforms.

## Decision

Use the web stack first. Revisit Unity or Godot after the first two milestones:

1. two-ion formation
2. membrane patch with transport

If the simulation needs deeper editor tooling or native packaging, migrate the
model layer without throwing away the research library.

## Sources

- Unity system requirements: https://docs.unity3d.com/Manual/system-requirements.html
- Unreal macOS development requirements: https://dev.epicgames.com/documentation/unreal-engine/macos-development-requirements-for-unreal-engine
- Godot Metal backend notes: https://godotengine.org/article/dev-snapshot-godot-4-4-dev-1/
- Apple WebGPU overview: https://developer.apple.com/videos/play/wwdc2025/236/
