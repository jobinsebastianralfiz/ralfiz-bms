/** Thin fetch wrapper for the Notes API (/notes/api/ in the Ralfiz BMS): session cookie auth,
 * CSRF header, and errors normalised to ApiError (the server always sends `detail` and `code`). */

/** Where the Django API lives. Image URLs stored in notes start with it too. */
export const API_BASE = "/notes/api";

export class ApiError extends Error {
  status: number;
  code: string;
  data: Record<string, unknown>;

  constructor(status: number, data: Record<string, unknown>) {
    super(typeof data.detail === "string" ? data.detail : "Something went wrong. Please try again.");
    this.status = status;
    this.code = typeof data.code === "string" ? data.code : "error";
    this.data = data;
  }

  /** Field-level validation messages, e.g. { name: ["…"] }. */
  get fields(): Record<string, string[]> {
    return (this.data.fields as Record<string, string[]>) ?? {};
  }
}

function csrfToken(): string {
  const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : "";
}

let csrfReady: Promise<unknown> | null = null;

/** Make sure the csrftoken cookie exists before the first unsafe request. */
function ensureCsrf() {
  if (csrfToken()) return Promise.resolve();
  csrfReady ??= fetch(`${API_BASE}/auth/csrf/`, { credentials: "same-origin" });
  return csrfReady;
}

type Options = { method?: string; body?: unknown; keepalive?: boolean };

async function send(path: string, { method = "GET", body, keepalive }: Options, accept: string): Promise<Response> {
  const headers: Record<string, string> = { Accept: accept };
  if (method !== "GET") {
    await ensureCsrf();
    headers["X-CSRFToken"] = csrfToken();
  }
  let payload: BodyInit | undefined;
  if (body instanceof FormData) {
    payload = body;
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, { method, headers, body: payload, credentials: "same-origin", keepalive });
  } catch {
    throw new ApiError(0, { detail: "You're offline or the server can't be reached.", code: "network" });
  }
  if (!res.ok) {
    throw new ApiError(res.status, await res.json().catch(() => ({})));
  }
  return res;
}

export async function api<T = unknown>(path: string, options: Options = {}): Promise<T> {
  const res = await send(path, options, "application/json");
  if (res.status === 204) return undefined as T;
  return (await res.json().catch(() => ({}))) as T;
}

/** For file responses such as PDFs; errors still arrive as JSON and become ApiError. */
export async function apiBlob(path: string, options: Options = {}): Promise<Blob> {
  const res = await send(path, options, "application/pdf, application/json");
  return res.blob();
}
