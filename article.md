---
title: How Monarch's Python actors work
subtitle: In pictures and a little mathematics
author: Shane Fletcher
---

A Python actor in [Monarch](https://github.com/meta-pytorch/monarch) spans two languages. Rust owns the mailbox; Python owns the loop.

![Rust owns the mailbox, Python owns the loop.](images/strip-1-python-actors.png)

Each section below takes one idea from the strip and states it exactly. Source links are pinned to [`d16adfd48`](https://github.com/meta-pytorch/monarch/tree/d16adfd48f71dadbdcf2c92c7a3d0054bd323ce2). *Personal notes, not an official Monarch or Meta publication.*

## An actor is a step

```python
from monarch.actor import Actor, endpoint

class Counter(Actor):
    def __init__(self):
        self.n = 0

    @endpoint
    def incr(self, k: int) -> int:
        self.n += k
        return self.n
```

Let $S$ be the actor's states, $M$ its messages, $R$ its replies. The actor is one function:

$$ \mathsf{step} : S \times M \to S \times R $$

![The step box.](images/fig-1-1-step.png)

For `Counter`, $S = R = \mathbb{Z}$ and $\mathsf{step}(n, \mathtt{incr}(k)) = (n + k,\ n + k)$. An exception raised by an endpoint is in $R$: it is pickled and fails the caller's future.

A state machine whose output depends on state and input is a **Mealy machine**. Curried, $S \to (M \to S \times R)$: each state is a menu of responses, a **coalgebra**.

The object is constructed once, on its own Python thread, and never moves; Rust's [`PythonActor`](https://github.com/meta-pytorch/monarch/blob/d16adfd48f71dadbdcf2c92c7a3d0054bd323ce2/monarch_hyperactor/src/actor.rs#L1066) holds a handle to it. Everything else is plumbing around `step`: delivering $m$, returning $r$, choosing the thread that calls it. `step` itself never changes, which is why sync and async actors turn out to be the same actor.

Real endpoints have effects (other actors, tensors, GPUs), so `step` is really a computation yielding $S \times R$. The shape is unchanged.

## A run is a fold

Add a second endpoint:

```python
    @endpoint
    def reset(self) -> int:
        self.n = 0
        return 0
```

From the state $s_0$ left by `__init__`, each step feeds the next:

$$
\begin{aligned}
(s_1, r_1) &= \mathsf{step}(s_0, m_1) \\
(s_2, r_2) &= \mathsf{step}(s_1, m_2) \\
(s_3, r_3) &= \mathsf{step}(s_2, m_3)
\end{aligned}
$$

![The fold.](images/fig-2-1-fold.png)

A fold that emits at each step is `mapAccumL`: replies out, state private.

```python
def run(step, s, msgs):
    for m in msgs:
        s, r = step(s, m)
        yield r
```

Monarch's [`_dispatch_loop`](https://github.com/meta-pytorch/monarch/blob/d16adfd48f71dadbdcf2c92c7a3d0054bd323ce2/python/monarch/_src/actor/actor_mesh.py#L1398), batching removed, is the same loop. The state lives in `self`; the actor object is the accumulator.

```python
while True:
    msg = await receiver.recv()
    await _handle_queued_message(actor, msg)
```

The stream never ends, but every prefix has a fold:

> The actor's state is the fold of the messages handled so far.

This demands two things.

**One at a time.** $s_2$ depends on $s_1$, so each handler completes before the next `recv`.

**Order.** From $s_0 = 5$:

$$
\begin{aligned}
\mathtt{incr}(1),\ \mathtt{reset}() &:\quad 5 \to 6 \to 0 \\
\mathtt{reset}(),\ \mathtt{incr}(1) &:\quad 5 \to 0 \to 1
\end{aligned}
$$

![Order matters.](images/fig-2-2-order.png)

Order is part of a message's meaning, so delivery must preserve it.

<!-- To come, in order:
## Order            two FIFO hops; order-preserving maps compose
## Where code runs  every step labelled with its thread; Python objects only on the actor's thread
## The GIL is a token   invariants and induction; never on Tokio (#4938, #4991, pytokio removal)
## Waking up        happens-before; check-then-wait; wakes <= messages
## Two drivers      strip 2 whole; loop owns thread vs thread owns loop
## The same actor   observational equivalence for sync endpoints; what changes (supervision in the queue, get() without a helper thread)
## Afterword        the comics were diagrams
-->
