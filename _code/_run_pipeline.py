from _code.clean_config import main as clean_config
from _code.clean_data import main as clean_data

from _code.simulate_approach_bucket_swaps import main as simulate_approach_bucket_swaps
from _code.simulate_approach_mgs_movements import main as simulate_approach_mgs_movements

from _code.visualize_simulations import main as visualize_simulations


def main(params=None):

    # Define pipeline parameters
    if params is None:
        params = {
            'clean_config': True,
            'clean_data': True,
            'simulate_approach_bucket_swaps': True,
            'simulate_approach_mgs_movements': True,
            'visualize_simulations': True
        }

    # Run configurations parsing
    if params['clean_config']:
        clean_config()

    # Run input data cleaning
    if params['clean_data']:
        clean_data()

    # Run RWA simulation approach with obligor swaps between buckets
    if params['simulate_approach_bucket_swaps']:
        simulate_approach_bucket_swaps(n_simulations=1000)

    # Run RWA simulation approach with mgs movements at the obligor level
    if params['simulate_approach_mgs_movements']:
        simulate_approach_mgs_movements(
            n_simulations=1000,
            approach='normal',
            approach_params={'mean': 0.0, 'std_dev': 1.5})

    # Run creation of distribution graphs
    if params['visualize_simulations']:
        visualize_simulations()


if __name__ == '__main__':
    main()
