import { lazy, Suspense, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api, ApiError } from "../api";
import type { Note } from "../types";

// TipTap and Excalidraw are both large; each loads only when a note of its kind opens.
const DocEditor = lazy(() => import("./NotePage").then((m) => ({ default: m.DocEditor })));
const BoardEditor = lazy(() => import("./BoardEditor").then((m) => ({ default: m.BoardEditor })));

export function NotePage() {
  const { id = "" } = useParams();
  // Bumped to remount the editor with server content (after resolving a conflict).
  const [generation, setGeneration] = useState(0);
  const query = useQuery({ queryKey: ["note", id], queryFn: () => api<Note>(`/notes/${id}/`) });

  // Wait for the server copy even when the note is cached: the editor keeps the version it starts
  // with, so starting from a stale cache (e.g. just after leaving the note) would end in a 409.
  if (query.isLoading || !query.isFetchedAfterMount) return <div className="center-screen"><div className="spinner" /></div>;
  if (query.isError && !query.data) {
    const err = query.error as ApiError;
    return (
      <div className="empty-main">
        <h2>{err.status === 404 ? "Note not found" : "Couldn't open this note"}</h2>
        <p className="muted">{err.status === 404 ? "It may have been deleted." : err.message}</p>
        <Link to="/" className="btn">Back to notes</Link>
      </div>
    );
  }
  const note = query.data!;
  const Editor = note.kind === "board" ? BoardEditor : DocEditor;
  return (
    <Suspense fallback={<div className="center-screen"><div className="spinner" /></div>}>
      <Editor key={`${id}:${generation}`} note={note} onReload={() => setGeneration((g) => g + 1)} />
    </Suspense>
  );
}

