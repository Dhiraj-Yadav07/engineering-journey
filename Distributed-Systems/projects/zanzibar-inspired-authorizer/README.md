# Zanzibar-Inspired Authorizer

A small, educational authorization engine inspired by the core ideas behind Google's Zanzibar: relationship tuples, usersets, recursive permission evaluation, hierarchical relationships, and snapshot-based consistency.

This project is intentionally **not** a production reimplementation of Zanzibar. It is a focused system-design and implementation exercise for learning authorization architecture and distributed-systems trade-offs.

## 1. What this project demonstrates

The prototype currently demonstrates:

- Relationship tuples such as `document:design#viewer@user:alice`
- Direct user-to-resource relationships
- Userset relationships such as `document:design#viewer@group:engineering#member`
- Relation definitions through namespaces
- Userset expressions:
  - direct
  - union
  - intersection
  - exclusion
  - tuple-to-userset
- Recursive authorization checks
- Resource hierarchy, for example document -> folder
- Recursion protection with a visited set and maximum evaluation depth
- Versioned tuple visibility using `valid_from` and `valid_to`
- Snapshot-aware authorization checks
- A `ConsistencyToken` abstraction for carrying the requested authorization snapshot

## 2. Architecture

```text
                    Authorization Request
                            |
                            v
                 +-----------------------+
                 |      CheckEngine      |
                 |                       |
                 | ConsistencyToken      |
                 |       -> snapshot     |
                 +-----------+-----------+
                             |
                             v
                 +-----------------------+
                 | Expression Evaluator  |
                 |                       |
                 | Direct                |
                 | Union                 |
                 | Intersection          |
                 | Exclusion             |
                 | TupleToUserset         |
                 +-----------+-----------+
                             |
                             v
                 +-----------------------+
                 |      TupleStore       |
                 |                       |
                 | snapshot-aware reads  |
                 +-----------------------+
```

The current implementation keeps the consistency boundary simple:

```text
Client
  |
  | ConsistencyToken(snapshot_version=100)
  v
CheckEngine.check()
  |
  | snapshot_version = 100
  v
recursive evaluator
  |
  v
TupleStore.find(snapshot_version=100)
```

The same snapshot is used throughout one authorization evaluation.

## 3. Relationship tuple model

The conceptual tuple format is:

```text
<object_type>:<object_id>#<relation>@<subject>
```

Examples:

```text
document:design#viewer@user:alice
group:engineering#member@user:alice
document:design#viewer@group:engineering#member
document:design#parent@folder:engineering-docs
```

A tuple may also include:

- `subject_relation` for usersets
- `valid_from`
- `valid_to`

The latter two allow the store to answer:

> Is this relationship visible at authorization snapshot V?

## 4. Namespace and relation model

A namespace defines the relations that are valid for an object type.

For example:

```python
Namespace(
    name="document",
    relations={
        "viewer": RelationRule(
            "viewer",
            expression=Direct("viewer"),
        ),
    },
)
```

The evaluator resolves the relation rule and evaluates its expression against the tuple store.

## 5. Usersets

A userset represents a relationship derived through another object.

Example:

```text
document:design#viewer
    @group:engineering#member
```

means:

```text
Alice
  |
  | member
  v
Engineering group
  |
  | viewer
  v
Design document
```

Therefore a check for Alice as a document viewer can succeed without storing a direct:

```text
document:design#viewer@user:alice
```

tuple.

## 6. Hierarchical relationships

The prototype also supports tuple-to-userset evaluation.

Example:

```text
document:design#parent@folder:engineering-docs
folder:engineering-docs#viewer@group:engineering#member
group:engineering#member@user:alice
```

The authorization engine can evaluate:

```text
Is Alice a viewer of document:design?
```

by following:

```text
document
   |
   | parent
   v
folder
   |
   | viewer
   v
group userset
   |
   | member
   v
Alice
```

This demonstrates the important Zanzibar-style idea that authorization can be evaluated over a relationship graph.

## 7. Consistency and snapshots

Tuple records have temporal visibility:

```python
valid_from <= snapshot_version < valid_to
```

with `valid_to=None` representing an open-ended relationship.

For example:

```text
Bob viewer relationship
valid_from = 100
valid_to   = 105
```

produces:

```text
snapshot 100  -> ALLOW
snapshot 104  -> ALLOW
snapshot 105  -> DENY
```

The public authorization interface carries this snapshot through:

```python
ConsistencyToken(snapshot_version=104)
```

The evaluator converts the token to an internal snapshot value and uses the same snapshot throughout recursive evaluation.

## 8. Safety properties

The evaluator intentionally fails closed.

Important safeguards include:

### Default deny

If the namespace, relation, tuple, or relationship path cannot establish access, the result is `False`.

### Recursion protection

A visited-check key prevents repeatedly evaluating the same authorization state:

```text
(subject, subject_id, object, object_id, relation)
```

### Maximum depth

The evaluator has:

```python
MAX_DEPTH = 10
```

to bound recursive evaluation.

### Snapshot propagation

Recursive checks preserve the same snapshot version so that one authorization request does not combine relationship state from different logical versions.

## 9. Test coverage

The test suite currently covers the core behaviors, including:

- direct viewer access
- unknown user denial
- group membership authorization
- non-member denial
- namespace relation definitions
- intersection semantics
- exclusion semantics
- hierarchical folder/document access
- snapshot filtering in `TupleStore`
- end-to-end historical authorization checks
- `ConsistencyToken` behavior

Current checkpoint:

```text
13 passed
```

Run the suite with:

```powershell
python -m pytest
```

## 10. Repository structure

```text
zanzibar-inspired-authorizer/
├── docs/
│   ├── HLD.md
│   ├── data-model.md
│   └── failure-analysis.md
├── src/
│   └── zanzibar_authz/
│       ├── __init__.py
│       ├── expressions.py
│       ├── models.py
│       ├── namespace.py
│       ├── evaluator.py
│       └── store.py
├── tests/
│   └── test_check.py
├── pyproject.toml
└── README.md
```

## 11. Running locally

From the project directory:

```powershell
python -m pip install -e .
python -m pytest
```

The project targets Python 3.11 or newer.

## 12. What is intentionally out of scope

This project does not attempt to implement the full distributed Zanzibar architecture.

Not implemented:

- Spanner or another distributed transactional database
- multi-region replication
- distributed consensus
- external change-log / watch infrastructure
- Leopard-style specialized indexing
- production sharding
- a production HTTP service
- globally distributed caching
- TrueTime-style external consistency

These are addressed as architecture and failure-analysis topics rather than code.

## 13. Production evolution

A production-oriented design could evolve from this prototype as follows:

```text
                +----------------------+
                | Authorization API    |
                +----------+-----------+
                           |
                           v
                +----------------------+
                | Decision Cache       |
                | version-aware        |
                +----------+-----------+
                           |
                           v
                +----------------------+
                | Check / Graph Engine |
                +----------+-----------+
                           |
             +-------------+-------------+
             |                           |
             v                           v
     Consistent Datastore         Namespace Config
             |
             v
       Change / Watch Path
             |
             v
        Distributed Replicas
```

The production design would need stronger guarantees around transactional writes, replication, cache invalidation, serving freshness, and operational observability.

## 14. Interview explanation

A concise explanation of the project is:

> I built a small Zanzibar-inspired authorization engine using relationship tuples and recursive userset evaluation. The engine supports direct, group-derived, and hierarchical permissions, plus union, intersection, and exclusion semantics. I then added versioned tuple visibility and a consistency-token abstraction so an authorization decision can be evaluated against a specific logical snapshot. The implementation is intentionally small; distributed storage, replication, and large-scale caching are discussed as production evolution rather than simulated in code.

## 15. Key design lessons

The main lessons demonstrated by the project are:

1. Authorization can be modeled as a relationship graph rather than hard-coded application logic.
2. Recursive graph evaluation requires explicit cycle and depth safeguards.
3. A consistent authorization decision needs a well-defined snapshot/freshness contract.
4. Cache correctness depends on the version/freshness semantics of the underlying authorization state.
5. A learning prototype should isolate the core authorization semantics from production-scale distribution mechanisms.

## 16. Current status

**Core Zanzibar-inspired authorization model:** complete

**Consistency/snapshot model:** complete

**Production distributed infrastructure:** intentionally out of scope

The project is now best treated as an interview-oriented implementation artifact and a foundation for discussing how a real Zanzibar-like authorization service would scale.
