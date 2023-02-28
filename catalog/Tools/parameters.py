import os
import f90nml

def get_indices_from_parfile(file_name, path_folder):
    namelist = f90nml.read(os.path.join(path_folder, file_name))
    indices = {'hydro':{}, 'thd':{}}    
    if 'I_VELZ'in namelist["IINDICES"]:
        indices['thd']['I_VELZ'] = namelist["IINDICES"]["I_VELZ"] - 1   
    if 'STENCIL'in namelist["GRIDPARS"]:
        STENCIL =  namelist["GRIDPARS"]["STENCIL"]
    for  k1 in indices['hydro']:
        if type(indices['hydro'][k1]) == list:
            for i in range(0,len(indices['hydro'][k1])):
                if indices['hydro'][k1][i] < 0:
                    indices['hydro'][k1][i] = None
        elif indices['hydro'][k1] < 0:
            indices['hydro'][k1] = None
    for  k1 in indices['thd']:
        if type(indices['thd'][k1]) == list:
            for i in range(0, len(indices['thd'][k1])):
                if indices['thd'][k1][i] < 0:
                    indices['thd'][k1][i] = None
        elif indices['thd'][k1] < 0:
            indices['thd'][k1] = None
    return indices, STENCIL
