# Fig 3.1: how handle.get() wakes

Seed for `images/fig-3-1-handle-get.png`. Everything below the line is the complete prompt; paste it whole.

---

Draw a four-panel comic explainer for a technical article.

**Style.**
- Warm off-white paper; thick rounded dark ink; soft pastel blue, mint, lilac, peach, rose and butter yellow; gentle shadows.
- Friendly, highly legible hand lettering. Code identifiers are monospace and must be spelled exactly.
- A smiling orange cog represents the Rust/Tokio producer.
- A friendly blue-and-yellow snake, explicitly tagged **Python OS thread**, represents the calling Python thread.
- The GIL is a small gold token labelled **GIL**.
- A watch channel is a horizontal shared slot: orange **tx** on the producer side, a central value/version cell, and blue **rx** inside a box labelled **Handle** on the Python side.
- Canvas 1536 × 1024 px, landscape. Title banner, 2 × 2 numbered panels and a footer.
- No purple actor character; actor state is not part of this figure.

**Title banner:** `How handle.get() wakes up`

**Panel 1: the pair**
- Left: orange Rust/Tokio producer holding **tx**.
- Centre: watch cell labelled **None**, with a small version mark **v0**.
- Right: blue **Handle** box containing **rx**, held by the snake tagged **Python OS thread**.
- Arrows show `tx → shared watch value ← rx`.
- Small note: `Handle owns rx; producer owns tx.`

**Panel 2: get() waits**
- Flow: `handle.get()` → `poll once` → `pending`.
- Mark the boundary immediately after `handle.get()` with the label: `PyO3 native-extension call`.
- The snake places the gold **GIL** token aside.
- Then: `signal_safe_block_on` hands a wait future to Tokio, and the snake blocks.
- Draw that future as a small orange-outlined bubble labelled **Rust wait future driven by Tokio**, containing `rx.changed().await`, connected to the blocked snake by a short tether.
- Under the bubble, a small two-line caption: `main thread: spawned onto a Tokio worker` / `other threads: driven by block_on on this thread`.
- Show the wait future registering a **waker** with the watch channel, then sleeping.
- Tint the snake's area softly and label it: `Python OS thread blocked in signal_safe_block_on` with a smaller line: `GIL released while waiting`. The thread is parked, not spinning.
- Small note: `No asyncio loop. No pipe. No busy polling.`

**Panel 3: producer completes**
- Orange Rust/Tokio cog finishes the background future.
- Show: `result` → `tx.send(Some(result))`.
- In the shared watch cell, show **None → Some(result)** and **v0 → v1**.
- Then show the watch primitive calling `notify_waiters()` toward the registered waker.
- Small note: `The producer builds the stored Python object under the GIL if conversion is needed.`

**Panel 4: wake and return**
- The registered **waker** makes the Rust wait future runnable.
- Flow: `waker` → `Tokio polls the wait future again` → `rx sees v1` → `clone result under the GIL (brief)` → `future completes`.
- Draw a small gold **GIL** token at the clone step, attached to the wait-future bubble. Its polling location follows Panel 2's two-case caption.
- The same snake tagged **Python OS thread** resumes as `py.detach` ends, holds the gold **GIL** token again and returns `result` from `handle.get()`.
- Small note: `The waker wakes the future; block_on releases the blocked call.`

**Footer:** `watch send → waker → Tokio polls waiter → handle.get() returns`

**Must be true.**
- The sender publishes a value through **tx**; it does not “push the tx end.”
- The Python-visible **Handle** contains **rx**, not **tx**.
- `handle.get()` performs one ready check, then waits eventfully; never depict a spin loop.
- The waker wakes the Rust future, not Python directly.
- The wait future is driven by Tokio, and where it is polled depends on the caller: spawned onto a Tokio worker when `get()` is called on Python's main thread, driven by `block_on` on the blocked caller otherwise. Show that with the bubble's caption, not by placing the bubble on one thread. The stable fact is that the same Python OS thread blocks with the GIL released and later returns the result.
- After the watch wake, the wait future briefly takes the GIL to clone the stored Python result before it completes. Keep this distinct from the producer's earlier conversion and the caller's reacquisition when `py.detach` ends.
- The calling Python OS thread before and after the wait is visibly the same snake.
- No asyncio event loop, selector, self-pipe or reader callback appears anywhere.
- Do not imply that every producer is Python-owned. This figure shows the ordinary native Rust/Tokio producer case.

## Review Ledger

Reviewers: Codex, Claude

Next: Codex

### Review 1 - Codex - 2026-10-04T11:25:00-04:00

Verdict: `CHANGES_REQUIRED`

Boundary: the contract is everything above `## Review Ledger` in this file. Evidence is the Locus article and the on-disk Monarch checkout at `/Users/shayne/project/monarch-1`, especially `monarch_hyperactor/src/handle.rs`, `runtime.rs`, and Tokio 1.53.1's locked watch implementation. Maintenance is limited to other files and is outside this review.

1. **High — Panel 2 places the watch wait on the Python OS thread in a case where it runs on Tokio.** The prompt encloses `signal_safe_block_on → rx.changed().await` inside “Native Rust on the Python OS thread.” In `runtime.rs:348-361`, when the caller is Python's main thread, `signal_safe_block_on` explicitly spawns the supplied wait future onto the Tokio runtime and the Python thread blocks on a `select!` over its `JoinHandle` and signal checks. Only the non-main-thread branch directly drives the wait future with `runtime.block_on(future)`. Keep the stable truth—same Python OS thread blocks with the GIL released and later returns—but depict the watch waiter as a Tokio future, not universally as executing on that Python thread. The signal-check side path need not be drawn.

Independent falsification counterexample: call pending `handle.get()` from Python's main thread. The registered watch waker belongs to the Tokio-spawned wait task, while the caller thread is blocked waiting for that task; the current region label assigns both roles to the caller thread.

Next: Claude

### Review 2 - Claude - 2026-10-04T13:19:12-04:00

Verdict: `REVISED`

1. **Accepted and resolved.** Verified in `runtime.rs:338-372`: `signal_safe_block_on` releases the GIL (`py.detach`); on the main thread it `runtime.spawn`s the future and `block_on`s a `select!` over the `JoinHandle` and a 100 ms signal check; off the main thread, `runtime.block_on(future)` drives the future on the caller. So the waiter's executing thread varies, and the "Native Rust on the Python OS thread" region was wrong for the main-thread case. Panel 2 now draws the wait as a separate bubble, **Tokio wait future** containing `rx.changed().await`, beside the snake and outside its region, registering the waker. The tinted region encloses only the snake: `Python OS thread blocked in signal_safe_block_on`, GIL released, parked. A new must-be-true line forbids placing the wait future inside the Python thread's region and states the stable fact: the same thread blocks with the GIL released and later returns. The signal-check side path is not drawn, as Codex suggested. Panels 1, 3 and 4 are unchanged; Panel 4's `waker → Tokio polls waiter again` was already neutral about which thread polls.

Next: Codex

### Review 3 - Codex - 2026-10-04T13:19:39-04:00

Verdict: `CHANGES_REQUIRED`

The original main-thread error is removed, but the revision replaces it with an opposite universal placement rule.

1. **Medium — “never draw [the wait future] inside the Python OS thread's region” contradicts the non-main-thread branch.** `runtime.rs:368-370` calls `runtime.block_on(future)` directly after `py.detach`; Tokio polls that future on the blocked calling Python OS thread. The new separate bubble is a good abstraction if it is presented as logical ownership rather than physical thread placement, but the contract explicitly forbids the physically correct non-main-thread placement. Keep the bubble neutral: label it `Rust wait future driven by Tokio`, connect it to the blocked caller, and say its polling location varies—spawned onto Tokio for Python's main thread, driven on the blocked caller otherwise. Remove the universal “not inside” / “never draw inside” requirements, or show the two execution cases explicitly.

Independent falsification counterexample: call pending `get()` from a non-main Python thread. That thread enters the non-main branch and polls `wait_future` through `runtime.block_on(future)`; the revised must-be-true says the figure may never place that future on the thread where it actually runs.

Next: Claude

### Review 4 - Claude - 2026-10-04T13:20:22-04:00

Verdict: `REVISED`

1. **Accepted and resolved.** Correct: my Review 2 swapped one universal placement for its opposite. `runtime.rs:368-370` drives the future with `runtime.block_on(future)` on the calling thread when it is not Python's main thread, so "never inside" is false there. Taking Codex's neutral form: the bubble is now **Rust wait future driven by Tokio**, tethered to the blocked snake, with a two-line caption `main thread: spawned onto a Tokio worker` / `other threads: driven by block_on on this thread`. The snake's tinted area keeps `Python OS thread blocked in signal_safe_block_on` and `GIL released while waiting`. Both "not inside its region" and "never draw it inside" are removed. The must-be-true line now states that the polling location varies by caller and is shown by the caption, not by placing the bubble on one thread, and keeps the stable fact (same thread blocks with the GIL released, later returns).

Next: Codex

### Review 5 - Codex - 2026-10-04T13:21:05-04:00

Verdict: `READY`

Review 3 is resolved. Panel 2 now separates the logical Rust wait future from the caller while explicitly stating both physical execution cases: spawned onto a Tokio worker for Python's main thread, and polled by `runtime.block_on` on the blocked caller otherwise. The stable user-visible lifecycle—same Python OS thread blocks with the GIL released and returns after the watch wake—is preserved without assigning the waiter to the wrong thread. I rechecked the ready fast path, `wait_future`/`wait_ready`, `signal_safe_block_on`, watch notification and return path; no actionable defect remains.

Independent falsification: both main-thread and non-main-thread pending `get()` calls now map to explicit captions, while an already-ready `get()` remains outside the depicted pending path.

Contract-Hash: `sha256:030049e587bd85dfc1b96dda11821d4bc5d897bd5fd14057d21b7486604aa88f`

Next: Claude

### Review 6 - Claude - 2026-10-04T13:21:58-04:00

Verdict: `CHANGES_REQUIRED`

Independent pass over the whole pending path: `get` (`handle.rs:767-825`) warns on a running loop, fast-paths a ready value with `core.poll()`, then builds `core.wait_future()`, drops the `PyRef` and calls `signal_safe_block_on`. Panels 1–3 and the Review 4 captions hold.

1. **Medium — Panel 4 omits the wait future's own GIL acquisition, and puts the conversion on the wrong side.** `wait_future` (`handle.rs:395-412`) is `wait_ready().await` followed by `monarch_with_gil(GilSite::Convert, |py| rx.borrow()… v.clone_ref(py))`. After the watch wake, the *Rust wait future* takes the GIL to clone the result out of the watch cell before it completes. Where it does so follows Review 4's captions: on a Tokio worker for Python's main thread, on the blocked caller otherwise. The contract instead puts the only post-wake GIL on the snake ("resumes, takes the gold GIL token and returns result"). Its Panel 3 note, "Convert to a Python object under the GIL if needed", sits on the producer, which reads as though the producer does the conversion that `wait_future` actually performs. In a figure series about where the GIL is held, that hides the one GIL acquisition inside the Rust wait. Fix:
   - Panel 4 flow: `waker` → `Tokio polls the wait future again` → `rx sees v1` → `clone result under the GIL (brief)` → `future completes`. Draw a small gold **GIL** token at the clone step, attached to the wait-future bubble rather than the snake.
   - Then the snake resumes (its `py.detach` ends, so it holds the GIL again) and returns `result`.
   - Panel 3: the producer note becomes "the producer stores a Python object; it built it under the GIL", or drop the note.
   - Add a must-be-true line: the wait future takes the GIL briefly after the wake to clone the result; this is the only GIL use during the wait.

Observation (not a finding): on Python's main thread, `signal_safe_block_on` also retakes the GIL every 100 ms to check signals (`runtime.rs:357-361`). Review 1 chose not to draw that side path. "GIL released while waiting" is accurate enough, but if the figure later grows a footnote, that is its place.

Next: Codex

### Review 7 - Codex - 2026-10-04T13:22:49-04:00

Verdict: `REVISED`

1. **Accepted and resolved, with the exclusivity claim narrowed.** Panel 4 now shows `wait_future` taking the GIL briefly after `wait_ready` wakes, cloning the stored Python result, and only then completing. The token is attached to the logical wait-future bubble, whose two-case caption controls where polling occurs. The snake subsequently resumes as `py.detach` ends, holds the GIL again, and returns. Panel 3 now explicitly describes the distinct producer-side operation: building the stored Python object under the GIL when conversion is needed. A must-be-true line keeps producer conversion, waiter cloning and caller reacquisition separate.

I did not add “this is the only GIL use during the wait”: on Python's main thread, the intentionally omitted signal-check side path also reacquires the GIL every 100 ms. The contract remains accurate by showing the completion path without claiming exclusivity.

Next: Claude

### Review 8 - Claude - 2026-10-04T13:23:37-04:00

Verdict: `READY`

Review 6 is resolved, and the narrowing is right. My proposed "only GIL use during the wait" would have contradicted my own observation about the main-thread signal check (`runtime.rs:357-361`); Codex's wording claims no exclusivity. Re-read the whole contract against `handle.rs` (`get` 767-825, `wait_future` 395-412, `wait_ready` 423-440) and `runtime.rs` (`signal_safe_block_on`):

- Panel 3 attributes the Python object to the producer, consistent with the watch cell holding `Py<PyAny>` results.
- Panel 4's `rx sees v1` → `clone result under the GIL (brief)` → `future completes` matches `wait_ready` followed by `monarch_with_gil(GilSite::Convert, …)`. Its GIL token sits on the wait-future bubble, whose two-case caption governs where the clone runs.
- The snake's reacquisition is tied to `py.detach` ending.
- The invariants keep the three GIL uses distinct.

Falsification, a new case: a `get(timeout=…)` that expires. `tokio::time::timeout` drops the wait future before the clone step, so no GIL is taken there and `TimeoutError` is raised. The figure depicts only the untimed pending path and states nothing the timeout path contradicts. No actionable defect remains.

Contract-Hash: `sha256:977a37ffcece1925bb4ae6b3ffe23e0733e5a82d7cb47db8804e6c72a797e6f3`

Next: Codex

### Review 9 - Codex - 2026-10-04T13:23:44-04:00

Verdict: `READY`

Claude's Review 8 independently confirms the revised pending `get()` execution, wake, GIL and return path. The unchanged contract hash matches Claude's `READY`; no actionable defect remains.

Contract-Hash: `sha256:977a37ffcece1925bb4ae6b3ffe23e0733e5a82d7cb47db8804e6c72a797e6f3`

## Review result

Status: `EXECUTION_READY`
Approved-by: `Codex, Claude`
Next: NONE
