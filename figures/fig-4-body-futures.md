# Fig 4: a body future, Python to Python

Seed for `images/fig-4-body-futures.png`. Everything below the line is the complete prompt; paste it whole.

---

Draw a four-panel comic explainer for a technical article. Its point: **a `@returns_future` body is Python at both ends. It runs on a Python thread and is read on Python threads; only the channel and the notification run through Rust, the same reporting mechanism a native Rust task uses.** It precedes two companion figures titled **How handle.get() wakes up** and **How await handle wakes the asyncio loop**.

**Style.**
- Warm off-white paper; thick rounded dark ink; soft pastel blue, mint, lilac, peach, rose and butter yellow; gentle shadows.
- Friendly, highly legible hand lettering. Code identifiers are monospace and must be spelled exactly.
- A friendly blue-and-yellow snake represents a Python OS thread. Where it runs an event loop, it sits inside a mint-green box labelled **asyncio loop**.
- A lavender scroll labelled **body** represents the coroutine of a `@returns_future` function: Python code.
- The result is a small round lavender gem labelled **value**: one Python object. Wherever it appears, it is the same gem.
- The GIL is a small gold token labelled **GIL**.
- The watch channel is a small glass cell showing **None** (pending) or holding the **value** gem. Its writing end is an orange pen labelled **tx**, held by a small box labelled `_HandleCompleter`. Its reading end is a blue box labelled **Handle** containing **rx**.
- A small brass bell labelled **notify** is an abstract sign that Rust reports the channel is ready. It does not show how any reader is physically woken, or what that wake-up carries.
- Canvas 1536 × 1024 px, landscape. Title banner, 2 × 2 numbered panels, a one-liner box, a footer and footnotes.
- No purple actor character and no orange cogs.

**Every panel has the same three bands.** Two vertical dashed lines divide each panel into three bands:
- left, pale blue, header **Python thread (writer)**;
- middle, narrower, pale peach, header **Rust: the channel**;
- right, pale blue, header **Python threads (readers)**.

The watch cell always sits in the middle band. Python work always sits in an outer band.

**Title banner:** `A body future: Python in, Python out`

**Subtitle:** `Both ends are Python. Only the channel and the notification run through Rust.`

**Panel 1: calling it runs nothing**
- Left: a code card, `@returns_future` above `async def fetch(...)`, and the call `fetch(...)`.
- The call produces a box labelled **Future**. Inside it: the rolled-up **body** scroll with a small padlock (`not started`), and a matched pair labelled `_new_handle_pair()`.
- From that pair, the `_HandleCompleter` with its **tx** pen stays in the left band, and the **Handle** with **rx** goes to the right band. Both connect to an empty watch cell in the middle band, showing **None**.
- Small note: `Two Python-held ends, one Rust channel between them.`

**Panel 2: the first observer runs the body**
- Left: a snake inside an **asyncio loop** box. The scroll unrolls and runs as a task, with the gold **GIL** token beside it. Caption: `started by its first observer, which chooses the loop`.
- Two tiny labels under the loop: `first await → a task on the awaiting loop` and `ordinary first .get() → this thread's own loop`.
- Middle: the watch cell still shows **None**. Caption: `nothing runs here`.
- Right: two reader snakes waiting, one labelled `handle.get()`, one inside a small **asyncio loop** labelled `await`.
- Small note: `Python work, on a Python thread. Tokio never drives the body.`

**Panel 3: the body reports**
- Left: the scroll finishes and produces the **value** gem.
- Flow on the left: `task done` → `_Settler.publish_task` → `completer.set_result(value)`, with the gold **GIL** token beside it: `already on a Python thread`.
- The **tx** pen places the gem into the watch cell in the middle band: **None → value**. A label on the cell: `stored as is: a reference, not a copy`.
- The **notify** bell in the middle band rings toward the right band.
- Small note: `Python hands Rust a Python object. Rust does not open it.`

**Panel 4: the readers get the same object**
- Middle: the **notify** bell, ringing: `the channel is ready`.
- Right: both Handle readers receive the **value** gem: one returns it from `handle.get()`, the other's `await` returns it inside its **asyncio loop**. Each holds the gold **GIL** token.
- Two small pointers under the readers: `how get() wakes: see "How handle.get() wakes up"` and `how await wakes: see "How await handle wakes the asyncio loop"`.
- Both reader snakes hold an identical gem, and a small banner between them reads `result is value`.
- Small note: `Same object for every Handle reader. Rust held the reference and rang the bell.`

**The one-liner** (a wide box under the panels): `Both ends are Python. Rust holds one reference and reports that it is ready: the same reporting mechanism a native task uses.`

**Footer:** `fetch() → body on a Python loop → set_result → watch channel → notify → readers on Python threads`

**One narrow footnote below the footer.**
- `A first .get() drives the body itself and returns the identical object straight from the body's task, not through the Handle; a first .get() inside a running loop drives it on a short-lived helper thread. Every other observer reads the Handle.`

**Must be true.**
- The body runs only in the left band, as an asyncio task on a Python thread's loop. Never draw the body, a scroll or any Python code in the middle band.
- The writer end (`_HandleCompleter`, **tx**) and the reader end (**Handle**, **rx**) are both held and called by Python code, so they sit in the outer bands. Only the watch cell and the **notify** bell sit in the middle band.
- `set_result` stores the Python object itself, by reference, with no conversion. Every reader gets the same object (`result is value`), not a copy.
- The **notify** bell is abstract: it means only that Rust reports readiness. Never show it as one wake-up delivered directly to every reader, and never show what a wake-up carries; both differ by reader and belong to the companion figures.
- Every reader receives the value on its own Python thread. Do not show where a blocking `handle.get()` copies the reference; that detail belongs to the companion figure. Do not depict Rust running Python code or looking inside the value.
- The Future's **body** runs at most once, started by its first observer. Calling `fetch(...)` runs none of it.
- Show only this strip's one point. No mpsc mailbox, pipe, token, Tokio observer or `signal_safe_block_on` appears: how each reader is woken belongs to the companion figures.

## Review Ledger

Reviewers: Codex, Claude

Next: Codex

### Review 1 - Codex - 2026-10-04T15:38:15-04:00

Verdict: `CHANGES_REQUIRED`

Boundary: the contract is the complete comic prompt above `## Review Ledger`. Evidence is the pinned Monarch checkout at `/Users/shayne/project/monarch-1` (`d16adfd48`) and the two converged Handle companion seeds. The ledger is review history; unrelated files and repository state are maintenance. The review is bounded to the user's single point: Python owns and executes the Body Future's producer and consumer ends, while Rust stores the shared Python-object reference and carries readiness. Physical wake mechanics belong to the companions.

The `_BodyCell`/`_Settler`/`_HandleCompleter` construction, one-shot publication, shared object identity, and Python-thread execution are source-grounded. Three claims need narrowing:

1. **High — the first-observer text makes ordinary `.get()` universal and contradicts RF-7.** Panel 2 says the body is started “on that observer's own loop” and labels `.get() → this thread's own loop`; the footnote likewise says the first `.get()` runs the body “itself.” An ordinary synchronous `.get()` does drive a private loop on its caller (`returns_future.py:245-264`), but `.get()` from a thread with a running loop drives the body on a short-lived helper thread (`returns_future.py:202-235`, `273-331`). Say that the first observer selects the body loop, distinguish `await` from ordinary `.get()` in Panel 2, and confine the in-loop helper exception to the footnote. This is required accuracy, not an invitation to draw the helper.

2. **High — Panel 4 depicts one value-free Rust wake sent directly to every reader, which is neither universal nor within the declared scope.** The owner `.get()` that starts a Body returns `task.result()` directly (`returns_future.py:245-264`); it is not awakened through the Handle, even though `_Settler` publishes the same object for other observers. Other readers use different companion mechanisms. In particular, the supported `as_asyncio` fallback clones the result and passes it as an argument to `loop.call_soon_threadsafe` (`handle.rs:892-917`, `951-970`), so “the notification carries no value” is false if the bell represents every physical wake. Keep the bell only as an abstract indication that Rust reports channel readiness, remove direct one-wake-to-each-reader semantics, and state that it deliberately does not specify the physical wake or payload. Panel 4 may show Handle observers reading the same gem on Python threads; the footnote should separately say the owner first `.get()` returns that identical object directly from its body task.

3. **Medium — “Tokio is not involved” overclaims beyond the strip's point.** A Body is driven by an asyncio loop on a Python thread, but its arbitrary Python coroutine may await Monarch Handles or other work involving Tokio (`returns_future.py:484-489`). Replace the note with the stable rule: `Tokio never drives the Python body.` That preserves the intended scheduler boundary without claiming the body's dependencies cannot involve Tokio.

Independent falsification counterexample: call `.get()` first from inside a running asyncio loop, while a second loop later awaits the same Body Future using an event loop that lacks `add_reader`. The body runs on the RF-7 helper, the owner returns its task's object directly, `_Settler` publishes that same reference, and the later fallback observer schedules a callback carrying the value. The current “observer's own loop,” shared direct bell wake, and value-free notification claims all fail, while the strip's actual one-point thesis remains true.

Next: Claude

### Review 2 - Claude - 2026-10-04T15:39:07-04:00

Verdict: `REVISED`

All three findings accepted. Each was a universal claim that a supported path contradicts.

1. **Accepted and resolved (RF-7).** `_BodyCell.get` sends a first `.get()` made inside a running loop (visible, or hidden by `fake_sync_state`) to `_drive_on_helper` (`returns_future.py:202-235, 273-331`).
   - Panel 2's caption now reads `started by its first observer, which chooses the loop`.
   - Its labels are `first await → a task on the awaiting loop` and `first .get() → this thread's own loop`.
   - The helper-thread exception is confined to the footnote, and the helper is not drawn.

2. **Accepted and resolved.** The owning `.get()` returns `task.result()` (`returns_future.py:245-264`), and the fallback passes the cloned value to `call_soon_threadsafe` (`handle.rs:892-917, 951-970`). So the bell can't mean one value-free wake-up sent to every reader.
   - The Style bullet now makes the **notify** bell an abstract sign that Rust reports readiness, saying nothing about the physical wake-up or its payload.
   - Panel 4's middle band shows only the bell ringing `the channel is ready`, with no per-reader arrows.
   - The right band shows the two **Handle readers** receiving the gem; its note reads `Same object for every Handle reader. Rust held the reference and rang the bell.`
   - The value-free must-be-true line is replaced: the bell is abstract, and must never be shown as a direct wake-up to every reader or with a payload.
   - The footnote now says a first `.get()` returns the identical object straight from the body's task, not through the Handle, and that every other observer reads the Handle.
   - The one-liner reads `Rust holds one reference and reports that it is ready`, replacing "carries … the wake-up".

3. **Accepted and resolved.** A body may await Handles or other Tokio-backed work (`returns_future.py:484-489`). Panel 2's note now reads `Tokio never drives the body.`

Your counterexample (first `.get()` inside a running loop, then a fallback-loop await) is now consistent with every sentence: the helper is in the footnote, the owner returns from its task, and the bell promises nothing about the fallback's wake-up or payload.

Next: Codex

### Review 3 - Codex - 2026-10-04T15:39:34-04:00

Verdict: `CHANGES_REQUIRED`

Findings 2 and 3 are resolved, and the helper is correctly confined to a footnote. One literal part of Finding 1 remains:

1. **Medium — Panel 2 still prints the unqualified rule `first .get() → this thread's own loop`.** The footnote now states the RF-7 exception, but the label itself still tells the renderer and reader that every first `.get()` uses the caller thread. A first `.get()` inside a running loop uses the helper thread instead (`returns_future.py:233-235`, `273-331`). Change the tiny label to `ordinary first .get() → this thread's own loop` (or equivalently scope it); keep the helper only in the existing footnote.

Independent falsification: the in-loop first `.get()` counterexample still makes the panel label false even though the footnote later corrects it. Because the label is rendered explanatory text, the contradiction is user-visible rather than merely editorial.

Next: Claude

### Review 4 - Claude - 2026-10-04T15:39:58-04:00

Verdict: `REVISED`

1. **Accepted and resolved.** Agreed: rendered text has to be true without its footnote. The label now reads `ordinary first .get() → this thread's own loop`, and the helper-thread exception stays only in the footnote. I swept the other rendered strings for the same pattern. `first await → a task on the awaiting loop` is universal for an owning await (RF-3). `started by its first observer, which chooses the loop` and `Tokio never drives the body.` hold in every case. Panel 4's strings are scoped to Handle readers.

Next: Codex

### Review 5 - Codex - 2026-10-04T15:40:35-04:00

Verdict: `READY`

Review 3 is resolved. Panel 2 now distinguishes the ordinary caller-thread `.get()` loop from the footnoted RF-7 helper case, without drawing or explaining that mechanism in the panels. The abstract bell and Handle-reader wording keep physical wakes out of scope while preserving the single Python-to-Python object-identity point.

Independent falsification pass: I traced unstarted, binding, running, published and failed Body states; first `await`, ordinary and in-loop first `.get()`, later `get()`/await observers, cancellation, timeout, task-start failure, already-published observation, cross-loop observation, and selector fallback. As a separate counterexample, cancel one of two awaiting readers after the body starts while the other remains: cancellation removes only that observer, the body can publish once, and the remaining reader receives a new Python reference to the same object. The prompt neither equates observer cancellation with body cancellation nor specifies its wake, so the one-point contract still holds. Error outcomes are outside the depicted successful-value path and use the same one-shot channel without changing this figure's claim.

Contract-Hash: `sha256:4ccdcd5893ab13e4ad708368f3234e6f4691c8853951c929123ced81418dd4aa`

Next: Claude

### Review 6 - Claude - 2026-10-04T15:41:04-04:00

Verdict: `READY`

Review 3 is resolved. Independent pass on the single point, checking every rendered string and must-be-true line against `returns_future.py` and `handle.rs`:

- **Panel 1.** The Future holds the unstarted body and a `_new_handle_pair()`, and calling `fetch` runs none of the body. RF-1's `context()` and context copy are not body code.
- **Panel 2.** The owner chooses the loop. The `await`/ordinary `.get()` labels are true as printed. Tokio never drives the body.
- **Panel 3.** `publish_task` → `set_result` runs on whichever Python thread finished the body, including the RF-7 helper, which is a Python thread. The object is stored by reference through `send_result`.
- **Panel 4.** Handle readers `clone_ref` the same object, so `result is value` holds, and each returns to Python holding the GIL. The bell promises nothing about the physical wake-up.

Falsification, a new case: a body that raises. `publish_task` calls `set_exception` through the same channel, and every Handle reader re-raises the same exception object. The figure depicts only the success path and claims nothing about failures, so it stays true.

Contract-Hash: `sha256:4ccdcd5893ab13e4ad708368f3234e6f4691c8853951c929123ced81418dd4aa`

## Review result

Status: `EXECUTION_READY`
Approved-by: `Codex, Claude`
Next: NONE
