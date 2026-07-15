from msinteract.parameters import MeshParameters
from msinteract.run_options import InputRunOptions
from msinteract.meteo import first_date_from_met
from datetime import datetime
import re


def set_coordinates(mesh_parameters:str, lat: float, lon: float):
    params = MeshParameters(mesh_parameters)
    params.set('deglat', lat)
    params.set('deglng', lon)
    params.write(mesh_parameters)


def set_start_date(run_options: str, start_date: str|datetime|int):
    options = InputRunOptions(run_options)
    
    if isinstance(start_date, int):
        start_date = str(start_date)
    
    if not isinstance(start_date, datetime):
        if not re.match(r"\d{10}", start_date):
            raise ValueError(f"start_date must be a string in the format YYYYMMDDHH, got {start_date}")
        start_date = datetime.strptime(start_date, "%Y%m%d%H")
    
    start_date = start_date.strftime("%Y%m%d%H")    
    current_flag = options.get_flag('BASINFORCINGFLAG')
    
    if not isinstance(current_flag, str):
        raise ValueError(f"Unexpected value for BASINFORCINGFLAG: {current_flag}")
    
    if 'start_date' in current_flag:
        new_flag = re.sub(r"start_date=\d{10}", f"start_date={start_date}", current_flag)
    else:
        new_flag = f"{current_flag},start_date={start_date}"

    options.set_flag('BASINFORCINGFLAG', new_flag)


def set_start_date_from_met(run_options: str, met_file: str):
    first_date = first_date_from_met(met_file)
    set_start_date(run_options, first_date)
    