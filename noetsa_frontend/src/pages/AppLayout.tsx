import { useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { Menu, Search } from "lucide-react";
import { CommandPalette } from "../components/CommandPalette";
import { Sidebar } from "../components/Sidebar";
import { Toaster } from "../components/Toaster";

export function AppLayout() {
  const location = useLocation();
  // On phones the sidebar is a drawer over the page.
  const [drawer, setDrawer] = useState(false);
  const [palette, setPalette] = useState(false);

  useEffect(() => setDrawer(false), [location.pathname]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPalette((open) => !open);
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  return (
    <div className={`app ${drawer ? "drawer-open" : ""}`}>
      <Sidebar onSearch={() => setPalette(true)} />
      <div className="drawer-backdrop" onClick={() => setDrawer(false)} />

      <main className="main">
        <div className="mobile-bar">
          <button className="icon-btn" onClick={() => setDrawer(true)} aria-label="Open menu">
            <Menu size={20} />
          </button>
          <span className="mobile-brand"><span className="logo-mark" aria-hidden="true">N</span> Notes</span>
          <button className="icon-btn" onClick={() => setPalette(true)} aria-label="Search">
            <Search size={19} />
          </button>
        </div>
        <Outlet />
      </main>

      {palette && <CommandPalette onClose={() => setPalette(false)} />}
      <Toaster />
    </div>
  );
}
