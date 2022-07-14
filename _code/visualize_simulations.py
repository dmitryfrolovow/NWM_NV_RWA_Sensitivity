import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import seaborn as sns

from _code._config import Confs
config = Confs()


def main():

    # Read data with simulations result - adjust depending on simulation to be visualised
    results_tag = 'result_bucket_swaps'
    df = pd.read_excel(config.data_path + f'result_data/{results_tag}.xlsx')

    # Define parameters for plotting
    plot_configurations = [
        {
            'column_name_pre_stress': 'rwa',
            'column_name_after_stress': 'rwa_new',
            'tag': 'RWA',
            'dimension': 'M EUR',
            'dimension_function': lambda x: round(x / 1e+6)
        },
        {
            'column_name_pre_stress': 'weighted_pd',
            'column_name_after_stress': 'weighted_pd_new',
            'tag': 'Weighted PD',
            'dimension': '%',
            'dimension_function': lambda x: round(x * 100, 2)
        }
    ]

    # Iterate and plot configurations
    for plot_configuration in plot_configurations:

        # Unpack plot configuration
        column_name_pre_stress = plot_configuration['column_name_pre_stress']
        column_name_after_stress = plot_configuration['column_name_after_stress']
        tag = plot_configuration['tag']
        dimension = plot_configuration['dimension']
        dimension_function = plot_configuration['dimension_function']

        # Plot distribution
        sns.distplot(x=df[column_name_after_stress], hist=True, kde=False,
                     color='darkblue',
                     hist_kws={'edgecolor': 'black'},
                     kde_kws={'linewidth': 1})

        # Add key verticals - pre-stress value, p50 stress value, p75 stress value
        value_now = df[column_name_pre_stress].mean()
        plt.axvline(value_now, color='grey')

        value_p50 = np.percentile(df[column_name_after_stress], 50)
        plt.axvline(value_p50, color='green')

        value_p75 = np.percentile(df[column_name_after_stress], 75)
        plt.axvline(value_p75, color='red')

        # Add title to graph
        plt.title(f'{tag} distribution,'
                  f'starting {tag} is {dimension_function(value_now):,}{dimension} \n'
                  f'Median {tag} is {dimension_function(value_p50):,}{dimension},'
                  f'75th perc. {tag} is {dimension_function(value_p75):,}{dimension}')

        # Save visualization
        plt.savefig(config.data_path + f'result_data/graphs/{results_tag}_{column_name_after_stress}_distribution.png')
        plt.close()


if __name__ == '__main__':
    main()
