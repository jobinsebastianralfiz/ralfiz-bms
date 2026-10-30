import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type ApiError } from "./api";
import { notify } from "./components/Toaster";
import { refreshLists } from "./notes";
import type { Note, TemplateCategory, TemplateSummary } from "./types";

export const CATEGORY_LABELS: Record<TemplateCategory, string> = {
  resume: "Resumes & CVs",
  business: "Business",
  letters: "Letters",
  personal: "Personal",
  education: "Education",
};

export function useTemplates() {
  return useQuery({ queryKey: ["templates"], queryFn: () => api<TemplateSummary[]>("/templates/"), staleTime: 5 * 60_000 });
}

/** Creates a note from a template and opens it. */
export function useUseTemplate() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api<Note>(`/templates/${id}/use/`, { method: "POST" }),
    onSuccess: (note) => {
      queryClient.setQueryData(["note", note.id], note);
      refreshLists(queryClient);
      navigate(`/n/${note.id}`);
    },
    onError: (e) => {
      notify((e as ApiError).message);
    },
  });
}
