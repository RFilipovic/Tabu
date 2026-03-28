# hotstorage-tabu-search

Bachelor's thesis project — an extension of [hotstorage-simulator](https://github.com/RFilipovic/hotstorage-simulator) that applies a **specialised Tabu Search metaheuristic** to experimentally find optimal (or near-optimal) crane scheduling solutions for a hot storage buffer system.

The simulator core is written in C++ and reused from the original project. The Tabu Search optimiser is implemented in Python and drives the simulation iteratively, searching the solution space for the best possible container scheduling order.

---

## Background

In hot storage management, containers stacked in buffers must be retrieved and moved by a crane before their due times. The order in which the crane services containers significantly affects total completion time and the number of deadline violations. The original [hotstorage-simulator](https://github.com/RFilipovic/hotstorage-simulator) evaluates a given schedule — this project adds an optimisation layer on top of it.

**Tabu Search** is a metaheuristic that explores the neighbourhood of a current solution, accepts moves even when they don't immediately improve the result (to escape local optima), and maintains a *tabu list* of recently visited solutions to prevent cycling. Over many iterations it converges on a high-quality solution without needing to exhaustively enumerate the search space.

---

## Repository Structure

```
hotstorage-tabu-search/
├── simulator/        # C++ simulator (adapted from hotstorage-simulator)
├── tabu-search/      # Python Tabu Search implementation
├── primjeri/         # Example input instances for testing
└── README.md
```

- **`simulator/`** — the C++ hot storage simulator, compiled as a library or executable. Evaluates a given container schedule and returns a cost (e.g. total crane operation time or number of late retrievals).
- **`tabu-search/`** — the Python optimiser. Generates candidate schedules, passes them to the simulator, reads back the cost, and uses Tabu Search logic to guide the next iteration.
- **`primjeri/`** — a collection of example problem instances (input files in the same format as `ulaz.txt` from the original simulator) used for benchmarking and experimentation.

---

## How It Works

```
┌─────────────────────────────┐
│   Tabu Search (Python)      │
│                             │
│  1. Generate initial        │
│     schedule                │
│  2. Evaluate via simulator  │◄──┐
│  3. Explore neighbourhood   │   │
│  4. Apply tabu list         │   │
│  5. Accept best non-tabu    │   │
│     move                    │───┘
│  6. Update best solution    │
│  7. Repeat until stopping   │
│     criterion met           │
└────────────┬────────────────┘
             │ writes input / reads output
             ▼
┌─────────────────────────────┐
│   C++ Simulator             │
│   (hotstorage-simulator)    │
│   Evaluates a schedule →    │
│   returns cost              │
└─────────────────────────────┘
```

The Python layer treats the C++ simulator as a **black-box cost function** — it constructs an input file, invokes the simulator, and parses the output to extract the objective value. This keeps the simulation logic unchanged and separates the optimisation concern cleanly.

---

## Requirements

**Simulator (C++):**
- C++17 or later
- `make` (Makefile-based build)
- A C++ compiler (e.g. `g++`)

**Tabu Search (Python):**
- Python 3

---

## Building the Simulator

```bash
cd simulator
make
```

This produces the simulator executable used by the Python optimiser to evaluate candidate solutions.

---

## Running the Tabu Search

```bash
cd tabu-search
python3 tabu_search.py
```

The optimiser will read a problem instance from the `primjeri/` directory (or a configured input path), run the Tabu Search loop, and output the best schedule found along with its cost.

---

## Example Instances

The `primjeri/` directory contains ready-to-use problem instances. The input format follows the same structure as the original `hotstorage-simulator`:

```
<BUFFER SIZE>10</BUFFER SIZE>
<CLEARING TIME>01:00</CLEARING TIME>
<CRANE LIFT>0:1</CRANE LIFT>
<CRANE MOVE>0:2</CRANE MOVE>
<CRANE LOWER>0:1</CRANE LOWER>
A0|B0|B1|B2|H0
B98(3:28)|B76(0:26)|...
```

---

## Relation to hotstorage-simulator

This project depends on and extends [hotstorage-simulator](https://github.com/RFilipovic/hotstorage-simulator). The simulator library provides the evaluation engine; this repo adds the search strategy on top. If you want to understand the problem domain or the simulator internals, start with the original repository first.

---

## License

Not specified. Contact the repository owner for usage terms.
