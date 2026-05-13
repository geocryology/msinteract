import warnings
import numpy as np


""" MESH_input_soil_levels.txt 
      0.05      0.05 !> delz(1)/dl_svs(1)
      0.05       0.1 !> delz(2)/dl_svs(2)
       0.1       0.2 !> delz(3)/dl_svs(3)
       0.2       0.4 !> delz(4)/dl_svs(4)
       0.6       1.0 !> delz(5)/dl_svs(5)
       1.0       2.0 !> delz(6)/dl_svs(6)
       1.0       3.0 !> delz(7)/dl_svs(7)

"""


class SoilLevels:
    def __init__(self, file=None):
        self._dz = []  # layer thickness
        self._dl_svs = []   # depth to layer bottom
        self._extra = []
        self._source_file = file
    
        if file is not None:
            self._read(file)
        
        if not (np.cumsum(self._dz) == np.array(self._dl_svs)).all():
            import pdb;pdb.set_trace()
            warnings.warn("Cumulative sum of delz does not match dl_svs values.")
    
    def _add_layer(self, delz=None, dl_svs=None, extra=""):
        if delz is None and dl_svs is None:
            raise ValueError("Either delz or dl_svs must be specified")
        if dl_svs is not None and len(self._dl_svs)> 1 and dl_svs < np.array(self._dl_svs).max():
            raise ValueError("dl_svs must be greater than or equal to the maximum existing dl_svs")
    
        if delz is None and dl_svs is not None:
            last_bottom = self._dl_svs[-1] if self._dl_svs else 0.0
            delz = dl_svs - last_bottom

        self._dz.append(delz)
        
        dl_svs = dl_svs if dl_svs is not None else sum(self._dz)        
        self._dl_svs.append(dl_svs)
        self._extra.append(extra)
    
    def __repr__(self):
        return f"MESH-SVS2 Soil with {len(self._dz)} layers"
    
    @property
    def layer_centres(self):
        return np.array(self._dl_svs) - np.array(self._dz) / 2
    
    @property
    def layer_bottoms(self):
        return np.array(self._dl_svs)
    
    @property
    def layer_thicknesses(self):
        return np.array(self._dz)   
    
    def _read(self, file):
        with open(file, "r") as f:
            for line in f:
                if line.strip() == "" or line.strip().startswith("!"):
                    continue
                delz, dl_svs, extra = self._parse_line(line)
                self._add_layer(delz=delz, dl_svs=dl_svs, extra=extra)

    
    def _parse_line(self, line):
        try:
            delz, dl_svs, extra = line.split()[:3]
            dl_svs = float(dl_svs)
        except ValueError:
            try:
                delz, extra = line.split()[:2]
                dl_svs = None
            except ValueError:
                delz = line.split()[0]
                dl_svs = None
                extra = ""
        
        return float(delz), dl_svs, extra
    
    def write(self, file):
        with open(file, "w") as f:
            for delz, dl_svs, extra in zip(self._dz, self._dl_svs, self._extra):
                line = f"{str(delz)}    {str(dl_svs)}    {extra}\n"
                f.write(line)
    
    @classmethod
    def from_delz(cls, delz_list):
        instance = cls()
        for delz in delz_list:
            instance._add_layer(delz=delz)
        return instance
    
    @classmethod
    def from_layer_bottoms(cls, layer_bottoms):
        instance = cls()
        for bottom in layer_bottoms:
            instance._add_layer(dl_svs=bottom)
        return instance


if __name__ == "__main__":
    new = SoilLevels.from_delz([0.05, 0.05, 0.1, 0.2, 0.6, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0])
    new.write(r"MESH_input_soil_levels_out.txt")