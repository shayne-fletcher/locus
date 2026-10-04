# Strip 1: Rust owns the mailbox, Python owns the loop

Seed for `images/strip-1-python-actors.png`, which opens the article. Everything below the line is the prompt; paste it whole. Panel content is maintained alongside the Monarch checkout's `strips/` and copied here.

---

Draw a comic strip for a technical article.

**Style.**
- A hand-drawn comic explainer on warm off-white paper.
- The page is a 4 × 2 grid of numbered panels under a title banner, with a one-liner box at the bottom or in the last panel.
- Thick, dark-ink rounded outlines; soft pastel fills (blue, lilac, mint, peach, rose, butter yellow); a gentle drop shadow on boxes.
- Lettering is hand-drawn and highly legible. Code identifiers are set in monospace and spelled exactly as given.
- **Recurring characters:**
  - **Rust:** a smiling orange cog with eyes.
  - **Python:** a friendly blue-and-yellow snake. When the panel says it's asleep, it sleeps with "z z z".
  - **Your actor:** a small lilac blob with a smiley face and crossed arms.
- **Recurring props:** the mpsc queue as a short stack of orange boxes; the self-pipe as a blue tube with a "0x01" byte; messages as envelopes.
- Canvas 1536 × 1024 px, landscape.
- Render each panel's title and text faithfully. Lines in *italics* are panel footnotes, set in a tinted box at the bottom of the panel. Draw the ASCII sketches as diagrams; don't copy them as text.

**Title banner:** "Rust owns the mailbox, Python owns the loop", with the two halves tinted rose and blue.

**Panels.**

**Panel 1: the cast**
```
Rust  PythonActor ──holds──▶ Py handle to _Actor ──wraps──▶ your Actor
        │                           (Python)                 (endpoints)
        └─ channel (pympsc) ─────────▶ Python's side
```
`PythonActor` (`monarch_hyperactor/src/actor.rs`) is an ordinary hyperactor actor whose handlers live in Python.

**Panel 2: spawn**
Rust unpickles `_Actor` (Monarch's wrapper, not your class) and constructs it. It creates a new asyncio event loop on a daemon thread, `monarch-actor-event-loop`, and starts `_dispatch_loop(actor, receiver, instance)` on it. Your class arrives as the first message, `__init__`: `_Actor.handle` constructs your Actor on that thread. It never leaves; messages never carry it.

**Panel 3: two loops per Python actor**
```
[Tokio task]  mailbox loop ──PendingMessage──▶ [Python thread] asyncio loop
  one msg at a time,                              _dispatch_loop: one
  never touches the GIL                           endpoint at a time
```
Both are first-in, first-out, so per-actor order holds end to end. All the Python threads in a process share one GIL.

**Panel 4: a message arrives (Rust side, no GIL)**
`Handler<PythonMessage>::handle` resolves indirect arguments, builds a plain Rust `PendingMessage` (instance, rank, span, method, pickled args, refs, response port), and `send`s it: one box onto an `mpsc` queue, then one byte down a self-pipe. Then it returns.
*Why no GIL: taking it on a Tokio worker could stall the whole proc's I/O (meta-pytorch/monarch#4938).*

**Panel 5: the wake-up**
The Python thread is asleep in the selector (kqueue/epoll), GIL released. The pipe becomes readable, the loop runs its reader callback (`os.read` one byte, `event.set()`), and `Receiver.recv()` resumes.
*The byte is only a hint; the queue is the truth.*

**Panel 6: the conversion (Rust code, on Python's thread)**
`recv` calls `try_recv`. It's declared in Python but implemented in Rust (`pympsc.rs`), and runs on this thread holding its GIL. It pops the box and calls `PendingMessage::into_queued`, producing a `QueuedMessage` (`PyContext`, method, bytes, refs, port).
*Rust that creates Python objects runs only on Python's thread.*

**Panel 7: the call**
`_Actor.handle` unpickles the arguments, finds the endpoint, and runs it, awaiting it if async. Effects land on your actor's state. The result or exception is pickled and sent through `response_port`, completion or failure is reported, and the caller's future resolves.

**Panel 8: repeat**
Back to `try_recv`. Anything that queued up during the handler is drained without sleeping again.

**The one-liner:** Rust owns the mailbox and never takes the GIL. Python owns the event loop and makes every Python object on its own thread. A queue plus a pipe byte joins them. In algebra terms, `_dispatch_loop` is a fold over messages: your actor object is the state, and the replies are the outputs.

**The exception:** supervision (`MeshFailure`) skips the queue: Rust schedules `__supervise__` directly on the same loop.
