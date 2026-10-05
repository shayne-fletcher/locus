# Fig 5: how a sync actor works

Seed for `images/fig-5-how-a-sync-actor-works.png`. Everything below the line is the complete prompt; paste it whole.

---

draw a standalone eight-panel comic explainer. its point is: **a sync actor has no persistent actor loop. one blocking driver owns the thread, runs actor work inline, gives callbacks priority between messages, starts or reuses a cached private asyncio loop during a nested `.get()`, and proves shutdown by running cleanup and then joining the Python thread.**

**Style.**
- use warm off-white paper, thick rounded dark ink, soft pastel blue, mint, lilac, peach, rose and butter yellow, and gentle shadows.
- use friendly, highly legible hand lettering. set code identifiers in monospace and spell them exactly.
- use a friendly blue-and-yellow snake tagged **sync actor OS thread** for the one driver thread. show the same snake in every panel where the thread appears.
- use a small lilac blob labelled **actor state** only where user code reads or changes actor state. it never represents a thread or loop.
- use a smiling orange cog only for Rust/Tokio actions such as classifying, enqueueing a callback, receiving an outcome, or joining. it never represents the Python driver thread.
- draw `_sync_dispatch_loop` as a labelled rose track controlled by the thread snake.
- draw an asyncio loop only as a separate mint-green rounded box labelled **RF-4 private loop**. never wrap the whole driver in that box.
- draw the message queue as orange envelope boxes, the callback queue as blue cards, and their shared wake pipe as one blue tube marked **1 byte**. the byte's value has no meaning.
- use a 1536 by 1024 px landscape canvas: title banner, four columns by two rows of numbered panels, and a wide one-liner box along the bottom.
- render each panel's short labels faithfully. draw schematic flows as diagrams, not as copied prose.

**Title banner:** `How a sync actor works`

**Panel 1: decide before spawn**
- show the Rust cog inspecting an actor class before a gate labelled `native spawn`.
- flow: `_actor_kind(Class)` -> `SYNC` -> `spawn`.
- beside the sync branch, show: `at least one endpoint; every endpoint is def; any hook overrides are def`.
- beneath `hooks`, list `__cleanup__`, `__supervise__`, and `_handle_undeliverable_message` in small monospace text.
- show a mismatched class stopped before the gate with `ValueError; no native actor created`.
- small note: `the kind chooses the runtime shape.`

**Panel 2: one thread, no actor loop**
- show `Actor::init` starting the snake tagged **sync actor OS thread**.
- the snake owns and walks the rose `_sync_dispatch_loop` track.
- place a crossed-out box labelled `TaskLocals / run_forever` outside the track.
- show the lilac **actor state** beside the track.
- small note: `__init__, endpoints, supervise and cleanup all enter here with no running loop.`

**Panel 3: two queues, one wake**
- an orange message envelope enters **message queue**, then writes **1 byte** to the shared blue pipe.
- a blue `callback` or `cleanup` card enters **callback queue**, then writes **1 byte** to the same pipe.
- `SyncInbox.next()` checks `1. callback` then `2. message`; if both are empty it releases the GIL and blocks in `poll(pipe)`.
- small note: `the queues carry the work; the pipe only says "look again."`

**Panel 4: a message runs inline**
- show the thread snake taking one orange envelope and moving through three boxes: `prepare` -> `endpoint(...)` -> `reply`.
- `endpoint(...)` is a plain call beside the lilac **actor state**, with no asyncio loop around it.
- under `reply`, show `resolve_and_send_blocking`; when reference resolution is pending, it waits through `Handle.get()`.
- small note: `one item at a time on one driver thread.`

**Panel 5: .get() borrows a loop**
- begin with the same thread snake inside `endpoint(...)`, holding a call card `body.get()`.
- show the separate mint box **RF-4 private loop** already attached to this thread and labelled `cached; idle`.
- `body.get()` starts or reuses that loop, runs `run_until_complete(body)`, receives `value`, then leaves the same loop attached and labelled `idle` while the endpoint continues.
- show no second snake and no helper thread.
- keep the mint box separate from `_sync_dispatch_loop`; never show it closing or disappearing.
- small note: `the cached private loop drives Python orchestration during .get(); it is not the actor dispatcher.`

**Panel 6: callback beats the backlog**
- show one active endpoint already in the thread snake's hands, followed by a tall orange message backlog.
- show the Rust cog enqueueing `PendingSupervision` on the callback queue and immediately returning; explicitly label `does not wait`.
- while an endpoint is active, order the driver steps as `finish active endpoint` -> `__supervise__` -> `next message`.
- after `__supervise__`, show `_handled` or `_raised` flowing into `SupervisionOutcome`, which returns to the Rust actor mailbox.
- small note: `the callback does not interrupt user code, but it runs before the next message.`

**Panel 7: user-code failures**
- show three clearly separated branches.
- branch A: `endpoint Exception` -> `error reply` -> `actor continues`.
- branch B: `__supervise__ Exception` -> `_raised` -> `failing SupervisionOutcome`.
- branch C: `endpoint or __supervise__ BaseException` -> `kill` -> `drain until cleanup`; cross out later orange messages but keep blue callback and cleanup cards moving. show `__init__ failure` joining this drain branch.
- small note: `Exception stays inside its boundary; BaseException kills and drains toward cleanup.`

**Panel 8: cleanup, join, return**
- show the Rust cog setting `stopping = true`; unclaimed callback cards are dropped, while a callback already claimed by the thread finishes first.
- show the Rust cog sending a blue `cleanup` card and waiting on its `Handle`.
- on the same thread snake: `finish active item` -> `__cleanup__` -> `complete Handle` -> `thread ends`.
- after that, show the Rust cog taking the Python driver `Thread` once and calling `Thread.join()` on Tokio's blocking pool, with the gold **GIL** token visibly set aside.
- final arrow: `Actor::cleanup returns` only after `thread ended`.
- small note: `cleanup orders user shutdown when the inbox works; Thread.join() proves termination.`

**The one-liner:** `One Python thread owns a sync actor: callbacks run between messages, .get() borrows its cached private loop, and stop returns only after Thread.join().`

**Must be true.**
- keep the sync actor OS thread, `_sync_dispatch_loop`, actor state, and RF-4 private loop as four distinct visual things.
- show exactly one Python OS thread. never add a helper thread, event-loop thread, or second snake.
- never place the whole driver inside an asyncio loop. the RF-4 private loop is cached on the thread, runs during `.get()`, and remains idle afterward.
- show callbacks and messages in separate queues that share one pipe. callbacks are checked first; the pipe byte carries no item identity.
- show send order as enqueue first, then write the pipe. do not depict the pipe as storing work.
- show a callback waiting for an active item, then running before the next message. do not depict preemption.
- never show Rust waiting for `__supervise__`; it enqueues and returns, and the verdict comes back later as `SupervisionOutcome`.
- distinguish endpoint `Exception`, `__supervise__ Exception`, and non-`Exception` `BaseException` exactly as Panel 7 specifies.
- keep cleanup on the same driver thread. show the order as cleanup completion, thread end, take the Python `Thread` exactly once, call `Thread.join()` on Tokio's blocking pool without the GIL, then return from `Actor::cleanup`.

**Notes (not for rendering).**
- user-created loops are outside the contract. the no-loop promise is that Monarch creates no persistent loop for a sync actor and enters its user code with no running loop.
- the pipe byte's value has no meaning; it is only a wake marker.
