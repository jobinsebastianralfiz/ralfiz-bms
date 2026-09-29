// Reference only: the same Task Board in React (for example in a Vite + React project).
// Compare each part with dom/dm24/solution/app.js.
import { useEffect, useState } from 'react';

const KEY = 'ralfiz-react-tasks';
const SEED = [
  { id: 1, title: 'Send quote for the Ralfiz Store redesign', done: false },
  { id: 2, title: 'Review pull request #42', done: true },
];
const loadTasks = () => {
  try { return JSON.parse(localStorage.getItem(KEY)) ?? SEED; } catch { return SEED; }
};

function TaskItem({ task, onToggle, onDelete }) {          // vanilla: TaskItem + patchTaskItem
  return (
    <li className={task.done ? 'done' : ''}>
      <label>
        <input type="checkbox" checked={task.done} onChange={() => onToggle(task.id)} />
        <span>{task.title}</span>
      </label>
      <button className="del" type="button" aria-label={`Delete ${task.title}`} onClick={() => onDelete(task.id)}>✕</button>
    </li>
  );
}

export default function TaskBoard() {
  const [tasks, setTasks] = useState(loadTasks);            // vanilla: signal(loadTasks())
  const [filter, setFilter] = useState('all');              // vanilla: signal('all')
  const visible = tasks.filter((t) => filter === 'all' || (filter === 'done') === t.done); // computed
  const remaining = tasks.filter((t) => !t.done).length;    // computed

  useEffect(() => {                                          // vanilla: the save effect
    localStorage.setItem(KEY, JSON.stringify(tasks));
  }, [tasks]);

  function add(ev) {
    ev.preventDefault();
    const title = new FormData(ev.currentTarget).get('title').trim();
    if (title) setTasks((ts) => [...ts, { id: Date.now(), title, done: false }]);
    ev.currentTarget.reset();
  }
  const toggle = (id) => setTasks((ts) => ts.map((t) => (t.id === id ? { ...t, done: !t.done } : t)));
  const remove = (id) => setTasks((ts) => ts.filter((t) => t.id !== id));

  return (
    <main className="board">
      <header><h1>Ralfiz Task Board</h1><span className="pill">{remaining} left</span></header>
      <form className="add" onSubmit={add}>
        <input name="title" required maxLength={60} placeholder="Add a task and press Enter" aria-label="New task" />
        <button>Add</button>
      </form>
      <nav className="filters" aria-label="Filter tasks">
        {['all', 'active', 'done'].map((f) => (
          <button key={f} type="button" aria-pressed={filter === f} onClick={() => setFilter(f)}>{f}</button>
        ))}
      </nav>
      <ul className="list">
        {visible.map((t) => (                               // vanilla: keyedList(list, visible.get())
          <TaskItem key={t.id} task={t} onToggle={toggle} onDelete={remove} />
        ))}
      </ul>
      <footer>
        <button type="button" className="link" onClick={() => setTasks((ts) => ts.filter((t) => !t.done))}>
          Clear completed
        </button>
      </footer>
    </main>
  );
}
