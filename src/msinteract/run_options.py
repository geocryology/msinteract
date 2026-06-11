import re
import os
import datetime

class InputRunOptions:
    """
    Class to manage reading and updating run option flags in MESH-SVS2 input files.
    """

    def __init__(self, file_path):
        self.file_path = file_path
    
    def __getitem__(self, key):
        return self.get_flag(key)
    
    def get_flag(self, key):
        raise NotImplementedError("get_flag method is not implemented yet.")

    def set_flag(self, key, value):
        raise NotImplementedError("set_flag method is not implemented yet.") 

    def get_output_directory(self):
        raise NotImplementedError("get_output_directory method is not implemented yet.")
    
    def get_start_date(self):
        raise NotImplementedError("get_start_date method is not implemented yet.")
    
    def get_end_date(self) -> datetime.datetime:
        raise NotImplementedError("get_end_date method is not implemented yet.")
    
    def set_start_date(self, start_date: datetime.datetime):
        raise NotImplementedError("set_start_date method is not implemented yet.")

    def set_end_date(self, end_date: datetime.datetime):
        raise NotImplementedError("set_end_date method is not implemented yet.")