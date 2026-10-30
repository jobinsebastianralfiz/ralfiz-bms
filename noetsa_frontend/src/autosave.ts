import { useCallback, useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { api, ApiError } from "./api";
import { patchNoteInLists, refreshLists } from "./notes";
import type { Note } from "./types";

const SAVE_DELAY_MS = 800;
const RETRY_DELAY_MS = 5000;

export type SaveStatus = "saved" | "unsaved" | "saving" | "offline" | "conflict";
/** `content` is TipTap JSON for docs and an Excalidraw scene for boards. */
type Patch = { title?: string; content?: unknown };

/** Debounced auto-save. Sends the version it last saw; a 409 means another tab or device saved first. */
export function useAutosave(note: Note) {
  const queryClient = useQueryClient();
  const version = useRef(note.version);
  const pending = useRef<Patch>({});
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined);
  const inFlight = useRef(false);
  // Set when a save is requested while another is in flight; it runs as soon as that one ends.
  const again = useRef(false);
  const blocked = useRef(false); // true while a conflict is unresolved
  const [status, setStatus] = useState<SaveStatus>("saved");
  const [conflict, setConflict] = useState<Note | null>(null);

  /** Resolves true when everything pending reached the server. */
  const flush = useCallback(async (): Promise<boolean> => {
    clearTimeout(timer.current);
    timer.current = undefined;
    if (inFlight.current) {
      again.current = true;
      return false;
    }
    if (blocked.current) return false;
    if (Object.keys(pending.current).length === 0) return true;
    const body = pending.current;
    pending.current = {};
    inFlight.current = true;
    setStatus("saving");
    let ok = false;
    try {
      const saved = await api<Note>(`/notes/${note.id}/`, { method: "PATCH", body: { ...body, version: version.current } });
      version.current = saved.version;
      queryClient.setQueryData(["note", note.id], saved);
      patchNoteInLists(queryClient, saved);
      setStatus(Object.keys(pending.current).length ? "unsaved" : "saved");
      ok = true;
    } catch (e) {
      pending.current = { ...body, ...pending.current };
      if (e instanceof ApiError && e.status === 409) {
        blocked.current = true;
        setConflict(e.data.note as Note);
        setStatus("conflict");
      } else {
        setStatus("offline");
        timer.current = setTimeout(() => void flush(), RETRY_DELAY_MS);
      }
    } finally {
      inFlight.current = false;
    }
    if (again.current) {
      again.current = false;
      if (ok) void flush();
    }
    return ok;
  }, [note.id, queryClient]);

  /** Save immediately (e.g. before exporting), waiting for a save already in progress. */
  const saveNow = useCallback(async () => {
    while (inFlight.current) await new Promise((resolve) => setTimeout(resolve, 50));
    return flush();
  }, [flush]);

  const schedule = useCallback(
    (patch: Patch) => {
      Object.assign(pending.current, patch);
      setStatus((s) => (s === "conflict" ? s : "unsaved"));
      if (blocked.current) return;
      clearTimeout(timer.current);
      timer.current = setTimeout(() => void flush(), SAVE_DELAY_MS);
    },
    [flush],
  );

  // Save whatever is left when leaving the note or closing the tab.
  useEffect(() => {
    const sendNow = () => {
      if (!Object.keys(pending.current).length) return;
      // Keep the saved version in the cache, or reopening the note would start from a stale one and hit a 409.
      void api<Note>(`/notes/${note.id}/`, {
        method: "PATCH",
        body: { ...pending.current, version: version.current },
        keepalive: true,
      })
        .then((saved) => {
          queryClient.setQueryData(["note", note.id], saved);
          patchNoteInLists(queryClient, saved);
        })
        .catch(() => undefined);
      pending.current = {};
    };
    const onBeforeUnload = (e: BeforeUnloadEvent) => {
      if (Object.keys(pending.current).length) {
        sendNow();
        e.preventDefault();
      }
    };
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => {
      window.removeEventListener("beforeunload", onBeforeUnload);
      clearTimeout(timer.current);
      sendNow();
      refreshLists(queryClient);
    };
  }, [note.id, queryClient]);

  /** Overwrite the other version with ours. */
  const keepMine = useCallback(() => {
    if (!conflict) return;
    version.current = conflict.version;
    blocked.current = false;
    setConflict(null);
    void flush();
  }, [conflict, flush]);

  /** Drop our unsaved edits and load the other version. */
  const discardMine = useCallback(() => {
    if (!conflict) return null;
    pending.current = {};
    queryClient.setQueryData(["note", note.id], conflict);
    return conflict;
  }, [conflict, note.id, queryClient]);

  return { status, conflict, schedule, keepMine, discardMine, saveNow };
}

