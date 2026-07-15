'''
 00 00  001  1950     0.00   105.94    1.7669E-07   -42.03   6.556E-05    5.39    97101.92
 01 00  001  1950     0.00   105.71    1.7669E-07   -42.18   6.439E-05    5.47    97186.01
 02 00  001  1950     0.00   110.63    2.0207E-07   -42.19   6.415E-05    5.57    97102.68
 03 00  001  1950     0.00   113.81    5.3995E-07   -42.07   6.498E-05    5.89    97155.09
 04 00  001  1950     0.00   122.23    7.7077E-07   -41.77   6.731E-05    6.00    97090.86
 05 00  001  1950     0.00   127.11    9.5617E-07   -41.51   6.931E-05    5.73    97108.66
'''
from datetime import datetime, timedelta


def first_date_from_met(met_file: str) -> datetime:
    with open(met_file, 'r') as f:
        firstline = f.readline()
    date = _date_from_met_line(firstline)
    return date


def _last_line(path: str) -> str:
    with open(path, "rb") as f:
        f.seek(-2, 2)              
        while f.read(1) != b"\n":  
            f.seek(-2, 1)          
        return f.readline().decode()


def last_date_from_met(met_file: str) -> datetime:
    lastline = _last_line(met_file)
    date = _date_from_met_line(lastline)
    return date
    

def _date_from_met_line(line: str) -> datetime:
    elements = line.split(" ")
    year = int(elements[3])
    jday = int(elements[2])
    hour = int(elements[0])
    minute = int(elements[1])
    date = datetime(year, 1, 1, hour, minute) + timedelta(days=jday - 1)
    return date