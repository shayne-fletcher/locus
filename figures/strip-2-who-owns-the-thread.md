# Strip 2: who owns the thread?

Seed for `images/strip-2-who-owns-the-thread.png`, which opens the section "Two drivers". Everything below the line is the prompt; paste it whole. Panel content is maintained alongside the Monarch checkout's `strips/` and copied here.

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

**Layout:** every panel is split into an **ASYNC** column (blue header) and a **SYNC** column (pink header). The one-liner and "What it replaces" sit in two boxes along the bottom. Leave out the "Notes (not for rendering)" section.

**Title banner:** "Two Python actors: who owns the thread?", with a small note to its right: "(monarch-1 at d16adfd48; the sync side is in progress)".

**Panels.**

**Panel 1: the cast**
```
ASYNC                              SYNC
thread ──calls──▶ run_forever      thread ──owns──▶ private loop (idle)
          (never returns)            └─ its own while-loop
```
Left: the thread gives itself to the loop. Right: the thread keeps control and keeps a loop in its pocket.

**Panel 2: waiting**
- **Async:** asleep in the selector, GIL released; `add_reader` is watching the pipe.
- **Sync:** asleep in `recv_blocking()`, GIL released; it waits on the queue itself.

*No pipe on the right: there's no running loop to wake.*

**Panel 3: a message arrives**
- **Async:** pipe byte → selector wakes → reader callback sets the event → `_dispatch_loop` resumes.
- **Sync:** `recv_blocking` returns, and the thread's own loop just continues.

**Panel 4: the conversion**
- **Async:** `try_recv()` (Rust, holds the GIL): `PendingMessage` → `QueuedMessage`.
- **Sync:** `recv_blocking()` (Rust): waits with the GIL released, then takes it to do the same conversion.

*Python objects are only ever made on Python's thread.*

**Panel 5: the endpoint runs**
- **Async:** `await endpoint(...)`, one task step at a time on the loop.
- **Sync:** `endpoint(...)`, a plain call.

*Nothing is hidden on the right, because nothing is running.*

**Panel 6: it needs a Monarch future**
```
ASYNC                              SYNC
await handle                       handle.get()
  Tokio wakes the loop               parks in Tokio, GIL released
  with a pipe byte (no GIL)
await returns_future body          body.get()
  runs as a task on this loop        runs on this thread's private loop:
                                     run_until_complete, then returns
```
*Two kinds of future: a `Handle` is native work; a `@returns_future` body is Python orchestration. Neither hands work to another thread.*

**Panel 7: other work** (supervise, cleanup, spawned tasks)
- **Async:** Rust schedules it onto the loop; it interleaves with the current endpoint at its `await`s. `@concurrent_endpoint` bodies run as tasks too, and the loop yields every 64 messages so they get a turn.
- **Sync:** it arrives on the same queue and runs in order, between endpoints. No concurrent endpoints: one endpoint at a time, always.

**Panel 8: done, go again**
Both reply through `response_port`. Then async goes back to `try_recv`; sync goes back to `recv_blocking`.

**The one-liner:** Async: the thread lives inside the loop. Sync: the loop lives inside the thread, and only wakes up when called.

**What it replaces:** today's sync actor is the async column with the loop frozen and hidden (`fake_sync_state`) during every call.

## Notes (not for rendering)

- **Panel 4:** `try_recv` is `PyReceiver::try_recv` (`monarch_hyperactor/src/pympsc.rs`), declared in `python/monarch/_src/actor/mpsc.py` and bound by `@rust_struct`. `recv_blocking` doesn't exist yet; the design requires it to wait with the GIL released (like `py.detach`) and convert with it held (like `try_recv`), or it would starve every other Python thread.
- **Panel 6, Handle:** `Handle.get` (`monarch_hyperactor/src/handle.rs`) polls, then waits via `signal_safe_block_on` (`monarch_hyperactor/src/runtime.rs`), which releases the GIL and briefly retakes it to check for signals. The await path's GIL-free pipe wake is #4991.
- **Panel 6, body:** `_drive` in `python/monarch/_src/actor/returns_future.py` runs the body with `loop.run_until_complete` on `_loop()` / `_THIS_THREAD.loop`, a per-thread loop made on first use, so the private loop already exists. Today's sync endpoint can't use it (its thread's real loop is hidden, not absent), so `get()` falls back to `_drive_on_helper`, a short-lived helper thread (#4996, "a compatibility bridge for synchronous endpoints"). The proposal removes the need for that bridge.
- **Panel 6, legacy:** pytokio's `PythonTask` still exists today but is being removed (`scripts/pytokio_removal_census.toml`; #4997–#5001 migrate producers to `returns_future`).
- **Panel 7, async:** supervision and cleanup are scheduled with `pyo3_async_runtimes::into_future_with_locals`. Ordinary endpoints never overlap: `_dispatch_loop` awaits one `handle` before the next `recv` (`python/monarch/_src/actor/actor_mesh.py`). The yield is `_DISPATCH_BATCH = 64` with `await asyncio.sleep(0)` (#4960).
- **Panel 7, sync:** the `@concurrent_endpoint` wrapper is an `async def` (`python/monarch/_src/actor/concurrent.py`), so an actor using one is an async actor, and mixing sync and async endpoints is rejected (`actor_mesh.py`).
- **What it replaces:** `fake_sync_state` (`python/monarch/_src/actor/sync_state.py`) sets the thread's running loop to `None` for each sync endpoint call. Inside, a `get()` sees no loop and blocks the OS thread in Tokio while anything else scheduled on that loop waits.
- **The asyncio rules this rests on:**
  - A loop runs on one thread, and a thread has at most one *running* loop.
  - `run_forever()` is an ordinary call that doesn't return until `loop.stop()`: wait in the selector, run the ready callbacks, repeat.
  - Other threads submit work only via `call_soon_threadsafe` / `run_coroutine_threadsafe`.
  - `run_until_complete` while that thread already has a running loop raises `RuntimeError`, which is why today's sync actor has to hide its loop.
