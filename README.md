# EddyClicker

Project for manual eddies tracking written by Elizaveta Ezhova (October, 2024).

## Installing

All packages are listed in requirements.txt, so you can install it using pip or Anaconda.

```sh
conda create --name clicker_env
conda activate clicker_env
conda install --yes --file requirements.txt
python eddyclicker.py
```

```sh
python -m venv clicker_env
source clicker_env/bin/activate
pip install -r requirements.txt
python eddyclicker.py
```

## Using

### First start

When you first start the program, you will be asked to select files with the pressure field and vortex centers, as well
as a folder for saving files. The last opened files will be opened automatically during subsequent starts. Saved tracks
from the folder are loaded automatically.

### Navigation

The display uses grid node coordinates, and the geographic coordinates corresponding to the cursor position are
displayed at the bottom right. Using the magnifying glass, you can zoom in on the image, using the left and right
buttons (also on keyboard) to switch between views. The home button will return you to the original position.

The current time of the shot is written at the top of the map. Using the up and down keys on the keyboard, you can move
forward and backward in time. The current coordinates of the centers of the identified vortices are shown as black dots,
the previous ones - as circles.

### Tracking

You can create tracks by connecting points on the map in sequence. To create a track, you must connect a circle to a
point - this will be the first segment. Then switch to a step forward and connect the circle (the former dot) to the
next dot. Using the mouse wheel you can adjust the compression of the ellipse. When you want to finish the track,
right-click on the end point of the track (circle). The geographic
coordinates of all points of the track will be sequentially written to the specified file. After that, the built track
will be deleted from the map.

An unnecessary track point can be deleted by double-clicking on it. If you accidentally start a new segment, press Esc
and select a new point again.