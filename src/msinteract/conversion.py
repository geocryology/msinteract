from pathlib import Path
import logging
import numpy as np
from os import PathLike
from typing import Union, Optional
import warnings

from groundmodel.lexicon import get_lexicon, Lexicon
from groundmodel.core.column import SoilColumn, StochasticSoilColumn
from groundmodel.core.layer import Layer
from groundmodel.core.geometry import resample_properties, thickness_to_midpoint
from groundmodel.logic import apply_semantic_roles, filter_column_by_domain

from msinteract.run_options import InputRunOptions

from .soil import SoilLevels
from .parameters import MeshParameters

logger = logging.getLogger(__name__)


def _write_to_soil_levels(thicknesses, soil_levels_file):
    """ 
    Write values to soil levels file, overwriting existing file if it exists. 
    """
    if Path(soil_levels_file).exists():
        logger.warning(f"File '{soil_levels_file}' already exists. It will be overwritten.")
    
    soil_levels = SoilLevels.from_delz(thicknesses)
    soil_levels.write(soil_levels_file)

    return True


def _write_to_parameters(soil_column: SoilColumn, parameters_file: Union[str, PathLike], current_thicknesses: list[float]):
    """ Write values to svs2 MESH_parameters file, will only write parameters in svs2:: domain."""
    soil_column = filter_column_by_domain(soil_column, "svs2")  # only keep properties relevant to MESH-SVS2
    column_props = soil_column.properties()
    
    params = MeshParameters(filepath=parameters_file)

    new_thicknesses = soil_column.layer_thicknesses
    params.rediscretize(current_thicknesses, new_thicknesses) 

    for param in params.keys():
        if f"svs2::{param}" in column_props:
            value = soil_column.get_property(f"svs2::{param}")
            params.set(param, value)
            print(f"Set parameter '{param}' to value '{value}' from soil column property 'svs2::{param}'")

    params.write(parameters_file)


def write_soil_column(soil_column: SoilColumn, 
                      soil_levels_file:  Union[str, PathLike], 
                      parameters_file:  Union[str, PathLike], 
                      lexicon: Optional[Union[str, Lexicon]]=None):
    if isinstance(soil_column, StochasticSoilColumn):
        raise ValueError("Stochastic SoilColumns cannot be written directly to MESH-SVS2 input files. Realize first")

    lexicon = get_lexicon(lexicon)
    apply_semantic_roles(soil_column)

    column_thicknesses = soil_column.layer_thicknesses
    current_thicknesses = SoilLevels(soil_levels_file).layer_thicknesses.tolist()
    
    if not len(current_thicknesses) == len(column_thicknesses) or not np.allclose(current_thicknesses, column_thicknesses):
        warnings.warn(f"Layer thicknesses {column_thicknesses} do not match soil levels {current_thicknesses}.")
        run_options_file = Path(parameters_file).with_name("MESH_input_run_options.ini")
        rediscretize_mesh(soil_levels_file, parameters_file, run_options_file, column_thicknesses)
    
    _write_to_parameters(soil_column, parameters_file, current_thicknesses)
    _write_to_soil_levels(column_thicknesses, soil_levels_file)


def rediscretize_mesh(soil_levels_file:str, parameters_file:str, run_options_file:str, new_thicknesses: list[float]):
    old_levels = SoilLevels(soil_levels_file)
    
    # Write new soil levels
    new_levels = SoilLevels()
    for dz in new_thicknesses:
        new_levels._add_layer(delz=dz)
    
    # Update parameter values
    params = MeshParameters(parameters_file)
    for var in params.SOIL_PARAMS:
        source_values = np.atleast_1d(params.get(var))
        new_values = resample_properties(target_z=thickness_to_midpoint(new_thicknesses),
                                         target_dz=new_thicknesses,
                                         source_thicknesses=old_levels.layer_thicknesses,
                                         source_values=source_values)
        params.set(var, new_values)
        

    runopts = InputRunOptions(run_options_file)
    runopts.set_flag("NRSOILAYEREADFLAG", str(len(new_thicknesses)))
    
    # Write updated files
    params.write(parameters_file)
    new_levels.write(soil_levels_file)


def write_soil_column_to_directory(soil_column: SoilColumn,
                                   directory: Union[str, PathLike],
                                   lexicon: Optional[Union[str, Lexicon]]=None,
                                   set_soil_layer_read_flag=True):
    """    
    By default, values for 3 layers are required and only read. The values of the third layer are applied to all deeper layers.
    To override this behaviour, activate "NRSOILAYEREADFLAG" in MESH_input_run_options.ini with an option.
    """
    soil_levels_file = Path(directory,  "MESH_input_soil_levels.txt")
    parameters_file = Path(directory, "MESH_parameters.txt")
    
    write_soil_column(soil_column, soil_levels_file, parameters_file, lexicon)

    if set_soil_layer_read_flag:
        from msinteract.run_options import set_run_option_flag
        n_layers = len(soil_column.layers)
        set_run_option_flag(Path(directory, "MESH_input_run_options.ini"), "NRSOILAYEREADFLAG", str(n_layers))   # is this a typo?


def mesh_directory_to_soil_column(directory: Union[str, PathLike], lexicon=None) -> SoilColumn:
    """Reads soil column properties from MESH-SVS2 input files in a directory."""
    soil_levels_file = Path(directory,  "MESH_input_soil_levels.txt")
    parameters_file = Path(directory, "MESH_parameters.txt")

    lexicon = get_lexicon(lexicon)

    soil_levels = SoilLevels(soil_levels_file)
    params = MeshParameters(parameters_file)

    thicknesses = soil_levels.layer_thicknesses
    layers = [{} for _ in thicknesses]
    params = {param: params.get(param) for param in params.SOIL_PARAMS if params.get(param) is not None}
    
    for i, t in enumerate(thicknesses):
        layers[i]["svs2::__layer_thickness"] = t
        for param, values in params.items():
            if i >= len(values):  # in MESH file, last value applies to all deeper layers
                value = values[-1]
            else:
                value = values[i]

            layers[i][f"svs2::{param}"] = value
            
    column = SoilColumn(layers=[Layer(l) for l in layers])
    column = apply_semantic_roles(column, lexicon=lexicon)  

    return column
