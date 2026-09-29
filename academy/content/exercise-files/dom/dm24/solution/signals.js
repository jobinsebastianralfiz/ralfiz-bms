// A tiny signals library: dependency tracking at read time.
let running = null; // the effect that is currently executing

export function signal(value) {
  const subscribers = new Set();
  return {
    get() {
      if (running) subscribers.add(running);
      return value;
    },
    set(next) {
      if (Object.is(next, value)) return;
      value = next;
      [...subscribers].forEach((fn) => fn());
    },
  };
}

export function effect(fn) {
  const run = () => {
    const previous = running;
    running = run;
    try {
      fn();
    } finally {
      running = previous;
    }
  };
  run();
}

export function computed(fn) {
  const s = signal();
  effect(() => s.set(fn()));
  return { get: s.get };
}

export const ready = true;
