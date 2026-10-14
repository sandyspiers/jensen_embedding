import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")

with app.setup:
    import anywidget
    import marimo as mo
    import numpy as np
    import plotly.graph_objects as go
    import traitlets
    from plotly.subplots import make_subplots

    # Categorical palette, one fixed hue per turbine (T1..T8); later turbines are grey, identified by label.
    TURBINE_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
    OTHER_COLOR = "#898781"
    HEAT = [[0, "#fcfcfb"], [0.15, "#cde2fb"], [0.5, "#5598e7"], [1, "#0d366b"]]
    PC_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#6250d6"]
    EXTENT = 2000.0  # map half-width (m)

    PRESETS = {
        "Doc example: 3 in a row": [[0, 0], [-500, -866], [-1000, -1732]],
        "4 turbines": [[-900, 300], [100, 800], [600, -500], [-300, -1100]],
        "3x3 grid": [[x, y] for y in (-700, 0, 700) for x in (-700, 0, 700)],
        "Row of 8": [[x, 150 * (i % 2)] for i, x in enumerate(range(-1400, 1401, 400))],
        "12 scattered": np.random.default_rng(7).uniform(-1600, 1600, (12, 2)).round().tolist(),
        "100 scattered": np.random.default_rng(100).uniform(-1800, 1800, (100, 2)).round().tolist(),
    }

    class LayoutWidget(anywidget.AnyWidget):
        """Draggable turbine map; syncs turbine positions (m) and wind direction (deg)."""

        turbines = traitlets.List().tag(sync=True)
        theta = traitlets.Float(240.0).tag(sync=True)
        _esm = """
        const E = 2000, R = 70, NS = "http://www.w3.org/2000/svg";
        const COLORS = %s, OTHER = "%s";
        function render({ model, el }) {
          el.innerHTML = `<div style="font:13px system-ui;width:420px;max-width:100%%">
            <label>Wind direction θ = <b class="tv"></b>° (towards, anticlockwise from +x)
              <input type="range" min="0" max="359" step="1" style="width:100%%"></label>
            <svg viewBox="${-E} ${-E} ${2*E} ${2*E}" style="width:100%%;aspect-ratio:1;touch-action:none;
              background:#fcfcfb;border:1px solid #e1e0d9;border-radius:6px;user-select:none"></svg>
            <div style="color:#52514e">Drag to move · click empty space to add · right-click to remove · grid 500 m</div>
          </div>`;
          const svg = el.querySelector("svg"), slider = el.querySelector("input"), tv = el.querySelector(".tv");
          let pts = model.get("turbines").map(p => [...p]), theta = model.get("theta"), drag = null;
          const mk = (tag, attrs) => {
            const e = document.createElementNS(NS, tag);
            for (const k in attrs) e.setAttribute(k, attrs[k]);
            svg.appendChild(e); return e;
          };
          const clamp = v => Math.max(-E + R, Math.min(E - R, v));
          const toWorld = ev => {
            const p = svg.createSVGPoint(); p.x = ev.clientX; p.y = ev.clientY;
            const q = p.matrixTransform(svg.getScreenCTM().inverse());
            return [clamp(Math.round(q.x)), clamp(Math.round(-q.y))];
          };
          function draw() {
            svg.replaceChildren(); tv.textContent = theta; slider.value = theta;
            for (let v = -E + 500; v < E; v += 500) {
              mk("line", { x1: v, y1: -E, x2: v, y2: E, stroke: "#e1e0d9", "stroke-width": 6 });
              mk("line", { x1: -E, y1: v, x2: E, y2: v, stroke: "#e1e0d9", "stroke-width": 6 });
            }
            const t = theta * Math.PI / 180, w = [Math.cos(t), Math.sin(t)];
            const L = 0.95 * E / Math.max(Math.abs(w[0]), Math.abs(w[1]));
            mk("line", { x1: -L * w[0], y1: L * w[1], x2: L * w[0], y2: -L * w[1], stroke: "#898781", "stroke-width": 14 });
            const tip = [L * w[0], -L * w[1]], n = [-w[1], -w[0]], b = 140;
            mk("polygon", { fill: "#898781", points: [tip,
              [tip[0] - b * w[0] + 0.5 * b * n[0], tip[1] + b * w[1] + 0.5 * b * n[1]],
              [tip[0] - b * w[0] - 0.5 * b * n[0], tip[1] + b * w[1] - 0.5 * b * n[1]]].join(" ") });
            const s = pts.map(p => p[0] * w[0] + p[1] * w[1]);
            const color = pts.map((_, i) => COLORS[i] ?? OTHER);
            pts.forEach((p, i) => {
              const f = [s[i] * w[0], -s[i] * w[1]];
              mk("line", { x1: p[0], y1: -p[1], x2: f[0], y2: f[1], stroke: color[i], "stroke-width": 8, "stroke-dasharray": "40 30" });
              mk("circle", { cx: f[0], cy: f[1], r: 28, fill: color[i] });
            });
            pts.forEach((p, i) => {
              const c = mk("circle", { cx: p[0], cy: -p[1], r: R, fill: color[i], stroke: "#fcfcfb", "stroke-width": 16, style: "cursor:grab" });
              c.dataset.i = i;
              const lbl = mk("text", { x: p[0] + 1.2 * R, y: -p[1] - 1.2 * R, "font-size": 150, fill: "#0b0b0b", "pointer-events": "none" });
              lbl.textContent = "T" + (i + 1);
            });
          }
          function commit() { draw(); model.set("turbines", pts.map(p => [...p])); model.save_changes(); }
          svg.addEventListener("pointerdown", ev => {
            if (ev.button !== 0) return;
            const i = ev.target.dataset?.i;
            if (i !== undefined) { drag = +i; svg.setPointerCapture(ev.pointerId); }
            else { pts.push(toWorld(ev)); commit(); }
          });
          svg.addEventListener("pointermove", ev => { if (drag !== null) { pts[drag] = toWorld(ev); draw(); } });
          svg.addEventListener("pointerup", () => { if (drag !== null) { drag = null; commit(); } });
          svg.addEventListener("contextmenu", ev => {
            ev.preventDefault();
            const i = ev.target.dataset?.i;
            if (i !== undefined && pts.length > 2) { pts.splice(+i, 1); commit(); }
          });
          slider.addEventListener("input", () => { theta = +slider.value; draw(); });
          slider.addEventListener("change", () => { model.set("theta", theta); model.save_changes(); });
          model.on("change:turbines", () => { pts = model.get("turbines").map(p => [...p]); if (drag === null) draw(); });
          model.on("change:theta", () => { theta = model.get("theta"); draw(); });
          draw();
        }
        export default { render };
        """ % (str(TURBINE_COLORS), OTHER_COLOR)


@app.function
def wind_vector(theta_deg):
    """Unit wind vector w_theta, eq. (wind-unit-vector)."""
    t = np.deg2rad(theta_deg)
    return np.array([np.cos(t), np.sin(t)])


@app.function
def jensen_loss(d, beta):
    """Normalised Jensen velocity loss l(d) = 2/3 (1 + beta d)^-2."""
    return 2 / 3 * (1 + beta * d) ** -2


@app.function
def wake_matrix(s, beta):
    """Directed wake matrix W, eq. (loss-matrix-entrywise), every downstream turbine in the wake."""
    d = s[None, :] - s[:, None]  # d_ij = s_j - s_i
    return np.where(d > 0, jensen_loss(np.abs(d), beta), 0.0)


@app.function
def schoenberg_D(s_a, s_b, beta):
    """D_ij = f(T_ij) = 2/3 [1 - (1 + beta |s_i - s_j|)^-2], eq. (transformed Jensen distance)."""
    return 2 / 3 - jensen_loss(np.abs(s_a[:, None] - s_b[None, :]), beta)


@app.function
def classical_mds(D, tol=1e-12):
    """Points Z with ||z_i - z_j||^2 = D_ij from B = -1/2 HDH (Lemma: EDM characterisation).

    Returns (Z, lam): Z has one column per positive eigenvalue, PCA-ordered,
    each column's largest-|.| entry made positive; lam are all eigenvalues, descending.
    """
    n = len(D)
    H = np.eye(n) - 1 / n
    lam, U = np.linalg.eigh(-0.5 * H @ D @ H)
    lam, U = lam[::-1], U[:, ::-1]
    keep = lam > tol * max(lam[0], 0) if lam[0] > 0 else np.zeros(n, bool)
    Z = U[:, keep] * np.sqrt(lam[keep])
    Z *= np.sign(Z[np.abs(Z).argmax(0), np.arange(Z.shape[1])])
    return Z, lam


@app.function
def add_point(s_existing, s_new, beta):
    """Exact embedding of one extra turbine at each position in s_new (Gower's formula).

    Returns (Y, x_par, h): Y embeds the existing turbines; for each new position,
    x_par is its coordinate in Y's span and h its height along one new orthogonal
    axis, so that [x_par, h] is exactly at squared distance D from every row [Y, 0].
    """
    Y, lam = classical_mds(schoenberg_D(s_existing, s_existing, beta))
    d = schoenberg_D(s_new, s_existing, beta)
    r2 = (Y**2).sum(1)
    a = -0.5 * (d - d.mean(1, keepdims=True) - r2 + r2.mean())
    x_par = a @ Y / lam[: Y.shape[1]]
    h = np.sqrt(np.clip(d.mean(1) - r2.mean() - (x_par**2).sum(1), 0, None))
    return Y, x_par, h


@app.function
def turbine_colors(n):
    return [TURBINE_COLORS[i] if i < len(TURBINE_COLORS) else OTHER_COLOR for i in range(n)]


@app.cell
def _():
    mo.md(r"""
    # Jensen wake loss → Euclidean embedding

    Turbines project onto the wind axis, $s_i = q_i^\top w_\theta$, and only these projections
    matter below: sideways position is ignored. Assuming every downstream turbine is in the wake
    of every upstream one, $L = W + W^\top$ and $D_{ij} = \tfrac23 - L_{ij}$ is a squared Euclidean
    distance matrix (Schoenberg). Classical MDS recovers points $z_i$ with
    $\|z_i - z_j\|^2 = D_{ij}$, unique up to rigid motion; we fix it by centring the points and
    using PCA axes.

    Drag turbines on the map, change θ and β, or pick a preset; everything below updates when
    you release the mouse.
    """)
    return


@app.cell
def _():
    preset = mo.ui.dropdown(list(PRESETS), value="4 turbines", label="Preset (resets layout)")
    beta_milli = mo.ui.slider(0.2, 5.0, step=0.1, value=1.0, label="β (×10⁻³ m⁻¹)", show_value=True)
    return beta_milli, preset


@app.cell
def _(preset):
    layout = mo.ui.anywidget(LayoutWidget(turbines=PRESETS[preset.value], theta=240.0))
    return (layout,)


@app.cell
def _(beta_milli, layout):
    q = np.array(layout.value["turbines"], dtype=float)
    theta = layout.value["theta"]
    beta = beta_milli.value * 1e-3
    N = len(q)
    labels = [f"T{i + 1}" for i in range(N)]
    s = q @ wind_vector(theta)
    order = np.argsort(s)
    colors = turbine_colors(N)
    W = wake_matrix(s, beta)
    L = W + W.T
    D = schoenberg_D(s, s, beta)
    Z, lam = classical_mds(D)
    rank = Z.shape[1]
    return D, L, N, W, Z, beta, colors, labels, lam, order, rank, s


@app.cell
def _(beta_milli, layout, preset):
    mo.hstack(
        [layout, mo.vstack([preset, beta_milli,
                            mo.md("r₀ = 50 m, α₀ = 0.05 gives β = 1×10⁻³ m⁻¹ (doc values).")])],
        justify="start", gap=2,
    )
    return


@app.cell
def _():
    mo.md(r"""
    ---
    ## 1. Loss matrices
    Pairwise Jensen losses for the current layout and wind direction. Rows and columns are sorted
    from upstream to downstream, so $W$ (row = source, column = affected turbine) is upper
    triangular. Losses shrink away from the diagonal as turbines get farther apart along the wind;
    $D$ is the same information flipped, so it grows away from the diagonal.
    """)
    return


@app.cell
def _(D, L, N, W, labels, order):
    _lab = [labels[i] for i in order]
    _fig = make_subplots(1, 3, subplot_titles=["W (directed wake)", "L = W + Wᵀ", "D = ⅔ − L (off-diag)"],
                         horizontal_spacing=0.06)
    for _k, _M in enumerate([W, L, D]):
        _fig.add_trace(go.Heatmap(
            z=_M[np.ix_(order, order)], x=_lab, y=_lab, zmin=0, zmax=2 / 3, colorscale=HEAT,
            showscale=_k == 2, texttemplate="%{z:.3f}" if N <= 8 else None, xgap=1, ygap=1,
            hovertemplate="row %{y} → col %{x}: %{z:.4f}<extra></extra>"), 1, _k + 1)
        _fig.update_yaxes(autorange="reversed", row=1, col=_k + 1)
    _fig.update_layout(height=340, margin=dict(t=40, b=20, l=40, r=20),
                       title_text="Rows/columns sorted upstream → downstream", title_font_size=13)
    _fig
    return


@app.cell
def _():
    mo.md(r"""
    ---
    ## 2. Euclidean embedding
    Points $z_i$ recovered from $D$ by classical MDS, so that $\|z_i - z_j\|^2 = D_{ij}$.
    $N$ turbines generally need $N - 1$ dimensions, so for $N \le 4$ the 3D view is exact; beyond
    that it shows the first three principal axes, and the plots below show how much is left out
    and how each coordinate depends on position $s$ along the wind.
    """)
    return


@app.cell
def _(N, Z, colors, labels, lam, rank, s):
    _P = np.hstack([Z, np.zeros((N, max(0, 3 - rank)))])[:, :3]
    _var = lam[:3].clip(0).sum() / lam.clip(0).sum()
    _title = (f"Exact embedding of {N} turbines in R^{rank}" if rank <= 3 else
              f"First 3 of {rank} principal axes ({_var:.0%} of variance)")
    _fig = go.Figure()
    if N <= 4:  # edges show the pairwise distances sqrt(D_ij)
        for _i in range(N):
            for _j in range(_i + 1, N):
                _fig.add_trace(go.Scatter3d(x=_P[[_i, _j], 0], y=_P[[_i, _j], 1], z=_P[[_i, _j], 2],
                                            mode="lines", line=dict(color="#c3c2b7", width=2),
                                            hoverinfo="skip", showlegend=False))
    _fig.add_trace(go.Scatter3d(
        x=_P[:, 0], y=_P[:, 1], z=_P[:, 2], mode="markers+text", text=labels, textposition="top center",
        marker=dict(size=7, color=colors, line=dict(color="#fcfcfb", width=2)), showlegend=False,
        customdata=s, hovertemplate="%{text}: s = %{customdata:.0f} m<extra></extra>"))
    _fig.update_layout(height=520, title=dict(text=_title, font_size=13),
                       scene=dict(dragmode="turntable", aspectmode="data",
                                  xaxis_title="PC1", yaxis_title="PC2", zaxis_title="PC3"),
                       margin=dict(t=40, b=0, l=0, r=0))
    _fig
    return


@app.cell
def _(Z, beta, colors, labels, lam, rank, s):
    _pos = lam.clip(0)
    _frac = _pos[:rank] / _pos.sum()
    _ks = [f"PC{k + 1}" for k in range(rank)]
    _scree = go.Figure([
        go.Bar(x=_ks, y=_frac, name="per axis", marker_color="#2a78d6",
               hovertemplate="%{x}: %{y:.1%}<extra></extra>"),
        go.Scatter(x=_ks, y=np.cumsum(_frac), name="cumulative", mode="lines+markers",
                   line=dict(color="#0b0b0b", width=2), hovertemplate="%{x}: %{y:.1%}<extra></extra>")])
    _scree.update_layout(height=300, yaxis_tickformat=".0%", yaxis_range=[0, 1.05],
                         title=dict(text="Variance captured by each principal axis", font_size=13),
                         margin=dict(t=40, b=30, l=50, r=10), legend=dict(x=0.6, y=0.5))

    _k = min(4, rank)
    _sg = np.linspace(s.min(), s.max(), 300)
    _, _xp, _ = add_point(s, _sg, beta)  # PCA coordinates as smooth functions of s
    _vs = go.Figure()
    for _j in range(_k):
        _vs.add_trace(go.Scatter(x=_sg, y=_xp[:, _j], mode="lines", name=f"PC{_j + 1}",
                                 line=dict(color=PC_COLORS[_j], width=2), hoverinfo="skip"))
        _vs.add_trace(go.Scatter(x=s, y=Z[:, _j], mode="markers", showlegend=False, text=labels,
                                 marker=dict(color=PC_COLORS[_j], size=8, line=dict(color="#fcfcfb", width=2)),
                                 hovertemplate=f"%{{text}} PC{_j + 1}: %{{y:.3f}}<extra></extra>"))
    _vs.update_layout(height=300, xaxis_title="s (m along wind)",
                      title=dict(text="PCA coordinates vs position along the wind", font_size=13),
                      margin=dict(t=40, b=40, l=50, r=10))

    _plots = [_scree, _vs]
    if _k >= 2:
        _splom = go.Figure(go.Splom(
            dimensions=[dict(label=f"PC{j + 1}", values=Z[:, j]) for j in range(_k)], text=labels,
            marker=dict(color=colors, size=8, line=dict(color="#fcfcfb", width=1)), diagonal_visible=False,
            showupperhalf=False, hovertemplate="%{text}<extra></extra>"))
        _splom.update_layout(height=420, margin=dict(t=40, b=40, l=50, r=10),
                             title=dict(text=f"Pairs of the top {_k} PCA coordinates", font_size=13))
        _plots.append(_splom)
    mo.vstack(_plots)
    return


@app.cell
def _(D, Z, lam, rank, s):
    _err = np.abs(((Z[:, None] - Z[None]) ** 2).sum(-1) - D).max()
    _gap = np.abs(s[:, None] - s[None]) + np.eye(len(s)) * 1e9
    _ties = "" if _gap.min() > 1e-6 else " ⚠ Two turbines share a wind-axis position: they map to the same point."
    mo.md(f"**Check:** rank {rank}, max |‖zᵢ−zⱼ‖² − Dᵢⱼ| = {_err:.1e}, "
          f"smallest eigenvalue of B = {lam[-1]:.1e}.{_ties}")
    return


@app.cell
def _():
    mo.md(r"""
    ---
    ## 3. What about one new turbine?
    Keep the current turbines fixed in their section 2 PCA axes (origin = their centroid) and add
    **one new turbine** at position $s$ along the wind. Its embedded point traces a curve as $s$
    varies. Each point on the curve is **exactly** where the new turbine would sit: its squared
    distance to every current turbine equals $D$. Hover over the curve to read off $s$.

    How to read it:

    - **Horizontal axes** are PC1 and PC2 from section 2: the new turbine's shadow in the current
      embedding (the lines in the coordinates-vs-$s$ plot above). The **vertical axis** $h(s)$ is
      how far it must step out of that space to get all distances right.
    - **The curve touches every current turbine** ($h = 0$ there): a new turbine at the same $s$ as
      an existing one lands on top of it ($D = 0$, maximum surrogate loss ⅔).
    - **Distance from the origin is the max-sum objective.** With $x$ the new turbine's point,
      $\sum_i D(s, s_i) = N\|x\|^2 + \text{const}$, where the constant depends only on the current
      turbines. So farther from the centroid means less total surrogate loss. The line plot shows
      this sum directly.
    - **Both ends meet.** Far upstream or downstream every $D(s, s_i) \to ⅔$, so the two ends of the
      curve converge to the same limit point: the wake has decayed and all distant positions look alike.
    - **Actually adding it changes the picture.** With $N + 1$ turbines the embedding gains a
      dimension and PCA is refit, so the axes rotate.
    - **Exact for ≤ 3 current turbines** (they span a plane, plus the height). With more, the plot
      shows PC1–2 plus the height, which is a projection.
    """)
    return


@app.cell
def _(N, Z, beta, colors, labels, rank, s):
    _sg = np.linspace(-1, 1, 400) * EXTENT * np.sqrt(2)
    _, _xp, _h = add_point(s, _sg, beta)
    _k = min(rank, 2)
    _curve = np.column_stack([_xp[:, :_k], np.zeros((len(_h), 2 - _k)), _h])
    _P = np.zeros((N, 3))
    _P[:, :_k] = Z[:, :_k]
    _fig = go.Figure([
        go.Scatter3d(x=_curve[:, 0], y=_curve[:, 1], z=_curve[:, 2], mode="lines",
                     line=dict(color="#898781", width=3), name="new turbine at s",
                     customdata=_sg, hovertemplate="s = %{customdata:.0f} m<extra></extra>"),
        go.Scatter3d(x=[0], y=[0], z=[0], mode="markers", name="centroid of current turbines",
                     marker=dict(size=4, color="#0b0b0b", symbol="x"), hoverinfo="skip"),
        go.Scatter3d(x=_P[:, 0], y=_P[:, 1], z=_P[:, 2], mode="markers+text", text=labels,
                     textposition="top center", showlegend=False, customdata=s,
                     marker=dict(size=7, color=colors, line=dict(color="#fcfcfb", width=2)),
                     hovertemplate="%{text}: s = %{customdata:.0f} m<extra></extra>")])
    _exact = "exact" if N <= 3 else f"PC1–2 of the {N} current turbines + height: a projection"
    _fig.update_layout(height=520, title=dict(text=f"Where a new turbine lands for every s ({_exact})",
                                              font_size=13),
                       scene=dict(dragmode="turntable", aspectmode="data", xaxis_title="PC1",
                                  yaxis_title="PC2", zaxis_title="height h(s)"),
                       margin=dict(t=40, b=0, l=0, r=0), legend=dict(x=0, y=1))

    _obj = go.Figure([
        go.Scatter(x=_sg, y=schoenberg_D(_sg, s, beta).sum(1), mode="lines", showlegend=False,
                   line=dict(color="#898781", width=2),
                   hovertemplate="s = %{x:.0f} m: ΣD = %{y:.3f}<extra></extra>"),
        go.Scatter(x=s, y=schoenberg_D(s, s, beta).sum(1), mode="markers+text", text=labels,
                   textposition="top center", showlegend=False,
                   marker=dict(size=8, color=colors, line=dict(color="#fcfcfb", width=2)),
                   hovertemplate="%{text}: s = %{x:.0f} m<extra></extra>")])
    _obj.add_hline(y=2 / 3 * N, line_dash="dot", line_color="#898781",
                   annotation_text="limit N·⅔", annotation_position="bottom right")
    _obj.update_layout(height=300, xaxis_title="new turbine position s (m along wind)",
                       yaxis_title="Σᵢ D(s, sᵢ)", margin=dict(t=40, b=40, l=60, r=10),
                       title=dict(text="Max-sum objective for the new turbine (higher = less wake loss)",
                                  font_size=13))
    mo.vstack([_fig, _obj])
    return

if __name__ == "__main__":
    app.run()
