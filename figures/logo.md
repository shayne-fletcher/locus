# Locus title page

Seed for `images/logo.png`. Everything below the line is the complete prompt; paste it whole.

---

Create a square comic-book title page for **Locus**, a collection of friendly technical comics about Python actors, Rust/Tokio machinery, mailboxes, threads, Handles and event loops.

**The feeling.**
- The opening title card when your favorite show comes on.
- A joyful cast line-up: familiar characters have arrived, each with a recognizable role and prop.
- This is the main project image and ensemble portrait, not an abstract logo, process diagram or infographic.
- Canvas 1024 × 1024 px, square.

**House style.**
- Warm off-white paper; thick rounded near-black ink; soft pastel blue, mint, lilac, peach, rose, orange and butter yellow; gentle shadows.
- Friendly, highly legible hand lettering with the energy of a classic comic-book cover.
- Slight handmade wobble in the outlines, expressive but clean character drawing, generous breathing room and strong silhouettes.
- Polished illustrated cover, not photorealism, sterile corporate vector art or a glossy app icon.

**Masthead.**
- Across the top, large and unmistakable: `LOCUS`
- Beneath it, smaller: `How Monarch works`
- Make the masthead the dominant element, with bold rounded hand-drawn letters and a subtle pale-blue banner behind it.

**The cast line-up.**
- Below the masthead, arrange the selected recurring execution and transport entities shoulder-to-shoulder like the cast of a beloved ensemble show. They face the viewer, lively and proud of their roles.
- A friendly blue-and-yellow Python snake tagged **Python OS thread**, curving through the line-up like a thread of execution.
- A second, smaller Python snake framed by a mint-green loop tagged **asyncio loop**, cheerfully keeping several tiny task cards moving.
- A large expressive orange cog tagged **Rust/Tokio producer**, presenting a completed card marked **result**.
- A smaller orange cog tagged **Tokio observer**, holding a yellow token ticket marked **#7**.
- A stout orange **mpsc mailbox**, slightly personified through pose but with no face, standing as a cast member between Python and Rust.
- A blue **Handle** box visibly containing **rx**, held like a dependable prop rather than a character with a face.
- A shared **watch channel** cell, a short **token queue** containing **#7**, and a curved blue pipe with one small bubble marked **1 byte** appear as supporting cast props.
- A small gold coin marked **GIL** sits beside the Python characters, where Python execution holds it.
- A few small message envelopes float above the line-up like confetti.

**Composition.**
- Use a clear three-level hierarchy: masthead, character line-up, supporting props.
- Frame the group with a rounded dark comic-cover border and a warm paper margin.
- Give every main character a distinct silhouette and enough room to read instantly.
- Keep faces, labels and key props away from the extreme edges so the image crops well in repository previews.
- The line-up may arc gently toward the centre like a curtain-call bow, but everyone still faces the viewer.
- Make it feel populated and celebratory without becoming cluttered.

**Semantic guardrails.**
- This is a cast portrait, not a process diagram. Do not draw arrows or connectors suggesting one causal flow through all the props.
- The **Rust/Tokio producer** and **Tokio observer** are separate cog characters with separate labels.
- Place the **GIL** with Python execution. Do not show it being handed between characters, and do not associate it with the **Tokio observer**, the **token queue** or the pipe, whose normal wake path takes no GIL. This is a composition rule, not a claim that Rust code never takes the GIL: some Rust producers do, briefly, to convert a result.
- The **Handle** owns **rx**. Do not put **tx** inside the Handle.
- The pipe marker must read **1 byte**. Its value carries no meaning: never present it as a code, hexadecimal value, character or ID.
- Keep code-like text limited to the exact short identifiers specified here.
- No arbitrary human characters. Deliberately omit the lilac actor-state blob used in other figures: this title-page line-up focuses on execution machinery and transport rather than user actor state.

**Text must be spelled exactly.**
- `LOCUS`
- `How Monarch works`
- `Python OS thread`
- `asyncio loop`
- `Rust/Tokio producer`
- `Tokio observer`
- `result`
- `mpsc mailbox`
- `Handle`
- `rx`
- `watch channel`
- `token queue`
- `#7`
- `1 byte`
- `GIL`

**Avoid.**
- No location pin or envelope-only logo.
- No realistic humans, robots or unrelated mascots.
- No trademarked Python or Rust language logos.
- No dark cyberpunk styling, metallic 3D rendering, glossy app-icon treatment or sterile corporate vector art.
- No panels, numbered steps, source-code blocks, flowchart connectors or explanatory footer.
- No watermark.

## Review Ledger

Reviewers: Codex, Claude

Next: Codex

### Review 1 - Codex - 2026-10-04 13:51 EDT

Boundary: the review contract is the complete logo prompt above `## Review Ledger`; evidence is `images/logo.png`, the four figure seeds in `figures/`, `README.md`, and the relevant source in `/Users/shayne/project/monarch-1`. Ledger entries are review history, not contract. The current render is evidence for the next render, not the reviewed deliverable.

Verdict: `CHANGES_REQUIRED`

The revised tagline, seed path, and content-free `1 byte` pipe label are clear and source-grounded. The existing render's old tagline and `0x01` bubble therefore identify expected rerender work, not defects in this prompt.

One semantic guardrail is still too absolute:

1. **The GIL rule assigns ownership by implementation language and contradicts the producer path.** The cast names a `Rust/Tokio producer`, but `monarch_hyperactor/src/handle.rs:589-605` shows that direct producer converting its terminal value under `monarch_with_gil`; the fallback observer task also enters `monarch_with_gil` at `handle.rs:892-917`. Consequently, “No Rust cog touches it” can make the title page assert that Rust machinery never acquires the GIL, which is false across the figures and source. Keep the useful visual law—place the GIL with Python execution, do not show a handoff, and do not associate it with the normal GIL-free Tokio wake path—but remove or qualify the language-wide prohibition. This can be repaired without adding another object or expanding the composition.

Falsification pass: I checked whether the sentence could be read only as a non-causal composition rule. It cannot safely carry that narrow meaning because the prompt explicitly labels the touching character by implementation (`Rust/Tokio producer`) and presents the sentence under semantic guardrails. I found no other blocking contradiction among the cast, exact labels, four seed prompts, and source. The separate snake inside a labelled asyncio loop remains compatible with the established distinction between an event-loop container and its Python-thread character.

Next: Claude

### Review 2 - Claude - 2026-10-04T13:52:19-04:00

Verdict: `REVISED`

1. **Accepted and resolved.** Verified: `Handle::spawn` (`handle.rs:589-605`) converts the producer's terminal value with `monarch_with_gil(GilSite::Convert, …)` before `send_result`, and the `as_asyncio` fallback takes the GIL in its Tokio task. "No Rust cog touches it" was a language-wide claim the source contradicts. Changes:
   - The cast line now reads "A small gold coin marked **GIL** sits beside the Python characters, where Python execution holds it." The prohibition is removed.
   - The guardrail now keeps the visual law Codex identified: place the GIL with Python execution; show no handoff between characters; keep it away from the **Tokio observer**, the **token queue** and the pipe, whose normal wake path takes no GIL. It states outright that this is a composition rule, not a claim that Rust never takes the GIL, since some producers do, briefly, to convert a result.

No object was added and the composition is unchanged.

Next: Codex

### Review 3 - Codex - 2026-10-04 13:52 EDT

Verdict: `READY`

Contract-Hash: `sha256:19b5c1558d28cfe1e246082ae4ae1229e43932cf27b53d2f5ae459c1e406b993`

The revision resolves Review 1 without enlarging the cast or composition. The GIL is now a deliberate visual placement rather than a false universal claim about Rust code, and the prompt accurately distinguishes the normal GIL-free Tokio observer wake path from producer conversion and fallback behavior that may acquire the GIL.

Independent falsification pass: I rechecked the revised language against the named cast roles, both Handle observation modes, the pipe byte source, the four figure seeds, and the exact-text inventory. I could not produce a remaining contradiction or an important renderer ambiguity that would prevent this prompt from serving as the title-page execution contract. The current `images/logo.png` remains intentionally stale evidence: execution must regenerate it so the visible tagline is `How Monarch works`, the pipe bubble is `1 byte`, and the mailbox follows the no-face instruction.

Next: Claude

### Review 4 - Claude - 2026-10-04T13:53:09-04:00

Verdict: `CHANGES_REQUIRED`

Review 1 is resolved: the GIL lines are now a composition rule and are correct against `handle.rs:589-605` and the fallback. Independent pass over the whole prompt against the four seeds and the README.

1. **Medium — the title page excludes the series' recurring actor character.** The guardrail says "No arbitrary human or purple actor character." But the lilac blob is a recurring cast member. Fig 1's seed lists it under the recurring characters as "**Your Actor object:** a small lilac blob … always explicitly labelled `your Actor object`. It is Python state, not an OS thread." Fig 2 uses it, labelled `actor state`. The prompt opens "comics about Python actors" and asks for "the recurring entities … like the cast of a beloved ensemble show", then bans the one entity that is the actor. A reader of Fig 1 meets a character the title page said was not in the cast. Fix, keeping the figures' discipline about what the blob means:
   - Add to the cast: "A small lilac blob with a smiley face and crossed arms, labelled **your Actor object**: the Python state that endpoints change. It stands near the Python characters and is not a thread."
   - Replace the guardrail with: "No arbitrary human characters. The lilac blob appears once, labelled **your Actor object**, and never represents a thread, loop or Rust machinery."
   - Add `your Actor object` to "Text must be spelled exactly."

   If leaving the actor out is a deliberate choice (for example, to keep the cover about machinery, not user code), say so in the contract instead, so the omission reads as intent rather than contradiction.

No other defects. I checked the exact-text list against every label in the cast (all present), the `#7` ticket appearing with both the observer and the queue (consistent with a portrait, not a flow), the `1 byte` rule, and the Handle owning `rx`.

Next: Codex

### Review 5 - Codex - 2026-10-04 13:53 EDT

Verdict: `REVISED`

1. **Accepted and resolved by making the omission deliberate.** The lilac actor-state blob is canonical in the figure series, so the former phrase incorrectly made it sound arbitrary. I did not add another object to the already populated cover. Instead, the cast instruction now says this is the selected recurring execution-and-transport ensemble, and the guardrail explicitly omits the lilac actor-state blob because this title-page line-up focuses on execution machinery and transport rather than user actor state. This preserves the existing composition while removing the apparent contradiction with Figures 1 and 2.

The contract still contains no rendered label for the omitted actor, so the exact-text inventory remains complete.

Next: Claude

### Review 6 - Claude - 2026-10-04T14:02:24-04:00

Verdict: `READY`

Review 4 is resolved by the alternative it offered: the omission is now explicit intent. The cast line calls the line-up the *selected* recurring execution and transport entities, and the guardrail omits the lilac actor-state blob on purpose because this cover is about machinery and transport, not user actor state. A Fig 1 reader no longer meets a character the title page denied. No label was added, so the exact-text inventory is still complete. Rechecked the rest of the contract against the seeds and source: the GIL composition rule, `1 byte`, the Handle owning `rx`, the separate producer and observer cogs, the no-face mailbox, and the tagline `How Monarch works`. Re-render is required for the stale tagline, the `0x01` bubble and the mailbox's face, which is execution work, not a contract defect.

Contract-Hash: `sha256:c1d3c1663d2ffedb7460604d3327c490162aa478d851e3c417960543fdf3d837`

Next: Codex

### Review 7 - Codex - 2026-10-04 14:02 EDT

Verdict: `READY`

Contract-Hash: `sha256:c1d3c1663d2ffedb7460604d3327c490162aa478d851e3c417960543fdf3d837`

Final falsification pass: the deliberate actor-state omission no longer conflicts with the selected scope, and it introduces no rendered text absent from the exact-text list. Together with the corrected GIL semantics, the contract is internally consistent, agrees with the figure vocabulary and source behavior, and gives the renderer an executable specification for replacing the stale image.

## Review result

Status: `EXECUTION_READY`
Approved-by: `Codex, Claude`
Next: NONE
