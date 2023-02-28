import os
import json
import f90nml
try:
    from scidata.quantities.quantities import SimulationAnalysis
except:
    from Tools.Tools import SimulationAnalysis
import pathlib
import datetime


class catalog:
    def __init__(self, save_name, path_list, path_to_previous_catalog = None, save_folder = '..'):
        self.__catalog = self.__read_catalog(path_to_previous_catalog)
        self.__save_path, self.__save_README = self.__check_save_path(save_name, save_folder)
        self.__path_list = path_list
    
    def build_catalog(self):
        if self.__path_list is None:
            return
        assert type(self.__path_list) == str or type(self.__path_list) == list, "Wrong path list format."
        print("Initial catalog size:", len(self.__catalog))
        if (len(self.__path_list) == 1 and type(self.__path_list[0]) == str):
            self.__check_folder_for_simulations(self.__path_list[0])
        elif type(self.__path_list[0]) == str:
            for path in self.__path_list:
                self.__check_folder_for_simulations(path)
        else:
            raise ValueError("path format not recognized")
        print("Final catalog size:", len(self.__catalog))
        self.__save_catalog()

    def add_entry(self, simulation_name, simulation_path):
        assert type(simulation_name) == str, "The name of the simulation MUST be a string"
        assert type(simulation_path) == str, "The path of the simulation MUST be a string"
        assert os.path.exists(os.path.join(simulation_path, simulation_name)), \
            "The selected simulation does not exists or you do not have the permission to access"
        self.__catalog.append(self.__read_simulations_parameters(simulation_name, simulation_path))
        self.__save_catalog()
    
    def remove_entry(self, simulation_name, simulation_path = None):
        assert type(simulation_name) == str, "The name of the simulation MUST be a string"
        assert type(simulation_path) == str or simulation_path is None, "The path of the simulation MUST be a string"
        if simulation_path is None:
            sure = ''
            while sure not in ['Y', 'n']:
                sure = input("You are about to delete all entries called " + simulation_name + ", are you sure? (Y/n) ")
            if sure == 'n':
                return None
            
            for simulation in self.__catalog:
                if sure == 'Y':
                    if simulation["name"] == simulation_name:
                        self.__catalog.remove(simulation)
                else:
                    if simulation["name"] == simulation_name and simulation["location"] == simulation_path:
                        self.__catalog.remove(simulation)
                        break
        self.__save_catalog()
        
    def __check_save_path(self, save_name, save_folder):
        while not (os.path.exists(save_folder) and os.path.isdir(save_folder)):
            save_folder = input("Please insert a valid save folder path.")
        path_save = os.path.join(save_folder, save_name + '.json')
        path_save_readme = os.path.join(save_folder, 'README_' + save_name + '.txt')
        if not os.path.exists(path_save):
            return path_save, path_save_readme
        
        over_write = ''
        while over_write not in ['Y', 'n']:
            over_write = input("File already exists. Would you like to overwrite it? (Y/n) ")
        if over_write == 'Y':
            sure = ''
            while sure not in ['Y', 'n']:
                sure = input("Are you sure? (Y/n) ")
            if sure == 'Y':
                return path_save, path_save_readme
        if over_write == 'n' or sure == 'n':
            save_name = input("Please insert a new save_name: ")
            return self.__check_save_path(save_name, save_folder)
                
            
    def __read_catalog(self, path_to_catalog):
        if path_to_catalog is not None and os.path.exists(path_to_catalog):
            with open(path_to_catalog) as infile:
                catalog = json.load(infile)
        else:
            catalog = []
        return catalog
    

    def __remove_redundant_folders(self, dirs):
        """
        Removes the Initial models and EOS folders from a list of directories
        """
        while 'Initial_Models' in dirs:
            dirs.remove('Initial_Models')
        while 'EOS' in dirs:
            dirs.remove('EOS')
        return dirs
    
    def __polish_path(self, string, remove_bars = True, remove_points = True):
        if remove_bars:
            while string.find('/') != -1:
                string = string[string.find('/')+1:]
        if remove_points:
            while string.find('.') != -1:
                string = string[:string.find('.')]
        return string

    def __check_existence(self, folder, path):
        """
        Run the catalog and check if the simulation is already there. In case of previous
        denied access the simulation is removed and checked again.
        """
        exists = False
        for simulation in self.__catalog:
            if simulation["name"] == folder and simulation["location"] == path \
                and "access" not in simulation.keys():
                exists = True
                if simulation["Heger_model"] == "original parfile not found":
                    self.__catalog.remove(simulation)
                    exists = False
                break
            elif simulation["name"] == folder and simulation["location"] == path \
                and "access"  in simulation.keys():
                self.__catalog.remove(simulation)
                break
        return exists

    def __sort_keywords(self, dictionary):
        """
        Sorts the keys of a single simulation dictionary.
        """

        if not dictionary["magnetic_fields"]:
            keys = ["name", "location", "dimensions", "NS_EOS", "Heger_model", "gravity", "neutrinos",
                    "gravitational_potential", "lapse_function", "total_time", "bounce_time", "inner_dr", 
                    "nx", "ny", "nz", "omega", "magnetic_fields", "simulation_started", "simulation_ended", 
                    "nucleosynthesis_computed"]
        else:
            keys = ["name", "location", "dimensions", "NS_EOS", "Heger_model", "gravity", "neutrinos",
                "gravitational_potential", "lapse_function", "total_time", "bounce_time", "inner_dr", 
                "nx", "ny", "nz", "omega", "magnetic_fields", "poloidal_b_field", "toroidal_b_field",
                "simulation_started", "simulation_ended", "nucleosynthesis_computed"]
            
        if "comment" in dictionary.keys():
            keys.append("comment")
        return {key: dictionary[key] for key in keys}
    
    def __read_simulations_parameters(self, folder, simulation_path):
        sim = SimulationAnalysis(folder, simulation_folder_path = simulation_path)
        parameter_dictionary = {}
        parameter_dictionary["name"] = folder
        parameter_dictionary["location"] = simulation_path
        parameter_dictionary["dimensions"] = sim.dim
        parameter_dictionary["inner_dr"] = sim.cell.dr(sim.ghost)[0]
        parameter_dictionary["nx"] = sim.cell.radius(sim.ghost).size
        parameter_dictionary["ny"] = 1
        parameter_dictionary["nz"] = 1
        if sim.dim > 1:
            parameter_dictionary["ny"] = sim.cell.theta(sim.ghost).size
            if sim.dim > 2:
                parameter_dictionary["nz"] = sim.cell.phi(sim.ghost).size
        #Neutrino scheme: there is no flag for the neutrino scheme for now.
        #Since most simulations use the Aenus-ALCAR nu scheme, this is set by default
        parameter_dictionary["neutrinos"] = "Aenus-ALCAR"
        #equations and progenitors
        parfiles = os.listdir(sim.par_path)
        for parfile in parfiles:
            check = all(item in ["NS_EOS", "Heger_model", "gravity", "gravitational_potential", "lapse_function"] for \
                        item in parameter_dictionary.keys())
            if check:
                break
            try:
                namelist = f90nml.read(os.path.join(sim.par_path, parfile))
                if 'SHENEOSPARS' in namelist:
                    parameter_dictionary["NS_EOS"] = self.__polish_path(namelist['SHENEOSPARS']['SHEN_TBFILE'])
                if 'HEGERPARS' in namelist:
                    parameter_dictionary["Heger_model"] = self.__polish_path(namelist['HEGERPARS']['HEGER_MODEL'], remove_points = False)
                    if 'omgadd' in namelist['HEGERPARS'] and not 'omgmult' in namelist['HEGERPARS']:
                        parameter_dictionary["omega"] = namelist['HEGERPARS']['omgadd']
                if 'PHYSSYST' in namelist:
                    if namelist['PHYSSYST']['RELATIVISTIC']:
                        parameter_dictionary["gravity"] = 'Pseudo-relativistic'
                    else:
                        parameter_dictionary["gravity"] = 'Newtonian'
                if 'GRAVPARS' in namelist:
                    parameter_dictionary["gravitational_potential"] = namelist['GRAVPARS']['MDPOT']
                    parameter_dictionary["lapse_function"] = namelist['GRAVPARS']['LAPSE_FORM']
                if 'AXIVECPOTPARS' in namelist:
                    if 'b0' in namelist['AXIVECPOTPARS'] and 'bt' in namelist['AXIVECPOTPARS']:
                        if namelist['AXIVECPOTPARS']['b0'] !=0 and namelist['AXIVECPOTPARS']['bt'] !=0:
                            parameter_dictionary["magnetic_fields"] = True
                            parameter_dictionary["poloidal_b_field"] = namelist['AXIVECPOTPARS']['b0']
                            parameter_dictionary["toroidal_b_field"] = namelist['AXIVECPOTPARS']['bt']
            except:
                continue
        if not "NS_EOS" in parameter_dictionary.keys():
            parameter_dictionary["NS_EOS"] = "Access denied"
            
        if not "Heger_model" in parameter_dictionary.keys():
            run_parfiles = os.listdir(os.path.join(sim.par_path, '.run'))
            for parfile in run_parfiles:
                if "Heger_model" in parameter_dictionary.keys():
                    break
                try:
                    namelist = f90nml.read(os.path.join(sim.par_path, '.run', parfile))
                    if 'HEGERPARS' in namelist:
                        parameter_dictionary["Heger_model"] = self.__polish_path(namelist['HEGERPARS']['HEGER_MODEL'])
                        if 'omgadd' in namelist['HEGERPARS'] and not 'omgmult' in namelist['HEGERPARS']:
                            parameter_dictionary["omega"] = namelist['HEGERPARS']['omgadd']
                    if 'AXIVECPOTPARS' in namelist:
                        if 'b0' in namelist['AXIVECPOTPARS'] and 'bt' in namelist['AXIVECPOTPARS']:
                            if namelist['AXIVECPOTPARS']['b0'] !=0 and namelist['AXIVECPOTPARS']['bt'] !=0:
                                parameter_dictionary["magnetic_fields"] = True
                                parameter_dictionary["poloidal_b_field"] = namelist['AXIVECPOTPARS']['b0']
                                parameter_dictionary["toroidal_b_field"] = namelist['AXIVECPOTPARS']['bt']
                except:
                    continue
        if not "Heger_model" in parameter_dictionary.keys():
            parameter_dictionary["Heger_model"] = "original parfile not found"
        #time
        parameter_dictionary["bounce_time"] = sim.time_of_bounce_rho()
        file_list = sim.file_list_hdf()
        err = True
        i = -1
        while err and i>-len(file_list):
            try:
                data_h5 = sim.open_h5(file_list[i])
                parameter_dictionary["total_time"] = sim.time(data_h5)[0]
                sim.close_h5(data_h5)
                err = False
            except:
                i -= 1
                parameter_dictionary["comment"] = "Unable to open last hdf file(s)"
        if err:
            parameter_dictionary["comment"] = "Unable to open last hdf file(s)"
        data_h5 = sim.open_h5(file_list[0])
        #omega and b fields
        if not "poloidal_b_field" in parameter_dictionary.keys() and \
            not "toroidal_b_field" in parameter_dictionary.keys():
            try:
                b_field_pol = sim.poloidal_magnetic_field(data_h5)
                b_field_tor = sim.toroidal_magnetic_field(data_h5)
                parameter_dictionary["magnetic_fields"] = True
                if sim.dim == 1:
                    parameter_dictionary["poloidal_b_field"] = (b_field_pol).max()
                    parameter_dictionary["toroidal_b_field"] = (b_field_tor).max()
                elif sim.dim == 2:
                    parameter_dictionary["poloidal_b_field"] = (b_field_pol.mean(axis = 0)).max()
                    parameter_dictionary["toroidal_b_field"] = (b_field_tor.mean(axis = 0)).max()
                else:
                    parameter_dictionary["poloidal_b_field"] = (b_field_pol.mean(axis = (0,1))).max()
                    parameter_dictionary["toroidal_b_field"] = (b_field_tor.mean(axis = (0,1))).max()
            except:
                parameter_dictionary["magnetic_fields"] = False
        if "poloidal_b_field" in parameter_dictionary.keys() and \
            "toroidal_b_field" in parameter_dictionary.keys():
            if parameter_dictionary["poloidal_b_field"] == 0 and parameter_dictionary["toroidal_b_field"] == 0:
                parameter_dictionary["magnetic_fields"] = False
                del parameter_dictionary["poloidal_b_field"]
                del parameter_dictionary["toroidal_b_field"]
        
        if not "omega" in parameter_dictionary.keys():
            try:
                omg = sim.omega(data_h5)
                if sim.dim == 1:
                    parameter_dictionary["omega"] = (omg).max()
                elif sim.dim == 2:
                    parameter_dictionary["omega"] = (omg.mean(axis = 0)).max()
                else:
                    parameter_dictionary["omega"] = (omg.mean(axis = (0,1))).max()
            except:
                    parameter_dictionary["omega"] = 0
            if parameter_dictionary["omega"] < 1e-5:
                parameter_dictionary["omega"] = 0
        sim.close_h5(data_h5)
        #dates
        min_date = datetime.date.fromtimestamp(pathlib.Path(os.path.join(sim.hdf_path, file_list[0])).stat().st_mtime)
        max_date = datetime.date.fromtimestamp(pathlib.Path(os.path.join(sim.hdf_path, file_list[0])).stat().st_mtime)
        for file in file_list[1:]:
            tmp_date = datetime.date.fromtimestamp(pathlib.Path(os.path.join(sim.hdf_path, file)).stat().st_mtime)
            if tmp_date > max_date:
                max_date = tmp_date
            if tmp_date < min_date:
                min_date = tmp_date
        parameter_dictionary["simulation_started"] = min_date.strftime('%d/%m/%Y')
        parameter_dictionary["simulation_ended"] = max_date.strftime('%d/%m/%Y')
        parameter_dictionary["nucleosynthesis_computed"] = ""
        return self.__sort_keywords(parameter_dictionary)

    def __save_catalog(self):
        self.__catalog = json.dumps(self.__catalog, indent=4)
        with open(self.__save_path, 'w') as outfile:
            outfile.write(self.__catalog)
        with open(self.__save_README, 'w') as readme:
            readme.write("Thank you for creating a CCSN catalog using this Python script!!\n" + \
                          "Please pay attention to the following points:\n" + \
                          " - Time of bounce is calculated using the maximum density, i.e. when it reaches 2.5e14 g/cm3;\n" + 
                          " - Omega, and poloidal and toroidal magnetic fields are calculated in one of two ways:\n" + \
                          "   + If the progenitor model has no prior b or omega and it is added to it, we take those written in the parfile as data;\n" + \
                          "   + If the parfile is missing or the progenitor model has b or omega, we average our data in azimuthal and polar angles, " + \
                          "reducing them to radial profiles and taking their maximum.\n" + \
                          "   This last approach has the disadvantage of being \"initial step dependent\".\n" + \
                          "\n\n\nGrazie per l'attenzione ;-P")
        

    def __check_folder_for_simulations(self, path):
        try:
            dirs = self.__remove_redundant_folders(os.listdir(path))
        except:
            return None
        for folder in dirs:
            path_subfolder = os.path.join(path, folder)
            print('\t', path_subfolder)
            try:
                subfolders = self.__remove_redundant_folders(os.listdir(path_subfolder))
            except:
                continue
            if 'outp-hdf' in subfolders:
                try:
                    if len(os.listdir(os.path.join(path_subfolder, 'outp-hdf'))) < 6:
                        continue
                except:
                    continue
                
                if self.__check_existence(folder, path):
                    continue
                try:
                    self.__catalog.append(self.__read_simulations_parameters(folder, path))
                except Exception as e:
                    print("EXCEPTION:", e)
                    self.__catalog.append({"name": folder, "location": path, "access": "denied"})
            else:
                self.__check_folder_for_simulations(path_subfolder)


