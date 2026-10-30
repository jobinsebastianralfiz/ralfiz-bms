import { useInfiniteQuery, useMutation, useQuery, useQueryClient, type InfiniteData, type QueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "./api";
import type { Folder, Note, NoteKind, NoteSummary, Page } from "./types";

export type ListQuery = {
  kind?: NoteKind;
  folder?: string;
  pinned?: boolean;
  trash?: boolean;
  q?: string;
  /** Page size; the home page only needs a few. */
  limit?: number;
};

export function useNoteList(query: ListQuery = {}) {
  const limit = query.limit ?? 50;
  return useInfiniteQuery({
    queryKey: ["notes", query],
    initialPageParam: 0,
    queryFn: ({ pageParam }) => {
      const params = new URLSearchParams({ limit: String(limit), offset: String(pageParam) });
      if (query.kind) params.set("kind", query.kind);
      if (query.folder) params.set("folder", query.folder);
      if (query.pinned) params.set("pinned", "1");
      if (query.trash) params.set("trash", "1");
      if (query.q) params.set("q", query.q);
      return api<Page<NoteSummary>>(`/notes/?${params}`);
    },
    getNextPageParam: (last, pages) => (last.next ? pages.length * limit : undefined),
  });
}

/** Creates a note or board and opens it. */
export function useCreateNote() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  return useMutation({
    mutationFn: (body: { kind: NoteKind; folder?: string | null }) => api<Note>("/notes/", { method: "POST", body }),
    onSuccess: (note) => {
      queryClient.setQueryData(["note", note.id], note);
      refreshLists(queryClient);
      navigate(`/n/${note.id}`);
    },
  });
}

/** Pin, unpin or move a note without touching its content or version. */
export function useUpdateNoteMeta() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...body }: { id: string; pinned?: boolean; folder?: string | null }) =>
      api<Note>(`/notes/${id}/`, { method: "PATCH", body }),
    onSuccess: (saved) => {
      queryClient.setQueryData<Note>(["note", saved.id], (old) => old && { ...old, pinned: saved.pinned, folder: saved.folder });
      refreshLists(queryClient);
    },
  });
}

export function useFolders() {
  return useQuery({ queryKey: ["folders"], queryFn: () => api<Folder[]>("/folders/"), staleTime: 60_000 });
}

/** Update a note in every cached list without refetching (used after each auto-save). */
export function patchNoteInLists(queryClient: QueryClient, note: Note) {
  queryClient.setQueriesData<InfiniteData<Page<NoteSummary>>>({ queryKey: ["notes"] }, (data) =>
    data && {
      ...data,
      pages: data.pages.map((page) => ({
        ...page,
        results: page.results.map((n) => (n.id === note.id ? { ...n, ...summaryOf(note) } : n)),
      })),
    },
  );
}

function summaryOf(note: Note): NoteSummary {
  const { content: _content, page_settings: _pageSettings, ...summary } = note;
  return summary;
}

export function refreshLists(queryClient: QueryClient) {
  return queryClient.invalidateQueries({ queryKey: ["notes"] });
}

export function noteTitle(n: Pick<NoteSummary, "title" | "kind">) {
  return n.title || (n.kind === "board" ? "Untitled board" : "Untitled");
}

export function timeAgo(iso: string) {
  const seconds = Math.round((Date.now() - new Date(iso).getTime()) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.round(hours / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(iso).toLocaleDateString();
}

export function formatBytes(bytes: number) {
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  return `${(bytes / 1024 / 1024 / 1024).toFixed(1)} GB`;
}
