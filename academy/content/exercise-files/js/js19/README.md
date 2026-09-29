# js19 · The event loop in Node.js

Two experiments that make the event loop visible.

## Run

    cd javascript/js19/start
    node index.js

Node.js 22 or newer. No dependencies.

## Part 1: predict the order
Inside a timer callback the script schedules setTimeout(0), setImmediate, a promise,
queueMicrotask and process.nextTick. Write your prediction first, then run it.

## Part 2: blocking versus chunked work
A heartbeat setInterval counts ticks every 10 ms while 400,000 invoices are processed.
- runBlocking() processes everything in one go
- runChunked() (you write it) processes slices of about 5 ms and yields with setImmediate

## Acceptance criteria
- Part 1 prints the actual order: timer callback, end of callback (sync), process.nextTick,
  promise.then, queueMicrotask, setImmediate, setTimeout 0
- Blocking: heartbeat ticks 0 times
- Chunked: heartbeat ticks more than 0 times, and the invoice sums of both runs are equal
- You can explain why the chunked version takes a little longer in total but keeps the process responsive
