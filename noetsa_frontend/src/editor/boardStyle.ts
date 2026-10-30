import { FONT_FAMILY } from "@excalidraw/excalidraw";
import type { AppState } from "@excalidraw/excalidraw/types";

/** Noetsa's default drawing style: crisp lines and a plain font, like a diagramming tool,
 * instead of Excalidraw's hand-drawn look. Users can still pick "sketchy" per shape. */
export const CLEAN_DEFAULTS: Partial<AppState> = {
  currentItemRoughness: 0,
  currentItemFontFamily: FONT_FAMILY.Nunito,
  currentItemStrokeWidth: 1,
  currentItemRoundness: "round",
  currentItemStrokeColor: "#1e1e1e",
  currentItemBackgroundColor: "transparent",
  currentItemFillStyle: "solid",
};
