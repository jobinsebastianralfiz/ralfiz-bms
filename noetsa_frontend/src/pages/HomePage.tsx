import { Link } from "react-router-dom";
import { ArrowRight, FileText, LayoutTemplate, Shapes } from "lucide-react";
import { useAuth } from "../auth";
import { NoteCard } from "../components/NoteCard";
import { useCreateNote, useNoteList } from "../notes";
import { CATEGORY_LABELS, useTemplates, useUseTemplate } from "../templates";

const STARTERS = ["simple-resume", "meeting-notes", "simple-invoice", "weekly-planner"];

function greeting() {
  const hour = new Date().getHours();
  return hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";
}

export function HomePage() {
  const { me } = useAuth();
  const create = useCreateNote();
  const recent = useNoteList({ limit: 12 });
  const notes = recent.data?.pages[0]?.results ?? [];
  const templates = useTemplates();
  const useTemplate = useUseTemplate();
  const starters = STARTERS.flatMap((slug) => templates.data?.filter((t) => t.slug === slug) ?? []);
  const firstName = (me?.user.full_name || "").split(" ")[0];

  return (
    <div className="page home-page">
      <header className="home-head">
        <h1>{greeting()}{firstName ? `, ${firstName}` : ""}</h1>
        <p className="muted">What would you like to work on?</p>
      </header>

      <div className="quick-grid">
        <button className="quick-tile" onClick={() => create.mutate({ kind: "doc" })} disabled={create.isPending}>
          <span className="quick-icon tone-indigo"><FileText size={20} /></span>
          <span><strong>New note</strong><small>Write with rich text, tables and images</small></span>
        </button>
        <button className="quick-tile" onClick={() => create.mutate({ kind: "board" })} disabled={create.isPending}>
          <span className="quick-icon tone-teal"><Shapes size={20} /></span>
          <span><strong>New board</strong><small>Whiteboard, flowcharts and diagrams</small></span>
        </button>
        <Link to="/templates" className="quick-tile">
          <span className="quick-icon tone-amber"><LayoutTemplate size={20} /></span>
          <span><strong>Templates</strong><small>Resumes, invoices, letters and plans</small></span>
        </Link>
      </div>

      <section className="home-section">
        <div className="section-head">
          <h2>Recent</h2>
          {notes.length > 0 && <Link to="/docs" className="section-link">View all <ArrowRight size={14} /></Link>}
        </div>
        {recent.isLoading && <div className="spinner" />}
        {!recent.isLoading && notes.length === 0 && (
          <div className="empty-panel">
            <FileText size={22} />
            <p><strong>Nothing here yet.</strong> Create your first note or board above, or start from a template below.</p>
          </div>
        )}
        <div className="card-grid">
          {notes.map((n) => <NoteCard key={n.id} note={n} />)}
        </div>
      </section>

      {starters.length > 0 && (
        <section className="home-section">
          <div className="section-head">
            <h2>Start from a template</h2>
            <Link to="/templates" className="section-link">All templates <ArrowRight size={14} /></Link>
          </div>
          <div className="starter-grid">
            {starters.map((t) => (
              <button key={t.id} className="starter-card" onClick={() => useTemplate.mutate(t.id)} disabled={useTemplate.isPending}>
                <span className="starter-sheet" aria-hidden="true">
                  <b>{t.name}</b>
                  <span>{t.preview}</span>
                </span>
                <span className="starter-name">{t.name}</span>
                <small className="muted">{CATEGORY_LABELS[t.category]}</small>
              </button>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
