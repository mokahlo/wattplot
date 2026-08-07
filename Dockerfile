# Wattplot analysis + firmware regression environment.
#
# Builds a Python 3.12 image with the runtime + dev dependencies
# needed to:
#   * run `python wattplot.py` (the analysis pipeline)
#   * run pytest firmware/tests/ (the firmware regression suite)
#   * build the docs site with Jekyll (optional -- see comments)
#
# Not included: FreeCAD (used only by wattplot.py when generating
# the 3D model; the analysis-only pipeline doesn't need it).
# Install FreeCAD 1.0+ separately if you want to build the model.

FROM python:3.12-slim

# System deps for pvlib / matplotlib headless + netemu / scipy
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        git \
        libatlas-base-dev \
        libopenjp2-7 \
        && rm -rf /var/lib/apt/lists/*

WORKDIR /wattplot

# Copy only the dependency manifests first so Docker can cache the
# pip install layer when only the source changes.
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Copy the source
COPY . .

# Sanity check the install (catches a broken wattplot_params, missing
# entry points, etc.). The pytest run is the smoke test; the full
# suite is what CI runs.
RUN python -c "import wattplot_params; print('wattplot_params OK')" \
    && pytest firmware/tests/ -q -x --no-header

# Default to a no-op shell so `docker run -it wattplot` lands the
# user in the repo with the env set up. Override with `docker run
# wattplot python wattplot.py` etc.
CMD ["/bin/bash"]