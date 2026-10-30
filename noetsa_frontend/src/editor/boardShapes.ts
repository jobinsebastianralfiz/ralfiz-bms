import { FONT_FAMILY, ROUNDNESS } from "@excalidraw/excalidraw";
import type { ExcalidrawElementSkeleton } from "@excalidraw/excalidraw/data/transform";

/** Built-in shapes for the board's shape panel and the starter boards. Each shape builds fresh
 * Excalidraw skeletons at a position; `convertToExcalidrawElements` turns them into elements. */

export type Skeleton = ExcalidrawElementSkeleton;
export type ShapeDef = { id: string; name: string; keywords?: string; w: number; h: number; build: (x: number, y: number) => Skeleton[] };
export type ShapeGroup = { name: string; shapes: ShapeDef[] };

export const INK = "#1e1e1e";
const LINE = "#495057";

/** Soft fill + matching stroke pairs, taken from Excalidraw's own palette so the colour picker matches. */
export const TONES = {
  plain: { fill: "#ffffff", stroke: INK },
  blue: { fill: "#e7f5ff", stroke: "#1971c2" },
  green: { fill: "#ebfbee", stroke: "#2f9e44" },
  amber: { fill: "#fff9db", stroke: "#f08c00" },
  violet: { fill: "#f3f0ff", stroke: "#6741d9" },
  teal: { fill: "#e6fcf5", stroke: "#0c8599" },
  red: { fill: "#fff5f5", stroke: "#e03131" },
  grey: { fill: "#f8f9fa", stroke: "#868e96" },
  indigo: { fill: "#4f46e5", stroke: "#4f46e5" },
};
export type Tone = keyof typeof TONES;

export const STICKY_COLOURS = { Yellow: "#ffec99", Pink: "#ffc9c9", Green: "#b2f2bb", Blue: "#a5d8ff", Purple: "#d0bfff" };

const STYLE = { strokeWidth: 1, roughness: 0, fillStyle: "solid", opacity: 100 } as const;
export const FONT = { fontFamily: FONT_FAMILY.Nunito, fontSize: 16 } as const;
const ROUNDED = { type: ROUNDNESS.ADAPTIVE_RADIUS } as const;

/** Text is measured when elements are built, so Nunito must be loaded first or labels come out clipped.
 * Excalidraw registers the font face when it loads; this only waits for the file. */
export async function ensureBoardFont() {
  try {
    await Promise.race([document.fonts.load(`20px Nunito`), new Promise((resolve) => setTimeout(resolve, 2000))]);
  } catch {
    // Labels just measure with the fallback font.
  }
}

let counter = 0;
/** A group id unique to one insert, so two copies of a shape never join one group. */
export function newGroup() {
  counter += 1;
  return `g${Date.now().toString(36)}${counter}`;
}

type BoxOpts = { tone?: Tone; rounded?: boolean; label?: string; fontSize?: number; align?: "left" | "center"; valign?: "top" | "middle"; group?: string; id?: string; textColor?: string; dashed?: boolean; noStroke?: boolean };

export function box(type: "rectangle" | "ellipse" | "diamond", x: number, y: number, w: number, h: number, o: BoxOpts = {}): Skeleton {
  const t = TONES[o.tone ?? "plain"];
  return {
    type, x, y, width: w, height: h, ...STYLE,
    id: o.id,
    strokeColor: o.noStroke ? "transparent" : t.stroke,
    backgroundColor: t.fill,
    strokeStyle: o.dashed ? "dashed" : "solid",
    roundness: o.rounded ? ROUNDED : null,
    groupIds: o.group ? [o.group] : [],
    label: o.label === undefined ? undefined : {
      text: o.label, ...FONT, fontSize: o.fontSize ?? FONT.fontSize,
      textAlign: o.align ?? "center", verticalAlign: o.valign ?? "middle",
      strokeColor: o.textColor ?? (o.tone === "indigo" ? "#ffffff" : INK),
    },
  } as Skeleton;
}

/** A closed outline from points relative to (x, y); Excalidraw fills a line whose ends meet. */
function outline(x: number, y: number, points: [number, number][], o: { tone?: Tone; group?: string; smooth?: boolean; fill?: boolean } = {}): Skeleton {
  const t = TONES[o.tone ?? "plain"];
  const closed = [...points, points[0]];
  return {
    type: "line", x: x + points[0][0], y: y + points[0][1], ...STYLE,
    strokeColor: t.stroke,
    backgroundColor: o.fill === false ? "transparent" : t.fill,
    roundness: o.smooth ? { type: ROUNDNESS.PROPORTIONAL_RADIUS } : null,
    groupIds: o.group ? [o.group] : [],
    points: closed.map(([px, py]) => [px - points[0][0], py - points[0][1]]),
  } as Skeleton;
}

/** An open line (dividers, stick figures). Points are relative to (x, y). */
function stroke(x: number, y: number, points: [number, number][], group?: string, color = INK): Skeleton {
  return {
    type: "line", x: x + points[0][0], y: y + points[0][1], ...STYLE, strokeColor: color, backgroundColor: "transparent",
    groupIds: group ? [group] : [], points: points.map(([px, py]) => [px - points[0][0], py - points[0][1]]),
  } as Skeleton;
}

export function text(x: number, y: number, value: string, o: { size?: number; group?: string; color?: string; align?: "left" | "center"; angle?: number } = {}): Skeleton {
  return {
    type: "text", x, y, text: value, ...FONT, fontSize: o.size ?? FONT.fontSize, ...STYLE,
    strokeColor: o.color ?? INK, textAlign: o.align ?? "left", angle: o.angle ?? 0,
    groupIds: o.group ? [o.group] : [],
  } as Skeleton;
}

/** A transparent box carrying a centred, editable label: lets outline shapes have text and take arrows. */
function labelled(x: number, y: number, w: number, h: number, label: string, group: string): Skeleton {
  return { ...(box("rectangle", x, y, w, h, { label, group, noStroke: true }) as object), backgroundColor: "transparent" } as Skeleton;
}

export type Route = "straight" | "vh" | "hv" | "vhv" | "hvh";

/** A connector bound to two element ids, from point a to point b (on the shapes' edges).
 * Non-straight routes use right angles, like a diagramming tool's connectors. */
export function link(from: string, to: string, a: [number, number], b: [number, number], o: { label?: string; head?: boolean; route?: Route } = {}): Skeleton {
  const dx = b[0] - a[0];
  const dy = b[1] - a[1];
  const route = dx === 0 || dy === 0 ? "straight" : (o.route ?? "straight");
  const points: [number, number][] = {
    straight: [[0, 0], [dx, dy]],
    vh: [[0, 0], [0, dy], [dx, dy]],
    hv: [[0, 0], [dx, 0], [dx, dy]],
    vhv: [[0, 0], [0, dy / 2], [dx, dy / 2], [dx, dy]],
    hvh: [[0, 0], [dx / 2, 0], [dx / 2, dy], [dx, dy]],
  }[route] as [number, number][];
  return {
    type: "arrow", x: a[0], y: a[1], ...STYLE,
    strokeColor: LINE, backgroundColor: "transparent", roundness: null,
    points, start: { id: from }, end: { id: to },
    startArrowhead: null, endArrowhead: o.head === false ? null : "triangle",
    label: o.label ? { text: o.label, ...FONT, fontSize: 14 } : undefined,
  } as Skeleton;
}

function shape(id: string, name: string, w: number, h: number, build: ShapeDef["build"], keywords = ""): ShapeDef {
  return { id, name, w, h, build, keywords };
}

const one = (s: Skeleton) => [s];

export const SHAPE_GROUPS: ShapeGroup[] = [
  {
    name: "Flowchart",
    shapes: [
      shape("process", "Process", 160, 72, (x, y) => one(box("rectangle", x, y, 160, 72, { tone: "blue", rounded: true, label: "Process" })), "step action"),
      shape("decision", "Decision", 180, 120, (x, y) => one(box("diamond", x, y, 180, 120, { tone: "amber", label: "Decision?" })), "if condition branch"),
      shape("terminator", "Start / End", 150, 60, (x, y) => one(box("ellipse", x, y, 150, 60, { tone: "green", label: "Start" })), "begin finish stop terminal"),
      shape("data", "Data", 170, 72, (x, y) => {
        const g = newGroup();
        return [outline(x, y, [[24, 0], [170, 0], [146, 72], [0, 72]], { tone: "violet", group: g }), labelled(x + 24, y, 122, 72, "Data", g)];
      }, "input output parallelogram"),
      shape("document", "Document", 160, 86, (x, y) => {
        const g = newGroup();
        const pts: [number, number][] = [[0, 0], [160, 0], [160, 70], [120, 62], [80, 74], [40, 86], [0, 76]];
        return [outline(x, y, pts, { tone: "teal", group: g, smooth: false }), labelled(x, y, 160, 66, "Document", g)];
      }, "file report paper"),
      shape("database", "Database", 120, 110, (x, y) => database(x, y, 120, 110, "Database"), "db storage cylinder sql"),
      shape("subprocess", "Subprocess", 160, 72, (x, y) => {
        const g = newGroup();
        return [
          box("rectangle", x, y, 160, 72, { tone: "blue", label: "Subprocess", group: g }),
          stroke(x, y, [[14, 0], [14, 72]], g, TONES.blue.stroke),
          stroke(x, y, [[146, 0], [146, 72]], g, TONES.blue.stroke),
        ];
      }, "predefined process function"),
      shape("delay", "Delay", 150, 72, (x, y) => {
        const g = newGroup();
        const pts: [number, number][] = [[0, 0], [105, 0], [131, 10], [147, 36], [131, 62], [105, 72], [0, 72]];
        return [outline(x, y, pts, { tone: "red", group: g }), labelled(x, y, 130, 72, "Delay", g)];
      }, "wait"),
    ],
  },
  {
    name: "Sticky notes",
    shapes: Object.entries(STICKY_COLOURS).map(([name, fill]) =>
      shape(`sticky-${name.toLowerCase()}`, `${name} note`, 170, 150, (x, y) => [sticky(x, y, fill, "Write something…")], "sticky post-it idea brainstorm"),
    ),
  },
  {
    name: "Containers",
    shapes: [
      shape("swimlanes", "Swimlanes", 640, 330, (x, y) => swimlanes(x, y, 640, ["Lane 1", "Lane 2", "Lane 3"]), "pool lanes process bpmn"),
      shape("group-box", "Group box", 320, 220, (x, y) => {
        const g = newGroup();
        return [box("rectangle", x, y, 320, 220, { tone: "grey", rounded: true, dashed: true, group: g }), text(x + 14, y + 10, "Group", { group: g, size: 14, color: "#495057" })];
      }, "container section area boundary"),
      shape("frame", "Frame", 400, 280, (x, y) => [{ type: "frame", x, y, width: 400, height: 280, children: [], name: "Frame" } as Skeleton], "artboard slide page section"),
      shape("table", "Table", 360, 150, (x, y) => table(x, y, ["Name", "Owner", "Status"], 3), "grid rows columns"),
    ],
  },
  {
    name: "Org chart",
    shapes: [
      shape("person", "Person", 180, 72, (x, y) => one(box("rectangle", x, y, 180, 72, { tone: "violet", rounded: true, label: "Name\nRole", fontSize: 15 })), "employee member role"),
      shape("team", "Manager + 3", 560, 200, (x, y) => orgTeam(x, y), "team hierarchy reports"),
    ],
  },
  {
    name: "Network & cloud",
    shapes: [
      shape("cloud", "Cloud", 170, 110, (x, y) => {
        const g = newGroup();
        const pts: [number, number][] = [[30, 100], [6, 82], [10, 52], [34, 34], [52, 12], [86, 6], [112, 22], [140, 22], [162, 46], [160, 78], [138, 100]];
        return [outline(x, y, pts, { tone: "blue", group: g, smooth: true }), labelled(x + 22, y + 28, 124, 60, "Cloud", g)];
      }, "internet aws azure gcp"),
      shape("server", "Server", 110, 130, (x, y) => {
        const g = newGroup();
        const els: Skeleton[] = [];
        for (let i = 0; i < 3; i++) {
          els.push(box("rectangle", x, y + i * 36, 110, 32, { tone: "grey", rounded: true, group: g }));
          els.push(box("ellipse", x + 88, y + i * 36 + 12, 8, 8, { tone: "green", group: g }));
        }
        els.push(text(x + 26, y + 112, "Server", { group: g, size: 14 }));
        return els;
      }, "host machine rack backend"),
      shape("desktop", "Computer", 130, 120, (x, y) => {
        const g = newGroup();
        return [
          box("rectangle", x, y, 130, 86, { tone: "blue", rounded: true, group: g, label: "Computer", fontSize: 14 }),
          stroke(x, y, [[65, 86], [65, 104]], g, TONES.blue.stroke),
          stroke(x, y, [[35, 106], [95, 106]], g, TONES.blue.stroke),
        ];
      }, "desktop pc monitor client"),
      shape("phone", "Phone", 70, 120, (x, y) => {
        const g = newGroup();
        return [box("rectangle", x, y, 70, 120, { tone: "grey", rounded: true, group: g }), stroke(x, y, [[26, 108], [44, 108]], g, "#868e96")];
      }, "mobile device app"),
      shape("db-net", "Database", 100, 100, (x, y) => database(x, y, 100, 100, "DB"), "sql storage"),
    ],
  },
  {
    name: "UML",
    shapes: [
      shape("class", "Class", 200, 150, (x, y) => umlClass(x, y), "uml object entity"),
      shape("actor", "Actor", 60, 120, (x, y) => actor(x, y), "user person stick figure use case"),
      shape("usecase", "Use case", 170, 70, (x, y) => one(box("ellipse", x, y, 170, 70, { tone: "plain", label: "Use case" })), "uml oval"),
      shape("note", "Note", 160, 90, (x, y) => {
        const g = newGroup();
        return [
          outline(x, y, [[0, 0], [140, 0], [160, 20], [160, 90], [0, 90]], { tone: "amber", group: g }),
          stroke(x, y, [[140, 0], [140, 20], [160, 20]], g, TONES.amber.stroke),
          labelled(x, y + 10, 150, 80, "Note", g),
        ];
      }, "comment annotation"),
    ],
  },
  {
    name: "Wireframe",
    shapes: [
      shape("browser", "Browser", 480, 300, (x, y) => browser(x, y, 480, 300), "window web page site"),
      shape("button", "Button", 120, 40, (x, y) => one(box("rectangle", x, y, 120, 40, { tone: "indigo", rounded: true, label: "Button", fontSize: 15 })), "cta action"),
      shape("input", "Text field", 220, 40, (x, y) => one(box("rectangle", x, y, 220, 40, { tone: "plain", rounded: true, label: "Placeholder", align: "left", fontSize: 15, textColor: "#adb5bd" })), "input form textbox"),
      shape("image", "Image", 160, 110, (x, y) => imagePlaceholder(x, y, 160, 110), "picture photo placeholder"),
      shape("mobile", "Mobile screen", 200, 380, (x, y) => {
        const g = newGroup();
        return [
          box("rectangle", x, y, 200, 380, { tone: "plain", rounded: true, group: g }),
          stroke(x, y, [[0, 44], [200, 44]], g, "#ced4da"),
          text(x + 16, y + 12, "9:41", { group: g, size: 14 }),
          stroke(x, y, [[80, 364], [120, 364]], g, "#868e96"),
        ];
      }, "app phone screen"),
    ],
  },
  {
    name: "Basic",
    shapes: [
      shape("text", "Text", 120, 25, (x, y) => one(text(x, y, "Text", { size: 20 })), "label heading"),
      shape("rect", "Rectangle", 140, 90, (x, y) => one(box("rectangle", x, y, 140, 90)), "box square"),
      shape("rounded", "Rounded", 140, 90, (x, y) => one(box("rectangle", x, y, 140, 90, { rounded: true })), "card"),
      shape("ellipse", "Ellipse", 130, 90, (x, y) => one(box("ellipse", x, y, 130, 90)), "circle oval"),
      shape("triangle", "Triangle", 120, 100, (x, y) => one(outline(x, y, [[60, 0], [120, 100], [0, 100]])), ""),
      shape("hexagon", "Hexagon", 130, 100, (x, y) => one(outline(x, y, [[30, 0], [100, 0], [130, 50], [100, 100], [30, 100], [0, 50]])), "preparation"),
    ],
  },
];

// ---- composite shapes ------------------------------------------------------

/** Stickies use the stronger palette shade so they read as paper, not boxes. */
export function sticky(x: number, y: number, fill: string, label: string, w = 170, h = 150): Skeleton {
  return { ...(box("rectangle", x, y, w, h, { noStroke: true, label, align: "left", valign: "top", fontSize: 18 }) as object), backgroundColor: fill } as Skeleton;
}

function database(x: number, y: number, w: number, h: number, label: string): Skeleton[] {
  const g = newGroup();
  const cap = Math.round(h * 0.22);
  const t = TONES.teal;
  return [
    box("ellipse", x, y + h - cap, w, cap, { tone: "teal", group: g }),
    { ...(box("rectangle", x, y + cap / 2, w, h - cap, { tone: "teal", group: g }) as object), strokeColor: "transparent" } as Skeleton,
    stroke(x, y, [[0, cap / 2], [0, h - cap / 2]], g, t.stroke),
    stroke(x, y, [[w, cap / 2], [w, h - cap / 2]], g, t.stroke),
    box("ellipse", x, y, w, cap, { tone: "teal", group: g }),
    labelled(x, y + cap, w, h - cap * 1.5, label, g),
  ];
}

export function swimlanes(x: number, y: number, w: number, lanes: string[], laneH = 110): Skeleton[] {
  const g = newGroup();
  const els: Skeleton[] = [box("rectangle", x, y, w, laneH * lanes.length, { tone: "plain", group: g })];
  lanes.forEach((name, i) => {
    if (i > 0) els.push(stroke(x, y, [[0, i * laneH], [w, i * laneH]], g, INK));
    // Lane header: a box turned on its side, so its label is centred and reads bottom to top.
    const cx = x + 20;
    const cy = y + i * laneH + laneH / 2;
    els.push({ ...(box("rectangle", cx - laneH / 2, cy - 20, laneH, 40, { tone: "grey", group: g, label: name, fontSize: 15 }) as object), strokeColor: INK, angle: -Math.PI / 2 } as Skeleton);
  });
  return els;
}

function table(x: number, y: number, headers: string[], rows: number): Skeleton[] {
  const g = newGroup();
  const cw = 120;
  const rh = 36;
  const els: Skeleton[] = [];
  headers.forEach((hd, c) => {
    els.push(box("rectangle", x + c * cw, y, cw, rh, { tone: "grey", group: g, label: hd, fontSize: 15 }));
    for (let r = 1; r <= rows; r++) els.push(box("rectangle", x + c * cw, y + r * rh, cw, rh, { group: g, label: "", fontSize: 15 }));
  });
  return els;
}

function orgTeam(x: number, y: number): Skeleton[] {
  const boss = `boss-${newGroup()}`;
  const els: Skeleton[] = [box("rectangle", x + 190, y, 180, 64, { tone: "violet", rounded: true, label: "Manager\nRole", fontSize: 15, id: boss })];
  for (let i = 0; i < 3; i++) {
    const id = `rep-${newGroup()}`;
    const rx = x + i * 190;
    els.push(box("rectangle", rx, y + 136, 180, 64, { tone: "blue", rounded: true, label: `Name\nRole`, fontSize: 15, id }));
    els.push(link(boss, id, [x + 280, y + 64], [rx + 90, y + 136], { route: "vhv", head: false }));
  }
  return els;
}

function umlClass(x: number, y: number): Skeleton[] {
  const g = newGroup();
  return [
    box("rectangle", x, y, 200, 40, { tone: "blue", group: g, label: "ClassName", fontSize: 16 }),
    box("rectangle", x, y + 40, 200, 54, { group: g, label: "- id: int\n- name: string", align: "left", fontSize: 14 }),
    box("rectangle", x, y + 94, 200, 56, { group: g, label: "+ save(): void\n+ load(): void", align: "left", fontSize: 14 }),
  ];
}

function actor(x: number, y: number): Skeleton[] {
  const g = newGroup();
  return [
    box("ellipse", x + 18, y, 24, 24, { group: g }),
    stroke(x, y, [[30, 24], [30, 70]], g),
    stroke(x, y, [[6, 40], [54, 40]], g),
    stroke(x, y, [[8, 100], [30, 70], [52, 100]], g),
    text(x + 8, y + 104, "Actor", { group: g, size: 14 }),
  ];
}

export function browser(x: number, y: number, w: number, h: number): Skeleton[] {
  const g = newGroup();
  return [
    box("rectangle", x, y, w, h, { tone: "plain", rounded: true, group: g }),
    stroke(x, y, [[0, 34], [w, 34]], g, "#ced4da"),
    box("ellipse", x + 14, y + 12, 10, 10, { tone: "red", group: g, noStroke: true }),
    box("ellipse", x + 30, y + 12, 10, 10, { tone: "amber", group: g, noStroke: true }),
    box("ellipse", x + 46, y + 12, 10, 10, { tone: "green", group: g, noStroke: true }),
    box("rectangle", x + 72, y + 8, w - 96, 18, { tone: "grey", rounded: true, group: g, noStroke: true }),
  ].map((el, i) => (i >= 2 && i <= 4 ? ({ ...el, backgroundColor: ["#ff8787", "#ffd43b", "#69db7c"][i - 2] } as Skeleton) : el));
}

export function imagePlaceholder(x: number, y: number, w: number, h: number): Skeleton[] {
  const g = newGroup();
  return [
    box("rectangle", x, y, w, h, { tone: "grey", group: g }),
    stroke(x, y, [[0, 0], [w, h]], g, "#ced4da"),
    stroke(x, y, [[w, 0], [0, h]], g, "#ced4da"),
  ];
}
