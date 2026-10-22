# MSINTERACT: Python wrappers for MESH-SVS2

## Classes
These provide a python wrapper to read, write, and modify core input files for MESH-SVS2

### `InputRunOptions` 

```python
from msinteract import InputRunOptions
import datetime

o = InputRunOptions("MESH_input_run_options.ini")
o.get_flag("NRSOILAYEREADFLAG")
o.set_flag("NRSOILAYEREADFLAG", 10)
o.set_end_date(datetime.datetime(year=2020, month=9, day=1))
o.write("~/MESH_input_run_options.ini")

```

### `MeshParameters`


```python
from msinteract import MeshParameters

p = MeshParameters("MESH_parameters.txt")
print(f"Value of `clay` parameter is {p.get('clay')}")
p.set('clay', [20, 20, 20])
print(f"Value of `clay` parameter is {p.get('clay')}")
p.write("~/MESH_parameters.txt")
```

### `SoilLevels`

```python
from msinteract import SoilLevels

s = SoilLevels("MESH_input_soil_levels.txt")
s.layer_bottoms

s2 = SoilLevels.from_delz([0.05, 0.1, 0.5, 0.5])
s2.write("~/MESH_input_soil_levels.txt")
```

