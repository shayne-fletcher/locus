---
title: How Monarch's Python actors work
subtitle: The actor model
author: Shane Fletcher
---

A Python actor in [Monarch](https://github.com/meta-pytorch/monarch) spans two languages. Rust owns the mailbox; Python owns the loop.

![Rust owns the mailbox, Python owns the loop.](images/strip-1-python-actors.png)

Source: [`d16adfd48`](https://github.com/meta-pytorch/monarch/tree/d16adfd48f71dadbdcf2c92c7a3d0054bd323ce2). *Personal notes.*

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

`Counter` holds an integer `n`. The endpoint `incr(k)` adds `k` to `n` and replies with the result.

In general, let $S$ be the set of states an actor can be in, $M$ the set of messages it accepts, and $R$ the set of replies it can send. Handling one message is a function, which we call **step**: it takes the current state and a message, and returns the next state and a reply.

$$ \mathsf{step} : S \times M \to S \times R $$

![$\mathsf{step}$ as a string diagram. Wires are sets, wires side by side form a product, and the box is a function.](images/fig-1-1-step.png)

For `Counter`, a state is the integer $n$, a message is $\mathtt{incr}(k)$ for an integer $k$, and a reply is an integer:

$$ \mathsf{step}(n, \mathtt{incr}(k)) = (n + k,\ n + k) $$

A function of this shape, where the next state and the output both depend on the current state and the input, defines a **Mealy machine**: the standard model of a state machine that produces output ([Mealy, 1955](#ref-mealy)).

Here a reply is what the endpoint returns, which Monarch sends back on the message's response port. In general an endpoint can send any number of messages to any ports (`explicit_response_port=True` hands it the response port to use itself), so the output of a step is a set of sends; `return x` is the case of exactly one. This is the **actor model** ([Hewitt, 1973](#ref-hewitt); [Agha, 1986](#ref-agha)): on each message, an actor sends messages, creates actors, and becomes its next state.

Each actor gets [its own Python thread](https://github.com/meta-pytorch/monarch/blob/d16adfd48f71dadbdcf2c92c7a3d0054bd323ce2/monarch_hyperactor/src/actor.rs#L1729). Your `Counter` instance is [constructed there](https://github.com/meta-pytorch/monarch/blob/d16adfd48f71dadbdcf2c92c7a3d0054bd323ce2/python/monarch/_src/actor/actor_mesh.py#L1534), as the handling of the actor's first message, `__init__`, and never leaves. Rust's [`PythonActor`](https://github.com/meta-pytorch/monarch/blob/d16adfd48f71dadbdcf2c92c7a3d0054bd323ce2/monarch_hyperactor/src/actor.rs#L1066) holds a handle to the `_Actor` wrapper around it. The rest is plumbing around `step`, which never changes.

## A run is a fold

Give `Counter` a second endpoint, which sets `n` back to zero:

```python
    @endpoint
    def reset(self) -> int:
        self.n = 0
        return 0
```

An actor handles a sequence of messages $m_1, m_2, m_3, \ldots$ one at a time. Write $s_0$ for the state `__init__` leaves. Each step's next state is the following step's current state:

$$
\begin{aligned}
(s_1, r_1) &= \mathsf{step}(s_0, m_1) \\
(s_2, r_2) &= \mathsf{step}(s_1, m_2) \\
(s_3, r_3) &= \mathsf{step}(s_2, m_3)
\end{aligned}
$$

![Three steps composed along the state wire, from $s_0$ to $s_3$.](images/fig-2-1-fold.png)

Threading a state through a sequence like this is a **fold**. The replies $r_1, r_2, \ldots$ go out; the state stays inside.

Monarch's [`_dispatch_loop`](https://github.com/meta-pytorch/monarch/blob/d16adfd48f71dadbdcf2c92c7a3d0054bd323ce2/python/monarch/_src/actor/actor_mesh.py#L1398) is this loop, with batching removed. The state is never passed along because it lives in `self`:

```python
while True:
    msg = await receiver.recv()
    await _handle_queued_message(actor, msg)
```

> State is the fold of the messages handled so far.

**One at a time.** $s_2$ can't be computed until $s_1$ exists, so each handler finishes before the next message is taken.

**In order.** The same two messages, applied in either order to a state of 5:

$$
\begin{aligned}
\mathtt{incr}(1),\ \mathtt{reset}() &:\quad 5 \to 6 \to 0 \\
\mathtt{reset}(),\ \mathtt{incr}(1) &:\quad 5 \to 0 \to 1
\end{aligned}
$$

![The same two messages in either order, ending in different states.](images/fig-2-2-order.png)

The final states differ, so delivery must preserve order.

## References

- []{#ref-agha}G. Agha. [*Actors: A Model of Concurrent Computation in Distributed Systems*](https://doi.org/10.7551/mitpress/1086.001.0001). MIT Press, 1986.
- []{#ref-hewitt}C. Hewitt, P. Bishop and R. Steiger. [A universal modular ACTOR formalism for artificial intelligence](https://www.ijcai.org/Proceedings/73/Papers/027B.pdf). *IJCAI*, 1973.
- []{#ref-mealy}G. H. Mealy. [A method for synthesizing sequential circuits](https://doi.org/10.1002/j.1538-7305.1955.tb03788.x). *Bell System Technical Journal* 34(5), 1955.

<!-- To come, in order:
## Order            two FIFO hops; order-preserving maps compose
## Where code runs  every step labelled with its thread; Python objects only on the actor's thread
## The GIL is a token   invariants and induction; never on Tokio (#4938, #4991, pytokio removal)
## Waking up        happens-before; check-then-wait; wakes <= messages
## Two drivers      strip 2 whole; loop owns thread vs thread owns loop
## The same actor   observational equivalence for sync endpoints; what changes (supervision in the queue, get() without a helper thread)
## Afterword        the comics were diagrams
-->
