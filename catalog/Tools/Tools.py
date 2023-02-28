import numpy as np
import os
from typing import Literal
import h5py
from Tools.parameters import get_indices_from_parfile as getPar


class SimulationAnalysis:
    def __init__(self, simulation_name, simulation_folder_path):
        self.simulation_name = simulation_name
        self.path = os.path.join(simulation_folder_path, self.simulation_name)
        self.log_path = os.path.join(self.path, 'log')
        self.hdf_path = os.path.join(self.path, 'outp-hdf')
        self.grid_path = os.path.join(self.path, 'grid')
        self.par_path = os.path.join(self.path, 'pars')
        self.rho_max_file = 'rho.dat'
        self.hydroTHD_index, self.ghost_cells = getPar('start.pars', self.par_path)
        self.cell = cell(self.path, None)
        self.dim = self.cell.simulation_dimension()
        self.ghost = ghost(self.ghost_cells)

    def time_of_bounce_rho(self):
        rho_data = self.__rho_max()
        rho_index = np.argmax(rho_data[:,1]>2.5e14)
        if rho_index == 0 or rho_data[rho_index, 0] >= 0.6:
            rho_index = np.argmax(rho_data[:,1]>2e14)
        return rho_data[rho_index, 0]

    def file_list_hdf(self):
        file_list = os.listdir(self.hdf_path)
        #remove x00 files
        file_list = [x for x in file_list if x.startswith('h')]
        #return the sorted list of files
        file_list.sort()
        return file_list
    
    def open_h5(self, file_name):
        file_path = os.path.join(self.hdf_path, file_name)
        return h5py.File(file_path)
    
    def close_h5(self, data_h5):
        data_h5.close()

    def poloidal_magnetic_field(self, data_h5):
        data = self.__magnetic_field(data_h5)
        return np.sqrt(data[...,0]**2+data[...,1]**2)

    def toroidal_magnetic_field(self, data_h5):
        return self.__magnetic_field(data_h5)[...,2]
    
    def time(self, data_h5):
        return np.array(data_h5['Parameters']['t'])
    
    def omega(self, data_h5):
        v_phi = self.__phi_velocity(data_h5)
        radius = self.cell.radius(self.ghost)
        if self.dim == 1:
            return v_phi / radius[None, :]
        theta = np.sin(self.cell.theta(self.ghost))
        if self.dim == 2:
            return v_phi / (theta[:, None] * radius[None, :])
        if self.dim == 3:
            phi = np.cos(self.cell.phi(self.ghost))
            return v_phi / (phi[:, None, None] * theta[None, :, None] * radius[None, None, :])
    
    def __phi_velocity(self, data_h5):
        data = np.array(data_h5['thd']['data'])[:,:,:,self.hydroTHD_index['thd']['I_VELZ']]
        return self.ghost.remove_ghost_cells(np.squeeze(data), self.dim)

    def __rho_max(self):
        rho =  np.loadtxt(os.path.join(self.log_path, self.rho_max_file), 
                          usecols=(2, 3))
        return rho
    
    def __magnetic_field(self, data_h5):
        return self.ghost.remove_ghost_cells(np.squeeze(np.array(data_h5['mag_vol']['data'])),
                                             self.dim)
    
class cell:
    def __init__(self, path_folder, dim=None):
        assert dim in (1, 2, 3, None), "Supernova simulation can either be 1D, 2D or 3D"
        self.path_grid = os.path.join(path_folder, 'grid')
        self.__radius_file = np.loadtxt(os.path.join(self.path_grid, 'grid.x.dat'))
        self.__theta_file = np.loadtxt(os.path.join(self.path_grid, 'grid.y.dat'))
        self.__phi_file = np.loadtxt(os.path.join(self.path_grid, 'grid.z.dat'))
        if dim is None:
            dim = 1
            if (self.__theta_file).size > 4:
                dim += 1
            if (self.__phi_file).size > 4:
                dim += 1
        self.dim = dim

    def simulation_dimension(self):
        return self.dim

    def radius(self, ghost):
        return ghost.remove_ghost_cells(self.__radius_file[:, 2], self.dim, 'radius')

    def dr(self, ghost):
        return ghost.remove_ghost_cells(self.__radius_file[:, 3], self.dim, 'radius') - \
            ghost.remove_ghost_cells(self.__radius_file[:, 1], self.dim, 'radius')

    def theta(self, ghost):
        return ghost.remove_ghost_cells(self.__theta_file[:, 2], self.dim, 'theta')
    
    def phi(self, ghost):
        return ghost.remove_ghost_cells(self.__phi_file[:, 2], self.dim, 'phi')

class ghost:
    def __init__(self, ghost_cells):
        self.ghost = ghost_cells
        self.__options_default = {'r_l': self.ghost,
                                  'r_r': self.ghost,
                                  't_l': self.ghost,
                                  't_r': self.ghost,
                                  'p_l': self.ghost,
                                  'p_r': self.ghost}
        for key, value in self.__options_default.items():
            self.__setattr__(key, value)
        self.__options_1D = {'radius': [self.r_l, self.r_r],
                           'theta': [self.t_l, self.t_r],
                           'phi': [self.p_l, self.p_r]}

    def restore_default(self):
        for key, value in self.__options_default.items():
            self.__setattr__(key, value)
        self.__options_1D = {'radius': [self.r_l, self.r_r],
                           'theta': [self.t_l, self.t_r],
                           'phi': [self.p_l, self.p_r]}

    def update_ghost_cells(self, **kwargs):
        self.restore_default()
        updated_parameters = self.__options_default.copy()
        updated_parameters.update(kwargs)
        values = list(updated_parameters.values())
        if min(values)<0 or max(values)>self.ghost:
            raise TypeError("The number of ghost cells MUST be between 0 and " + str(self.ghost))
        for key, value in updated_parameters.items():
            self.__setattr__(key, value)
        self.__options_1D = {'radius': [self.r_l, self.r_r],
                           'theta': [self.t_l, self.t_r],
                           'phi': [self.p_l, self.p_r]}
        del updated_parameters

    def return_ghost_dictionary(self):
        return self.__options_1D

    def remove_ghost_cells(self, array, dim, quantity_1D: 
                           Literal['radius', 'theta', 'phi'] = None):
        assert dim in (1, 2, 3), "Simulation MUST be 1, 2 or 3D"
        array_dim = array.ndim
        if dim == 1:
            if array_dim not in (1, 2):
                raise TypeError("Array MUST be 1 or 2D")
            if array_dim == 1:
                return self.__remove_1D_ghost_cells(array, 'radius')
            elif array_dim == 2:
                return self.__remove_ghost_cells_2D_ar_1D_sim(array)
        elif dim == 2:
            if array_dim not in (1, 2, 3):
                raise TypeError("Array MUST be 1, 2 or 3D")
            if array_dim == 1:
                if not quantity_1D in ['radius', 'theta']:
                    raise TypeError("Quantity type required: " + str(['radius', 'theta']))
                return self.__remove_1D_ghost_cells(array, quantity_1D)
            elif array_dim == 2:
                return self.__remove_2D_ghost_cells(array)
            elif array_dim == 3:
                return self.__remove_ghost_cells_3D_ar_2D_sim(array)
        else:
            if array_dim not in (1, 3, 4):
                raise TypeError("Array MUST be 1, 3 or 4D")
            if array_dim == 1:
                if not quantity_1D in ['radius', 'theta', 'phi']:
                    raise TypeError("Quantity type required: " + str(['radius', 'theta', 'phi']))
                return self.__remove_1D_ghost_cells(array, quantity_1D)
            elif array_dim == 3:
                return self.__remove_3D_ghost_cells(array)
            elif array_dim == 4:
                return self.__remove_ghost_cells_4D_ar_3D_sim(array)

    def remove_ghost_cells_radii(self, array, dim, **kwargs):
        assert dim in (1, 2, 3), "Simulation MUST be 1, 2 or 3D"
        if kwargs:
            self.update_ghost_cells(**kwargs)
            if dim == 2:
                array = self.__remove_2D_ghost_cells_radii(array)
            else:
                array = self.__remove_3D_ghost_cells_radii(array)
            self.restore_default()
            return array
        if dim == 1:
            return array
        if dim == 2:
            return self.__remove_2D_ghost_cells_radii(array)
        else:
            return self.__remove_3D_ghost_cells_radii(array)

    def __remove_1D_ghost_cells(self, array, quantity_1D):
        assert array.ndim == 1, "Array must be 1-dimensional"
        boundaries = self.__options_1D[quantity_1D]
        size = array.shape[0]
        return array[boundaries[0] : size - boundaries[1]]
    
    def __remove_2D_ghost_cells(self, array):
        assert array.ndim == 2, "Array must be 2-dimensional"
        size_y = array.shape[0]
        size_x = array.shape[1]
        return array[self.t_l : size_y - self.t_r,
                     self.r_l : size_x - self.r_r]

    def __remove_3D_ghost_cells(self, array):
        assert array.ndim == 3, "Array must be 3-dimensional"
        size_z = array.shape[0]
        size_y = array.shape[1]
        size_x = array.shape[2]
        return array[self.p_l : size_z - self.p_r,
                     self.t_l : size_y - self.t_r, 
                     self.r_l : size_x - self.r_r]
    
    def __remove_2D_ghost_cells_radii(self, array):
        t_r = abs(self.t_r-self.__options_default['t_r'])
        t_l = abs(self.t_l-self.__options_default['t_l'])
        return array[t_l : array.shape[0] - t_r]

    def __remove_3D_ghost_cells_radii(self, array):
        t_r = abs(self.t_r-self.__options_default['t_r'])
        t_l = abs(self.t_l-self.__options_default['t_l'])
        p_r = abs(self.p_r-self.__options_default['p_r'])
        p_l = abs(self.p_l-self.__options_default['p_l'])
        return array[p_l : array.shape[0] - p_r,
                     t_l : array.shape[1] - t_r]

    def __remove_ghost_cells_2D_ar_1D_sim(self, array):
        assert array.ndim == 2, "Array must be 2-dimensional"
        size = array.shape[0]
        return array[self.r_l : size - self.r_r, :]

    def __remove_ghost_cells_3D_ar_2D_sim(self, array):
        assert array.ndim == 3, "Array must be 3-dimensional"
        size_y = array.shape[0]
        size_x = array.shape[1]
        return array[self.t_l : size_y - self.t_r, self.r_l : size_x - self.r_r, :]

    def __remove_ghost_cells_4D_ar_3D_sim(self, array):
        assert array.ndim == 4, "Array must be 4-dimensional"
        size_z = array.shape[0]
        size_y = array.shape[1]
        size_x = array.shape[2]
        return array[self.p_l : size_z - self.p_r,
                     self.t_l : size_y - self.t_r, 
                     self.r_l : size_x - self.r_r,
                     :]