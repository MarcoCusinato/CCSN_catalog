# CCSN CATALOG
## Introduction
A small `Python` script that looks for Core Collapse supernova simulations produced with the Aenus-ALCAR code. The basic idea behind its work is to recursively search for non-empty `outp-hdf` directories in a given path. Once one of these is found, it uses either my [analysis tool](https://github.com/MarcoCusinato/scidata) (if installed) or a smaller basic version of it (included with this script in `Tools/`) to retrieve all the information about the simulation.

## Requirements
The requirements are very basic and included in the `Tools/requiremnts.txt`:
 - [h5py](https://www.h5py.org/)
 - [numpy](https://numpy.org/doc/stable/index.html)
 - [f90nml](https://pypi.org/project/f90nml/)

To install all of them at once just run:
```
pip install -r catalog/Tools/requiremnets.txt
```
## What it does and how to use it
To generate or update a catalog just run the provided `sh` file after adding the path of an already generate catalog (in case of update) and the list of paths to scan. For example:
```
python ./catalog/build_catalog.py \
  --catalog-name your_catalog_name \
  --paths-to-include /path/to/folder1/ /path/to/folder2/ \
  --path-to-previous-catalog None #if updating, here is where the catalog to update goes
```
In case you would like to delete an entry in the catalog you can either open the catalog and manually do that or use the built-in method:
```
python ./catalog/build_catalog.py --catalog-name your_catalog_name --path-to-previous-catalog /path/to/existing/catalog --remove-simulation --simulation-name name_of_your_simulation --simulation-path /path/to/simulation
```
Be aware that if you do not specify the simulation path every simulation with the same will be removed.\n
In a similar fashion, we can add an entry with the build-in method, however in this case we must specify both the name and the path of the simulation.
```
python ./catalog/build_catalog.py --catalog-name your_catalog_name --path-to-previous-catalog /path/to/existing/catalog --add-entry --simulation-name name_of_your_simulation --simulation-path /path/to/simulation
```
In both cases you can also use the provided `sh` file (`add_entry.sh` and `remove_entry.sh`).
## Known issues
Since there is no flag to indicate which neutrino scheme is used that has to be manually set.
The same goes for the nucleosynthesis key.