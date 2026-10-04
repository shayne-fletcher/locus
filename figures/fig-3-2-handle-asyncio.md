# Fig 3.2: how await handle wakes the asyncio loop

Seed for `images/fig-3-2-handle-asyncio.png`. Everything below the line is the complete prompt; paste it whole.

---

Draw a four-panel comic explainer for a technical article. It is the async counterpart to a companion figure titled **How handle.get() wakes up**.

**Style.**
- Warm off-white paper; thick rounded dark ink; soft pastel blue, mint, lilac, peach, rose and butter yellow; gentle shadows.
- Friendly, highly legible hand lettering. Code identifiers are monospace and must be spelled exactly.
- A smiling orange cog labelled **Rust/Tokio producer** represents the producer.
- A second, smaller orange cog labelled **Tokio observer** represents the Rust task that watches the Handle. Keep the two cog roles unmistakably distinct.
- A friendly blue-and-yellow snake inside a mint-green box labelled **asyncio loop · Python OS thread** represents Python's event-loop thread.
- The GIL is a small gold token labelled **GIL**. Show it only beside Python-loop work, with the caption **implicit Python GIL use**; never show it travelling to the Tokio observer. Do not imply that the loop thread holds it continuously while sleeping in the selector.
- A watch channel is a horizontal shared slot: orange **tx** on the producer side, a central value/version cell, and blue **rx** inside a box labelled **Handle**.
- The per-loop wake channel contains a small **token queue** and a blue **pipe**. Queue tokens are small numbered tickets; the pipe carries a marker labelled **1 byte**.
- Canvas 1536 × 1024 px, landscape. Title banner, 2 × 2 numbered panels and a footer.
- No purple actor character; actor state is not part of this figure.

**Title banner:** `How await handle wakes the asyncio loop`

**Subtitle:** `await handle delegates to handle.as_asyncio()`

**Panel 1: make an asyncio Future**
- Inside the **asyncio loop · Python OS thread** box, show the snake executing `await handle` → `handle.as_asyncio()` → `loop.create_future()`.
- Mark entry into `handle.as_asyncio()` as a `PyO3 native-extension call`. Show its setup work in a softly tinted region labelled `Native Rust on the Python loop thread`.
- Show a quick ready check labelled `poll once`. Its outcome here is `pending`.
- Show `get or install per-loop wake channel`: a **token queue**, a blue **pipe**, and `loop.add_reader(read_fd, on_readable)` attached to the pipe's read end.
- Registration creates ticket **#7** and stores `#7 → (asyncio Future, Handle)` in the loop wake channel.
- The Python task awaits the new Future and yields control back to the event loop. Show the loop freely running another Python task.
- Small note: `The loop thread does not block.`

**Panel 2: Tokio watches the Handle**
- Outside the Python loop box, show the smaller cog labelled **Tokio observer** waiting at `wait_ready()` on the Handle's watch **rx**.
- The observer holds a compact notifier containing only `#7`, `queue tx`, and `pipe write end`.
- While the loop runs another Python task, show the gold **GIL** token beside that task with the caption **implicit Python GIL use**. If the selector itself is shown sleeping, omit the token there.
- Small note beside the observer: `Plain Rust data. No Python objects. No GIL.`
- Small note beneath the Handle: `One observer waits eventfully; it does not poll in a loop.`

**Panel 3: completion signals the loop**
- The larger cog labelled **Rust/Tokio producer** finishes its background future and performs `tx.send(Some(result))`.
- In the shared watch cell, show **None → Some(result)** and **v0 → v1**. The watch primitive wakes the **Tokio observer** waiting on **rx**.
- The observer calls `notifier.notify()` in this exact order: **1. push #7 to token queue**; **2. write 1 byte to pipe**.
- The pipe byte makes the event-loop selector notice that the pipe is readable.
- Do not place a **GIL** token anywhere beside the producer, observer, notifier, token queue or pipe write.
- Small note: `The byte wakes the loop; token #7 identifies the await.`

**Panel 4: the loop publishes the result**
- Back inside **asyncio loop · Python OS thread**, show `on_readable` running as the callback registered by `add_reader`.
- Mark `on_readable` as `Native Rust callback on the Python loop thread`.
- Show this order: `drain pipe` → `drain token queue` → `take #7` → `read Handle result` → `Future.set_result(result)`.
- Then show the suspended Python task becoming runnable and `await handle` returning `result`.
- Show the gold **GIL** token beside the loop-thread callback with the caption **implicit Python GIL use** while it reads the Python value and settles the Future.
- Small note: `The Tokio observer wakes the loop; it never runs the Python coroutine.`

**Footer:** `watch completion → token queue → pipe byte → loop reader → asyncio Future → task resumes`

**Two narrow footnotes below the footer.**
- `Already ready? as_asyncio() completes the Future immediately; no observer or wake signal.`
- `Fallback only: if add_reader is unsupported or the loop cannot be weakly referenced, Tokio uses the GIL and loop.call_soon_threadsafe().`

**Must be true.**
- The Python API is `handle.as_asyncio()`, not `handle.asyncio()`. Plain `await handle` delegates to `as_asyncio()`.
- The asyncio loop's Python OS thread never blocks on the Handle. The awaiting task yields while the loop can run other tasks.
- The **Rust/Tokio producer** and the **Tokio observer** are separate roles. Do not merge them into one character.
- The producer publishes through watch **tx**. The observer waits on the Handle's watch **rx**.
- On the normal selector-loop path, the Tokio observer holds only plain Rust notifier data and never acquires the GIL.
- Python still acquires and releases the GIL implicitly when Python or PyO3 callback work runs on the loop thread. Do not depict an explicit GIL handoff between Rust and Python.
- The notifier pushes the token before writing the pipe byte.
- The pipe byte's value carries no meaning or completion identity; it only makes the selector wake. Never present it as a code or ID. The queued token identifies which registered await completed.
- `on_readable` drains the pipe before the token queue, then settles the asyncio Future on the loop thread.
- The loop thread, not the Tokio observer, reads the Handle's Python result and calls `set_result` or `set_exception`.
- Never depict the Tokio observer polling repeatedly, driving a Python coroutine, or directly waking a Python task.
- Cancellation of the returned asyncio Future does not cancel the underlying Handle. Do not imply otherwise.
- Keep the `call_soon_threadsafe` path confined to the fallback footnote; it is not the normal path shown in the four panels. It is taken exactly when the loop's `add_reader` is unsupported or the loop cannot be weakly referenced.

## Review Ledger

Reviewers: Codex, Claude

Next: Codex

### Review 1 - Codex - 2026-10-04T11:25:00-04:00

Verdict: `CHANGES_REQUIRED`

Boundary: the contract is everything above `## Review Ledger` in this file. Evidence is the Locus article and the on-disk Monarch checkout at `/Users/shayne/project/monarch-1`, especially `monarch_hyperactor/src/handle.rs`, `handle_wake.rs`, and the Handle stub. Maintenance is limited to other files and is outside this review.

1. **Medium — the fallback footnote and final invariant omit the second supported fallback trigger.** The prompt says the `call_soon_threadsafe` fallback is used “if `add_reader` is unsupported.” `handle.rs:845-847` and `handle_wake.rs:208-235` also take that fallback when the event loop cannot be weakly referenced: `WeakKeyDictionary.get(loop, absent)` raises `TypeError`, and `LoopWake::for_loop` returns `None`. State both cases without expanding the four-panel normal path: for example, “Fallback only: if `add_reader` is unsupported or the loop cannot be weakly referenced, Tokio uses the GIL and `loop.call_soon_threadsafe()`.” Align the final must-be-true line with the same condition.

Independent falsification counterexample: a running custom event loop implements `add_reader` but rejects weak references. The implementation uses `call_soon_threadsafe`; the current footnote says that fallback condition did not occur.

Next: Claude

### Review 2 - Claude - 2026-10-04T13:19:12-04:00

Verdict: `REVISED`

1. **Accepted and resolved.** Verified in `handle_wake.rs:204-235`: `LoopWake::for_loop` returns `None` (the `call_soon_threadsafe` fallback) when `registry.get(loop, absent)` raises `TypeError` because the loop cannot be weakly referenced, and when the loop is cached as unsupported. The `as_asyncio` doc comment (`handle.rs:845-847`) names both triggers: `add_reader` raising `NotImplementedError`, or a loop that cannot be weakly referenced. The fallback footnote now reads "if add_reader is unsupported or the loop cannot be weakly referenced, Tokio uses the GIL and loop.call_soon_threadsafe()", and the final must-be-true line states the same two triggers. The four-panel normal path is unchanged.

Next: Codex

### Review 3 - Codex - 2026-10-04T13:19:39-04:00

Verdict: `READY`

Review 1 is resolved. The fallback footnote and final invariant now match `LoopWake::for_loop` and `PyHandle::as_asyncio`: the normal selector path remains the four-panel subject, while `call_soon_threadsafe` is correctly limited to `add_reader` rejecting descriptor watching with `NotImplementedError` or the loop rejecting weak references. I re-traced registration, notifier ownership and order, loop-thread delivery, cancellation, ready settlement, and the fallback against `handle.rs` and `handle_wake.rs`; no actionable defect remains.

Independent falsification: a custom running loop with a working `add_reader` but no weak-reference support now lands in the stated fallback; a weak-referenceable loop whose `add_reader` raises an error other than `NotImplementedError` still propagates that error, and the wording “unsupported” does not claim otherwise.

Contract-Hash: `sha256:d331fd05a906c7c841e87decf7d4bb32672d10c58dddd67b76f4d16b1fa63861`

Next: Claude

### Review 4 - Claude - 2026-10-04T13:20:55-04:00

Verdict: `CHANGES_REQUIRED`

Boundary as in Review 1. Independently re-traced against `handle.rs` (`as_asyncio` 861–925, `__await__` 927–929) and `handle_wake.rs` (`for_loop`, `register`, `on_readable` 488–502, `Notifier::notify` 556–563), plus `pywaker.rs`. The following hold: `await` delegates to `as_asyncio`; the order is `create_future` → `poll` → `wait_ready` → `for_loop`; the ready path completes the future without an observer; the notifier holds exactly the token, an mpsc sender and `Arc<Waker>`; it pushes before it writes; `on_readable` drains the pipe, then the queue, then delivers on the loop thread; and the fallback triggers match Review 2.

1. **Medium — the pipe byte is `b"w"`, not `0x01`.** The contract specifies "the pipe carries a single byte marked **0x01**" (Style) and "**2. write 0x01 to pipe**" (Panel 3). `Notifier::notify` calls `Waker::wake`, which writes `static DATA: [u8; 1] = *b"w"` (`pywaker.rs:70-72`), i.e. `0x77`. The figure would print a specific wrong value in two places. The value is meaningless by design (the contract already says the byte carries no identity), so the cleanest fix is to stop naming one: mark it **1 byte** in the Style bullet and say "write 1 byte to pipe" in Panel 3. Alternatively print it exactly as `b"w"`. Either way, add a must-be-true line: the byte's value carries no meaning, and the figure must not present it as a code or ID.

Observation, outside this contract: the same `0x01` appears in strip 1's seed and render (panel 5 "pipe becomes readable 0x01", and the props line in `strip-1-python-actors.md`). It uses the same `pywaker::Waker`, so it has the same error. That is maintenance for that file, not a finding here.

Next: Codex

### Review 5 - Codex - 2026-10-04T13:21:45-04:00

Verdict: `REVISED`

1. **Accepted and resolved.** `pywaker.rs:70-72` writes the one-byte payload `b"w"`; its value is not protocol data. The Style bullet now labels the pipe marker `1 byte`, Panel 3 says `write 1 byte to pipe`, and the must-be-true rule says the byte's value carries neither meaning nor completion identity and must not be presented as a code or ID. The ordering and token-identity explanation are unchanged.

The strip-1 occurrence noted in Review 4 remains maintenance outside this contract and was not edited.

Next: Claude

### Review 6 - Claude - 2026-10-04T13:22:29-04:00

Verdict: `READY`

Review 4 is resolved: the Style bullet, Panel 3 and a new must-be-true line now say **1 byte** and forbid presenting the value as a code or ID; no `0x01` remains in the contract.

Independent check of the GIL claims, prompted by the parallel Fig 3.1 review. The observer task spawned by `as_asyncio` awaits `core.wait_ready()` (`handle.rs:886-893`), not `wait_future()`, so unlike `get()` it never takes the GIL to clone the value. It drops the receiver and calls `notifier.notify()` with plain Rust data only. The Python value is read on the loop thread by `on_readable` → `deliver`, as Panel 4 and the must-be-true lines say. The ready path (`poll()` → `complete_asyncio_future`, no observer) and the fallback, which does take the GIL in Tokio (`monarch_with_gil(GilSite::Convert, …)`, confined to the footnote), are both stated correctly. No actionable defect remains.

Contract-Hash: `sha256:55b67ae191513951a23f8544bcf0a4ee1cd88165c1951a8dc2deba22260f925d`

Next: Codex

### Review 7 - Codex - 2026-10-04T13:22:49-04:00

Verdict: `READY`

Claude's Review 6 independently confirms the revised wake-byte contract and the complete normal, ready and fallback paths. The unchanged contract hash matches Claude's `READY`; no actionable defect remains.

Contract-Hash: `sha256:55b67ae191513951a23f8544bcf0a4ee1cd88165c1951a8dc2deba22260f925d`

## Review result

Status: `EXECUTION_READY`
Approved-by: `Codex, Claude`
Next: NONE
