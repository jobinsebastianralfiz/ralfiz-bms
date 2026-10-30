import type { JSONContent } from "@tiptap/react";

export type User = {
  id: number;
  username: string;
  email: string;
  full_name: string;
  is_staff: boolean;
};

/** GET /notes/api/auth/me/. `home_url` is the BMS dashboard, or the staff portal for interns and employees. */
export type Me = { user: User; home_url: string; home_label: string; logout_url: string };

export type NoteKind = "doc" | "board";

export type Folder = { id: string; name: string; created_at: string };

/** The BMS record a note is linked to, shown as a chip that opens its page. */
export type NoteLink = { kind: "project" | "client" | "lead"; id: string; label: string; url: string };

export type NoteSummary = {
  id: string;
  kind: NoteKind;
  title: string;
  preview: string;
  pinned: boolean;
  folder: string | null;
  version: number;
  link: NoteLink | null;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
};

export type PageSettings = {
  size: "A4" | "Letter" | "Legal";
  orientation: "portrait" | "landscape";
  /** Millimetres, 0–60. */
  margins: { top: number; right: number; bottom: number; left: number };
  header: string;
  footer: string;
  page_numbers: boolean;
  show_title: boolean;
};

export type Note = NoteSummary & { content: JSONContent | null; page_settings: PageSettings };

export type Page<T> = { count: number; next: string | null; previous: string | null; results: T[] };

export type TemplateCategory = "resume" | "business" | "letters" | "personal" | "education";

export type TemplateSummary = {
  id: string;
  /** Set on built-in templates only. */
  slug: string | null;
  name: string;
  description: string;
  category: TemplateCategory;
  premium: boolean;
  builtin: boolean;
  preview: string;
  created_at: string;
};

export type TemplateDetail = TemplateSummary & { note_title: string; content: JSONContent; page_settings: PageSettings };
