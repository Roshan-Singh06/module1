WingLab — Module 1: Parametric Flying-Wing Generator
A small Streamlit application for generating a preliminary symmetric flying-wing geometry, visualizing the upper and lower surfaces in 3D, inspecting spanwise stations, and exporting coordinates as CSV.
Features
- Interactive controls for full wingspan, root chord, taper ratio, leading-edge sweep, dihedral, root twist, tip twist, and NACA four-digit airfoil.
- Structured upper/lower surface point grids.
- Interactive Plotly 3D visualization.
- Basic checks for finite inputs/coordinates and positive chord.
- Planform area, aspect ratio, and mean aerodynamic chord estimates for the assumed linearly tapered trapezoidal planform.
- CSV export for surface coordinates and spanwise station data.
Requirements
- Python 3.10 or newer recommended
- Packages listed in requirements.txt
Setup
Windows
py -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run module1_wing_generator.py
macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run module1_wing_generator.py
Streamlit will print a local URL in the terminal, usually http://localhost:8501.
Export files
Use the buttons in the app to export:
- wing_surface_coordinates.csv: upper and lower surface points in metres, with spanwise and chordwise indices.
- wing_spanwise_stations.csv: span station, leading-edge x coordinate, and local chord.
These exports contain point data. They are not a CAD solid, validated surface mesh, or manufacturing-ready file.
Coordinate conventions
- X: chordwise direction
- Y: spanwise direction, from left tip to right tip
- Z: vertical direction
- Units: metres for coordinates and dimensions; degrees for angular inputs
- The wing is symmetric about the X-Z center plane by construction.
- Sweep is defined by a straight leading edge whose x offset grows with absolute spanwise distance.
- Chord tapers linearly from the root chord to the tip chord.
- Twist varies linearly from root to tip and is applied about each section's quarter-chord point.
- Airfoil selection uses a conventional NACA four-digit profile generator.
Important limitations
This is a Module 1 geometry prototype, not a complete aircraft design system.
It does not currently perform:
- Aerodynamic solver analysis or lift/drag prediction
- Stability, trim, control authority, or center-of-gravity analysis
- Structural stress, buckling, deflection, fatigue, or material checks
- CAD-kernel solid creation, self-intersection testing, or watertightness verification
- Mesh convergence studies or independent validation
- Flight-readiness or certification checks
A generated geometry can be mathematically valid while being aerodynamically or structurally unsuitable. Do not use this tool alone to manufacture or fly an aircraft.
Troubleshooting
- If streamlit is not recognized, activate the virtual environment and run python -m streamlit run module1_wing_generator.py.
- If installation fails, confirm Python 3.10+ and retry after upgrading pip.
- If the browser does not open automatically, use the local URL printed in the terminal.
- If you encounter an error, send the full terminal traceback and a screenshot of the app.
Next planned development
Module 1.1: multiple spanwise design stations with independently editable chord, sweep, twist, and vertical position, followed by stronger geometric validation and CAD export.
