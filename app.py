import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="WingLab | Module 1",
    page_icon="✈️",
    layout="wide",
)

st.title("WingLab — Parametric Flying-Wing Generator")
st.caption(
    "Module 1: parametric geometry, 3D visualization, basic checks, and CSV export. "
    "Preliminary engineering tool; not validated for flight or manufacture."
)


def naca4(code: str = "0012", n: int = 81):
    """Generate normalized upper/lower coordinates for a NACA four-digit airfoil."""
    if len(code) != 4 or not code.isdigit():
        raise ValueError("Select a valid four-digit NACA airfoil code.")

    m = int(code[0]) / 100.0
    p = int(code[1]) / 10.0
    t = int(code[2:]) / 100.0

    if not (0.0 < t < 0.40):
        raise ValueError("Airfoil thickness must be greater than 0% and less than 40%.")
    if m > 0 and p == 0:
        raise ValueError("A cambered NACA four-digit airfoil needs a nonzero camber position.")

    beta = np.linspace(0.0, np.pi, n)
    x = (1.0 - np.cos(beta)) / 2.0

    # Closed trailing-edge thickness coefficient (-0.1036).
    yt = 5.0 * t * (
        0.2969 * np.sqrt(np.maximum(x, 0.0))
        - 0.1260 * x
        - 0.3516 * x**2
        + 0.2843 * x**3
        - 0.1036 * x**4
    )

    yc = np.zeros_like(x)
    dyc_dx = np.zeros_like(x)

    if m > 0:
        front = x < p
        rear = ~front

        yc[front] = (m / p**2) * (2.0 * p * x[front] - x[front]**2)
        dyc_dx[front] = (2.0 * m / p**2) * (p - x[front])

        yc[rear] = (m / (1.0 - p)**2) * (
            1.0 - 2.0 * p + 2.0 * p * x[rear] - x[rear]**2
        )
        dyc_dx[rear] = (2.0 * m / (1.0 - p)**2) * (p - x[rear])

    theta = np.arctan(dyc_dx)
    xu = x - yt * np.sin(theta)
    zu = yc + yt * np.cos(theta)
    xl = x + yt * np.sin(theta)
    zl = yc - yt * np.cos(theta)

    # Interpolate onto a common chordwise grid for a structured surface.
    z_upper = np.interp(x, xu, zu)
    z_lower = np.interp(x, xl, zl)
    return x, z_upper, z_lower


def generate_wing(
    span: float,
    root_chord: float,
    taper_ratio: float,
    sweep_deg: float,
    dihedral_deg: float,
    root_twist_deg: float,
    tip_twist_deg: float,
    airfoil: str,
    n_span: int = 41,
    n_chord: int = 81,
):
    """Generate symmetric, linearly tapered flying-wing surface grids."""
    numeric = [
        span, root_chord, taper_ratio, sweep_deg, dihedral_deg,
        root_twist_deg, tip_twist_deg,
    ]
    if not np.all(np.isfinite(numeric)):
        raise ValueError("All numeric inputs must be finite.")
    if span <= 0 or root_chord <= 0:
        raise ValueError("Wingspan and root chord must be positive.")
    if not (0.0 < taper_ratio <= 1.0):
        raise ValueError("Taper ratio must be greater than 0 and at most 1.")
    if n_span < 3 or n_chord < 11:
        raise ValueError("Use at least 3 span stations and 11 chordwise points.")

    x_norm, z_upper_norm, z_lower_norm = naca4(airfoil, n_chord)

    y = np.linspace(-span / 2.0, span / 2.0, n_span)
    eta = np.abs(y) / (span / 2.0)

    chord = root_chord * (1.0 - (1.0 - taper_ratio) * eta)
    leading_edge_x = np.abs(y) * np.tan(np.deg2rad(sweep_deg))
    base_z = np.abs(y) * np.tan(np.deg2rad(dihedral_deg))
    twist = np.deg2rad(root_twist_deg + (tip_twist_deg - root_twist_deg) * eta)

    # Chordwise positions are rotated about the local quarter-chord point.
    local_x = (x_norm[None, :] - 0.25) * chord[:, None]
    local_x = np.broadcast_to(local_x, (n_span, n_chord))

    def build_surface(z_norm):
        local_z = z_norm[None, :] * chord[:, None]
        angle = twist[:, None]

        x_rot = local_x * np.cos(angle) + local_z * np.sin(angle)
        z_rot = -local_x * np.sin(angle) + local_z * np.cos(angle)

        X = leading_edge_x[:, None] + 0.25 * chord[:, None] + x_rot
        Y = np.broadcast_to(y[:, None], X.shape).copy()
        Z = base_z[:, None] + z_rot
        return X, Y, Z

    Xu, Yu, Zu = build_surface(z_upper_norm)
    Xl, Yl, Zl = build_surface(z_lower_norm)

    surfaces = (Xu, Yu, Zu, Xl, Yl, Zl)
    if not all(np.all(np.isfinite(a)) for a in surfaces):
        raise ValueError("Generated geometry contains non-finite coordinates.")
    if np.any(chord <= 0):
        raise ValueError("Generated geometry contains a non-positive chord.")

    # Exact for the assumed linearly tapered trapezoidal planform.
    tip_chord = root_chord * taper_ratio
    area = span * (root_chord + tip_chord) / 2.0
    aspect_ratio = span**2 / area
    mean_aerodynamic_chord = (
        2.0 * root_chord / 3.0
        * (1.0 + taper_ratio + taper_ratio**2)
        / (1.0 + taper_ratio)
    )
    y_mac = (
        span / 6.0
        * (1.0 + 2.0 * taper_ratio)
        / (1.0 + taper_ratio)
    )

    return {
        "Xu": Xu, "Yu": Yu, "Zu": Zu,
        "Xl": Xl, "Yl": Yl, "Zl": Zl,
        "y": y, "chord": chord, "leading_edge_x": leading_edge_x,
        "area": area, "aspect_ratio": aspect_ratio,
        "mean_aerodynamic_chord": mean_aerodynamic_chord,
        "y_mac": y_mac,
    }


def coordinates_dataframe(wing):
    """Return long-form upper/lower surface coordinates in metres."""
    frames = []
    for side in ("upper", "lower"):
        X = wing["X" + side[0]]
        Y = wing["Y" + side[0]]
        Z = wing["Z" + side[0]]
        ns, nc = X.shape
        frames.append(pd.DataFrame({
            "surface": side,
            "span_station_index": np.repeat(np.arange(ns), nc),
            "chord_station_index": np.tile(np.arange(nc), ns),
            "x_m": X.ravel(),
            "y_m": Y.ravel(),
            "z_m": Z.ravel(),
        }))
    return pd.concat(frames, ignore_index=True)


with st.sidebar:
    st.header("Wing parameters")
    span = st.slider("Full wingspan (m)", 0.4, 3.0, 1.2, 0.05)
    root_chord = st.slider("Root chord (m)", 0.08, 0.60, 0.20, 0.01)
    taper_ratio = st.slider("Taper ratio (tip chord / root chord)", 0.10, 1.00, 0.35, 0.05)
    sweep_deg = st.slider("Leading-edge sweep (deg)", 0.0, 60.0, 25.0, 1.0)
    dihedral_deg = st.slider("Dihedral (deg)", -5.0, 15.0, 3.0, 0.5)
    root_twist_deg = st.slider("Root twist (deg)", -8.0, 8.0, 0.0, 0.5)
    tip_twist_deg = st.slider("Tip twist (deg)", -12.0, 8.0, -2.0, 0.5)
    airfoil = st.selectbox("NACA four-digit airfoil", ["0012", "2412", "4412", "0015", "0018"])
    n_span = st.select_slider("Spanwise stations", options=[11, 21, 41, 61, 81], value=41)
    n_chord = st.select_slider("Chordwise points", options=[21, 41, 61, 81, 101], value=81)
    st.caption("This version uses a symmetric, linearly tapered planform.")

try:
    wing = generate_wing(
        span=span,
        root_chord=root_chord,
        taper_ratio=taper_ratio,
        sweep_deg=sweep_deg,
        dihedral_deg=dihedral_deg,
        root_twist_deg=root_twist_deg,
        tip_twist_deg=tip_twist_deg,
        airfoil=airfoil,
        n_span=n_span,
        n_chord=n_chord,
    )
except ValueError as exc:
    st.error(f"Geometry generation failed: {exc}")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Full span", f"{span:.3f} m")
c2.metric("Planform area", f"{wing['area']:.4f} m²")
c3.metric("Aspect ratio", f"{wing['aspect_ratio']:.3f}")
c4.metric("Mean aerodynamic chord", f"{wing['mean_aerodynamic_chord']:.4f} m")

st.success("Basic checks passed: finite coordinates and positive chord values.")
st.warning(
    "These checks do not establish surface watertightness, structural integrity, "
    "aerodynamic performance, stability, manufacturability, or flight safety."
)

fig = go.Figure()
for X, Y, Z, name in (
    (wing["Xu"], wing["Yu"], wing["Zu"], "Upper surface"),
    (wing["Xl"], wing["Yl"], wing["Zl"], "Lower surface"),
):
    fig.add_trace(go.Surface(
        x=X, y=Y, z=Z, name=name, showscale=False, opacity=0.96,
        hovertemplate=(
            "X: %{x:.4f} m<br>Y: %{y:.4f} m<br>Z: %{z:.4f} m"
            f"<extra>{name}</extra>"
        ),
    ))

# Show section outlines at selected span stations.
for idx in sorted(set([0, len(wing["y"]) // 4, len(wing["y"]) // 2,
                       3 * len(wing["y"]) // 4, len(wing["y"]) - 1])):
    x_line = np.concatenate([wing["Xu"][idx, :], wing["Xl"][idx, ::-1]])
    y_line = np.concatenate([wing["Yu"][idx, :], wing["Yl"][idx, ::-1]])
    z_line = np.concatenate([wing["Zu"][idx, :], wing["Zl"][idx, ::-1]])
    fig.add_trace(go.Scatter3d(
        x=x_line, y=y_line, z=z_line, mode="lines",
        name=f"Section y={wing['y'][idx]:.2f} m",
        line={"width": 3},
    ))

fig.update_layout(
    title="Interactive 3D wing geometry",
    scene={
        "xaxis_title": "X — chordwise (m)",
        "yaxis_title": "Y — spanwise (m)",
        "zaxis_title": "Z — vertical (m)",
        "aspectmode": "data",
    },
    height=680,
    margin={"l": 0, "r": 0, "t": 55, "b": 0},
    legend={"orientation": "h"},
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Spanwise stations")
stations = pd.DataFrame({
    "y_m": wing["y"],
    "leading_edge_x_m": wing["leading_edge_x"],
    "chord_m": wing["chord"],
})
st.dataframe(stations, use_container_width=True)

st.subheader("Export")
coords = coordinates_dataframe(wing)
st.download_button(
    "Download upper/lower surface coordinates (CSV)",
    data=coords.to_csv(index=False).encode("utf-8"),
    file_name="wing_surface_coordinates.csv",
    mime="text/csv",
)
st.download_button(
    "Download spanwise station table (CSV)",
    data=stations.to_csv(index=False).encode("utf-8"),
    file_name="wing_spanwise_stations.csv",
    mime="text/csv",
)
st.caption(
    "Coordinate CSVs are point grids, not STEP solids or watertight manufacturing meshes. "
    "The current area and aspect-ratio calculations assume a linearly tapered trapezoidal planform."
)
