# Jensen wake loss → Euclidean embedding

An interactive [marimo](https://marimo.io) notebook that visualises the idea in
`docs/idea.tex`. Starting from a wind-farm layout, it computes the Jensen
velocity-loss matrices and the Schoenberg-transformed distance matrix D. It then
recovers the points whose squared distances are D (classical MDS) and plots
them.

## Setup

You need [uv](https://docs.astral.sh/uv/getting-started/installation/). uv
installs a suitable Python (3.12 or later) and all the dependencies for you:

```sh
uv sync
```

This creates `.venv/` from `pyproject.toml` and `uv.lock`, so everyone gets
the same package versions.

## Run the notebook

```sh
uv run marimo run app.py     # app view: controls and plots only
uv run marimo edit app.py    # notebook view: also shows and lets you edit the code
```

Each command prints a local URL (usually http://localhost:2718); open it in a
browser.

- **Map:** drag turbines to move them, click empty space to add one, and
  right-click a turbine to remove it.
- **Controls:** the slider above the map sets the wind direction θ. The β
  slider and the preset dropdown are beside the map.
- **Updates:** plots recompute when you release the mouse.

The page has three sections:

1. **Loss matrices:** W, L = W + Wᵀ and D.
2. **Euclidean embedding:** the 3D view, then PCA (variance per axis,
   coordinates against position along the wind, and plots of pairs of
   coordinates).
3. **One new turbine:** where an extra turbine would land in the embedding for
   every position along the wind, and the max-sum objective.

## Tests

```sh
uv run pytest
```

The tests check:

- the W matrix for the 3-turbine example in the doc;
- that D is reproduced exactly by the recovered points;
- that the new-turbine curve is exact.

## Files

| File | Contents |
|---|---|
| `app.py` | The notebook: math functions, map widget, and plots |
| `test_embedding.py` | Tests for the math functions |
| `docs/idea.tex` | The write-up being visualised |
