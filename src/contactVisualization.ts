export type ContactPatchInput = {
  geometric_contact: boolean;
  contact_input_active: boolean;
  contact_event: "none" | "enter" | "stay" | "exit";
  contact_patch_polygon_um: [number, number, number][];
  contact_patch_area_um2: number | null;
};

export type ContactPatchDecision = {
  render: boolean;
  reason: "active_engine_polygon" | "contact_inactive" | "area_unavailable" | "invalid_polygon";
};

/**
 * Decide whether the renderer may display a contact surface.
 *
 * There is deliberately no fallback ring or guessed radius. The external body
 * itself shows where a point contact occurs; a filled patch is permitted only
 * when the engine supplies a finite polygon and area for the current contact.
 */
export function contactPatchDecision(input: ContactPatchInput): ContactPatchDecision {
  if (!input.geometric_contact || !input.contact_input_active || input.contact_event === "none" || input.contact_event === "exit") {
    return { render: false, reason: "contact_inactive" };
  }
  if (input.contact_patch_area_um2 === null || !Number.isFinite(input.contact_patch_area_um2) || input.contact_patch_area_um2 <= 0) {
    return { render: false, reason: "area_unavailable" };
  }
  if (
    input.contact_patch_polygon_um.length < 3 ||
    input.contact_patch_polygon_um.some((point) => point.length !== 3 || point.some((coordinate) => !Number.isFinite(coordinate)))
  ) {
    return { render: false, reason: "invalid_polygon" };
  }
  return { render: true, reason: "active_engine_polygon" };
}
