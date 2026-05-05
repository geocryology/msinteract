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
    
        if file is not None:
            self.read(file)
        
        if not (np.cumsum(self._dz) == np.array(self._dl_svs)).all():
            warnings.warn("Cumulative sum of delz does not match dl_svs values.")
    
    def _add_layer(self, delz=None, dl_svs=None, extra=""):
        if delz is None and dl_svs is None:
            raise ValueError("Either delz or dl_svs must be specified")
        if dl_svs is not None and dl_svs < np.array(self._dl_svs).max():
            raise ValueError("dl_svs must be greater than or equal to the maximum existing dl_svs")
    
        if delz is None and dl_svs is not None:
            last_bottom = self._dl_svs[-1] if self._dl_svs else 0.0
            delz = dl_svs - last_bottom
    
        dl_svs = dl_svs if dl_svs is not None else sum(self._dz)
        
        self._dz.append(delz)
        self._dl_svs.append(dl_svs)
        self._extra.append(extra)
    
    def __repr__(self):
        return f"MESH-SVS2 Soil with {len(self._dz)} layers"
    
    def read(self, file):
        with open(file, "r") as f:
            for line in f:
                delz, dl_svs, extra = self._parse_line(line)
                self._dz.append(delz)
                self._dl_svs.append(dl_svs)
                self._extra.append(extra)
    
    def _parse_line(self, line):
        delz, dl_svs, extra = line.split()[:3]
        return float(delz), float(dl_svs), extra
    
    def write(self, file):
        with open(file, "w") as f:
            for delz, dl_svs, extra in zip(self._dz, self._dl_svs, self._extra):
                line = f"{str(delz)}    {str(dl_svs)}    {extra}\n"
                print(line)
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