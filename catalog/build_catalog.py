from catalog import catalog
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--catalog-name', type=str, required=True,
                    help="Name used to save the catalog ")
parser.add_argument('--paths-to-include', nargs='+', default=None,
                    help="List of paths to check for simulations.")
parser.add_argument('--path-to-previous-catalog', default=None, type=str,
                    help="Path to catalog to update.")
parser.add_argument('--save-folder', type=str, default='.',
                    help="Path in which to save the catalog.")
parser.add_argument('--remove-simulation', action='store_true', default=False)
parser.add_argument('--add-entry', action='store_true', default=False)
parser.add_argument('--simulation-name', type=str, default=None,
                    help="Name of the simulation to remove or add")
parser.add_argument('--simulation-path', type=str, default=None,
                    help="Path of the simulation to remove or add.")
args = parser.parse_args()

cat = catalog(save_name = args.catalog_name,
              path_list = args.paths_to_include,
              path_to_previous_catalog = args.path_to_previous_catalog,
              save_folder = args.save_folder)

if args.remove_simulation:
    cat.remove_entry(simulation_name = args.simulation_name,
                     simulation_path = args.simulation_path)
if args.add_entry:
    cat.add_entry(simulation_name = args.simulation_name,
                  simulation_path = args.simulation_path)
    
cat.build_catalog()