import { lazy, StrictMode, Suspense } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Link, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ApiError } from "./api";
import { AuthProvider, RequireAuth } from "./auth";
import { AppLayout } from "./pages/AppLayout";
import { HomePage } from "./pages/HomePage";
import { LibraryPage } from "./pages/LibraryPage";
import { NotePage } from "./pages/NoteRoute";
import "@fontsource-variable/inter";
import "./styles.css";

const TemplatesPage = lazy(() => import("./pages/TemplatesPage").then((m) => ({ default: m.TemplatesPage })));
const editorFallback = <div className="center-screen"><div className="spinner" /></div>;

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Don't retry client errors such as 404; do retry network blips.
      retry: (count, error) => count < 2 && !(error instanceof ApiError && error.status >= 400 && error.status < 500),
      refetchOnWindowFocus: false,
    },
  },
});

function NotFound() {
  return (
    <div className="center-screen stack">
      <h1>Page not found</h1>
      <Link to="/" className="btn">Go to your notes</Link>
    </div>
  );
}

// The app lives at /notes/ inside the Ralfiz BMS; Django serves this page for every
// /notes/... path and the API under /notes/api/.
createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter basename="/notes">
        <AuthProvider>
          <Routes>
            <Route path="/" element={<RequireAuth><AppLayout /></RequireAuth>}>
              <Route index element={<HomePage />} />
              <Route path="docs" element={<LibraryPage key="notes" section="notes" />} />
              <Route path="boards" element={<LibraryPage key="boards" section="boards" />} />
              <Route path="folders/:id" element={<LibraryPage key="folder" section="folder" />} />
              <Route path="trash" element={<LibraryPage key="trash" section="trash" />} />
              <Route path="n/:id" element={<NotePage />} />
              <Route path="templates" element={<Suspense fallback={editorFallback}><TemplatesPage /></Suspense>} />
              <Route path="*" element={<NotFound />} />
            </Route>
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
