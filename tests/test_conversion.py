import tempfile
import shutil
from pathlib import Path
import importlib.resources as res
from contextlib import contextmanager

from groundmodel.core.property import PropertySet, Property
from groundmodel.core.surface import SurfaceProperties
from groundmodel.core.layer import Layer
from groundmodel.core.column import SoilColumn
from msinteract.parameters import MeshParameters
from msinteract.vegetation import canopies, z0v
from msinteract.conversion import write_surface, write_soil_column

package = "msinteract.data"

svs2_files = [
    "MESH_parameters.txt",
    "MESH_input_soil_levels.txt",
    "MESH_input_run_options.ini",
]

@contextmanager
def package_data_context(filenames, package="msinteract.data"):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        base = res.files(package)

        for name in filenames:
            shutil.copy(base / name, tmpdir / name)

        yield tmpdir


s1 = SurfaceProperties([Property("svs2::vf", canopies(tundra=0.95, shor_gr=0.05)),
                        Property("svs2::hsnowscheme", "ES")],
                        name="test_surface_properties")

md = {'role_bindings': {'layer_thickness': 'svs2::__layer_thickness'}}
c1 = SoilColumn([Layer(data=[Property("svs2::__layer_thickness", 0.1),
                            Property("svs2::sand", 0.5), 
                            Property("svs2::clay", 0.3)], metadata=md),
                Layer(data=[Property("svs2::__layer_thickness", 0.1),
                            Property("svs2::sand", 0.5), 
                            Property("svs2::clay", 0.3)], metadata=md),
                Layer(data=[Property("svs2::__layer_thickness", 2.8),
                            Property("svs2::sand", 0.4), 
                            Property("svs2::clay", 0.4)], metadata=md)])


def test_write_surface():
    with package_data_context(svs2_files) as tmpdir:
        parameters_file = tmpdir / "MESH_parameters.txt"
        write_surface(s1, parameters_file)

        changed_params = MeshParameters(parameters_file)

        assert changed_params.get("vf")[21] == 0.95
        assert type(changed_params.get("vf")) == type(changed_params.get("z0v"))
        assert changed_params.get("hsnowscheme") == "ES"
        assert type(changed_params.get("hsnowscheme")) == type(changed_params.get("hsnowmetamo"))


def test_write_column():
    with package_data_context(svs2_files) as tmpdir:
        parameters_file = tmpdir / "MESH_parameters.txt"
        soil_levels_file = tmpdir / "MESH_input_soil_levels.txt"
        write_soil_column(c1, soil_levels_file, parameters_file)

        changed_params = MeshParameters(parameters_file)

        assert changed_params.get("sand")[0] == 0.5
        assert changed_params.get("clay")[1] == 0.3
        assert type(changed_params.get("tpsoil")[0]) is type(changed_params.get("sand")[0])