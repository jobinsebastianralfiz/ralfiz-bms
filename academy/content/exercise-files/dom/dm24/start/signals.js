// A tiny signals library. Finish TODO(1) and TODO(2).
let running = null; // the effect that is currently executing

export function signal(value) {
  // TODO(1): keep a Set of subscribers.
  // get(): if running is set, add it to the subscribers; return value.
  // set(next): return early when Object.is(next, value); otherwise store it and call every subscriber.
  return {
    get() { return value; },
    set(next) { value = next; },
  };
}

export function effect(fn) {
  // TODO(2): wrap fn in run(), which sets running = run while fn executes
  // (restore the previous value in finally), then call run() once.
  fn();
}

export function computed(fn) {
  // TODO(2): create a signal, keep it updated with effect(() => s.set(fn())),
  // and return only { get }.
  return { get: fn };
}

export const ready = false; // set to true when you finish
