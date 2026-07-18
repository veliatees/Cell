import { describe, expect, it } from "vitest";

import { contactPatchDecision, type ContactPatchInput } from "./contactVisualization";

const validContact = (): ContactPatchInput => ({
  geometric_contact: true,
  contact_input_active: true,
  contact_event: "enter",
  contact_patch_polygon_um: [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]],
  contact_patch_area_um2: 1
});

describe("contactPatchDecision", () => {
  it("renders only an active finite polygon supplied by the engine", () => {
    expect(contactPatchDecision(validContact())).toEqual({ render: true, reason: "active_engine_polygon" });
    expect(contactPatchDecision({ ...validContact(), contact_event: "stay" }).render).toBe(true);
  });

  it("does not invent a glowing area for mixed-shape point contact", () => {
    expect(contactPatchDecision({
      ...validContact(),
      contact_patch_polygon_um: [],
      contact_patch_area_um2: null
    })).toEqual({ render: false, reason: "area_unavailable" });
  });

  it("hides exited, separated, zero-area and malformed patches", () => {
    expect(contactPatchDecision({ ...validContact(), contact_event: "exit", contact_input_active: false }).render).toBe(false);
    expect(contactPatchDecision({ ...validContact(), geometric_contact: false }).render).toBe(false);
    expect(contactPatchDecision({ ...validContact(), contact_patch_area_um2: 0 }).render).toBe(false);
    expect(contactPatchDecision({ ...validContact(), contact_patch_polygon_um: [[0, 0, 0], [1, 0, 0], [Number.NaN, 1, 0]] }).render).toBe(false);
  });
});
