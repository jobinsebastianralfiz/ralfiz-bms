import { box, browser, imagePlaceholder, link, newGroup, STICKY_COLOURS, sticky, swimlanes, text, type Skeleton, type Tone } from "./boardShapes";

/** Ready-made boards offered on an empty board. Each builds its elements around (0, 0). */
export type Starter = { id: string; name: string; description: string; build: () => Skeleton[] };

const uid = (name: string) => `${name}-${newGroup()}`;

function flowchart(): Skeleton[] {
  const [s, p1, d, p2, e, p3] = ["start", "step", "check", "work", "end", "fix"].map(uid);
  return [
    box("ellipse", 125, 0, 150, 60, { tone: "green", label: "Start", id: s }),
    box("rectangle", 120, 110, 160, 72, { tone: "blue", rounded: true, label: "Receive request", id: p1 }),
    box("diamond", 100, 227, 200, 120, { tone: "amber", label: "Approved?", id: d }),
    box("rectangle", 120, 392, 160, 72, { tone: "blue", rounded: true, label: "Do the work", id: p2 }),
    box("ellipse", 125, 514, 150, 60, { tone: "red", label: "End", id: e }),
    box("rectangle", 380, 251, 160, 72, { tone: "violet", rounded: true, label: "Ask for changes", id: p3 }),
    link(s, p1, [200, 60], [200, 110]),
    link(p1, d, [200, 182], [200, 227]),
    link(d, p2, [200, 347], [200, 392], { label: "Yes" }),
    link(p2, e, [200, 464], [200, 514]),
    link(d, p3, [300, 287], [380, 287], { label: "No" }),
    link(p3, p1, [460, 251], [280, 146], { route: "vh" }),
  ];
}

function mindMap(): Skeleton[] {
  const centre = uid("idea");
  const branches: [string, number, number, Tone, string[]][] = [
    ["Goals", 20, 40, "blue", ["Grow revenue", "Happy users"]],
    ["Ideas", 640, 40, "amber", ["New feature", "Partnerships"]],
    ["People", 0, 230, "green", []],
    ["Timeline", 660, 230, "violet", []],
    ["Research", 20, 420, "teal", ["Interviews"]],
    ["Risks", 640, 420, "red", ["Budget"]],
  ];
  const els: Skeleton[] = [box("ellipse", 310, 206, 220, 100, { tone: "indigo", label: "Central idea", fontSize: 20, id: centre })];
  for (const [name, x, y, tone, subs] of branches) {
    const id = uid("branch");
    const left = x < 310;
    els.push(box("rectangle", x, y, 170, 52, { tone, rounded: true, label: name, id }));
    els.push(link(centre, id, [left ? 310 : 530, 256], [left ? x + 170 : x, y + 26], { head: false, route: "hvh" }));
    subs.forEach((sub, i) => {
      els.push(text(left ? x : x + 30, y + 64 + i * 24, `• ${sub}`, { size: 14, color: "#495057" }));
    });
  }
  return els;
}

function orgChart(): Skeleton[] {
  const ceo = uid("ceo");
  const els: Skeleton[] = [box("rectangle", 425, 0, 170, 64, { tone: "indigo", rounded: true, label: "Alex Morgan\nCEO", fontSize: 15, id: ceo })];
  const heads = [["Sam Lee", "Engineering"], ["Priya Nair", "Marketing"], ["Chris Diaz", "Operations"]];
  heads.forEach(([name, dept], i) => {
    const head = uid("head");
    const hx = i * 350 + 85;
    els.push(box("rectangle", hx, 130, 170, 64, { tone: "violet", rounded: true, label: `${name}\nHead of ${dept}`, fontSize: 15, id: head }));
    els.push(link(ceo, head, [510, 64], [hx + 85, 130], { route: "vhv", head: false }));
    for (let j = 0; j < 2; j++) {
      const person = uid("person");
      const px = i * 350 + j * 175;
      els.push(box("rectangle", px, 260, 160, 60, { tone: "blue", rounded: true, label: `Name\n${dept}`, fontSize: 14, id: person }));
      els.push(link(head, person, [hx + 85, 194], [px + 80, 260], { route: "vhv", head: false }));
    }
  });
  return els;
}

function swimlaneProcess(): Skeleton[] {
  const laneH = 120;
  const step = (lane: number, x: number, label: string, id: string, tone: Tone = "blue") =>
    box("rectangle", x, lane * laneH + 32, 140, 56, { tone, rounded: true, label, fontSize: 15, id });
  const [order, check, confirm, pack, ship, receive] = ["order", "check", "confirm", "pack", "ship", "receive"].map(uid);
  const mid = (lane: number) => lane * laneH + 60;
  return [
    ...swimlanes(0, 0, 960, ["Customer", "Sales", "Warehouse"], laneH),
    step(0, 80, "Place order", order, "green"),
    step(1, 260, "Check stock", check),
    step(1, 440, "Confirm order", confirm),
    step(2, 440, "Pack items", pack),
    step(2, 620, "Ship", ship),
    step(0, 790, "Receive", receive, "green"),
    link(order, check, [150, 88], [260, mid(1)], { route: "vh" }),
    link(check, confirm, [400, mid(1)], [440, mid(1)]),
    link(confirm, pack, [510, 208], [510, 272]),
    link(pack, ship, [580, mid(2)], [620, mid(2)]),
    link(ship, receive, [760, mid(2)], [860, 88], { route: "hv" }),
  ];
}

function kanban(): Skeleton[] {
  const columns: [string, string, string[]][] = [
    ["To do", STICKY_COLOURS.Yellow, ["Write the brief", "Collect feedback", "Plan the launch"]],
    ["In progress", STICKY_COLOURS.Blue, ["Design the homepage", "Set up analytics"]],
    ["Done", STICKY_COLOURS.Green, ["Kick-off meeting"]],
  ];
  const els: Skeleton[] = [];
  columns.forEach(([title, fill, cards], i) => {
    const x = i * 290;
    const g = newGroup();
    els.push(box("rectangle", x, 0, 260, 520, { tone: "grey", rounded: true, group: g }));
    els.push(text(x + 18, 16, `${title}  ${cards.length}`, { size: 18, group: g }));
    cards.forEach((card, j) => els.push(sticky(x + 18, 60 + j * 104, fill, card, 224, 88)));
  });
  return els;
}

function wireframe(): Skeleton[] {
  const els: Skeleton[] = [
    ...browser(0, 0, 900, 600),
    text(32, 54, "Logo", { size: 20 }),
    text(560, 58, "Features     Pricing     About", { size: 15, color: "#495057" }),
    box("rectangle", 780, 50, 96, 36, { tone: "indigo", rounded: true, label: "Sign up", fontSize: 14 }),
    text(60, 140, "Your headline here", { size: 36 }),
    text(60, 196, "One or two sentences that explain what you offer\nand why it matters to the visitor.", { size: 16, color: "#495057" }),
    box("rectangle", 60, 262, 150, 44, { tone: "indigo", rounded: true, label: "Get started", fontSize: 15 }),
    box("rectangle", 224, 262, 130, 44, { rounded: true, label: "Learn more", fontSize: 15 }),
    ...imagePlaceholder(520, 120, 330, 210),
  ];
  for (let i = 0; i < 3; i++) {
    const x = 60 + i * 270;
    els.push(box("rectangle", x, 372, 240, 190, { rounded: true }));
    els.push(...imagePlaceholder(x + 16, 388, 208, 90));
    els.push(text(x + 16, 494, `Feature ${i + 1}`, { size: 17 }));
    els.push(text(x + 16, 522, "Short description", { size: 14, color: "#868e96" }));
  }
  return els;
}

export const STARTERS: Starter[] = [
  { id: "flowchart", name: "Flowchart", description: "Steps, a decision and a loop", build: flowchart },
  { id: "mindmap", name: "Mind map", description: "One idea branching out", build: mindMap },
  { id: "orgchart", name: "Org chart", description: "Who reports to whom", build: orgChart },
  { id: "swimlane", name: "Swimlane process", description: "Steps across teams", build: swimlaneProcess },
  { id: "kanban", name: "Kanban", description: "To do, doing, done", build: kanban },
  { id: "wireframe", name: "Website wireframe", description: "A landing page layout", build: wireframe },
];
