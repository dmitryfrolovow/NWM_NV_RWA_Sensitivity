import numpy as np
import pandas as pd

from _code._config import Confs
config = Confs()

from _code._utilities import calculate_rwa


def run_movements(df, df_deals, random_state,
                  approach='linear', approach_params=None):

    print(f'MGS movements approach: starting simulation with random state = {random_state}...')

    np.random.seed(random_state)

    # Calculate new MGS grade after shock
    upper_limit = -3
    lower_limit = 3

    if approach == 'linear':
        df['mgs_movement'] = np.random.randint(upper_limit, lower_limit + 1, df.shape[0])
    if approach == 'normal':
        mean = approach_params['mean']
        std_dev = approach_params['std_dev']

        df['mgs_movement'] = np.random.normal(loc=mean, scale=std_dev, size=df.shape[0])
        df['mgs_movement'] = df['mgs_movement'].round().astype(int)

        df.loc[df['mgs_movement'] >= lower_limit, 'mgs_movement'] = lower_limit
        df.loc[df['mgs_movement'] <= upper_limit, 'mgs_movement'] = upper_limit

    df['mgs_new'] = df['mgs'] + df['mgs_movement']
    df.loc[df['mgs_new'] >= 26, 'mgs_new'] = 26
    df.loc[df['mgs_new'] <= 1, 'mgs_new'] = 1

    # Attach new PD
    config_mgs = pd.read_csv(config.data_path + 'clean_data/config_mgs_mapping.csv',
                             usecols=['mgs', 'pd_mid'])
    df = pd.merge(
        df,
        config_mgs.rename(columns={'mgs': 'mgs_new', 'pd_mid': 'pd_new'}),
        on=['mgs_new'], how='left', validate='m:1'
    )

    # Merge new pds to deals
    df_deals = pd.merge(
        df_deals,
        df[['cis_code', 'pd_new']],
        on=['cis_code'], how='left', validate='m:1')

    # Calculate RWA given new PD
    df_deals = calculate_rwa(df_deals, pd='pd_new', rw='rw_updated_calc_new', rwa='rwa_updated_calc_new')
    rwa = df_deals['rwa_updated_calc'].sum()
    rwa_new = df_deals['rwa_updated_calc_new'].sum()
    # print(f'   Cumulative RWA before simulation: {round(rwa):,}')
    # print(f'   Cumulative RWA after simulation: {round(rwa_new):,}')

    # Assert that there is no change in average pd
    average_pd = df['pd'].mean()
    average_pd_new = df['pd_new'].mean()

    # Note mgs movements
    mgs_movement_median = df['mgs_movement'].median()
    mgs_movement_mean = df['mgs_movement'].mean()

    # Create list with key results for simulation
    row = [
        random_state,

        mgs_movement_median,
        mgs_movement_mean,

        average_pd,
        average_pd_new,
        rwa,
        rwa_new,
    ]

    # For
    for i in range(upper_limit, lower_limit + 1):
        n = (df['mgs_movement'] == i).sum()
        row = row + [n]

    return row


def main(n_simulations, approach='linear', approach_params=None):

    # Read obligor data
    df = pd.read_csv(config.data_path + 'clean_data/clean_obligor_data_merged.csv')

    # Read deals data for capital calculation
    df_deals = pd.read_csv(config.data_path + 'clean_data/clean_deal_data_merged.csv')

    # Rename pd and mgs columns for simplicity
    df.rename(columns={'pd_updated': 'pd', 'mgs_updated': 'mgs'}, inplace=True)

    # Simulate random movements in MGS

    # Run simulations
    random_states = list(range(n_simulations))
    rows = []

    for random_state in random_states:
        row = run_movements(df, df_deals, random_state, approach, approach_params)
        rows.append(row)

    # Create DataFrame to store the results
    columns = [
        'random_state',

        'mgs_movement_median',
        'mgs_movement_mean',

        'average_pd',
        'average_pd_new',
        'rwa',
        'rwa_new',

        'mgs_-3',
        'mgs_-2',
        'mgs_-1',
        'mgs_0',
        'mgs_1',
        'mgs_2',
        'mgs_3'
    ]
    df_result = pd.DataFrame(rows, columns=columns)

    # Save result
    if approach == 'linear':
        save_path = f'result_data/result_mgs_movements_{n_simulations}_{approach}.xlsx'
    if approach == 'normal':
        mean = approach_params["mean"]
        std_dev = approach_params["std_dev"]
        save_path = f'result_data/result_mgs_movements_{n_simulations}_{approach}_{mean}_{std_dev}.xlsx'

    df_result.to_excel(config.data_path + save_path, index=False)


if __name__ == '__main__':
    main(n_simulations=1000, approach='linear')
    # main(n_simulations=1000, approach='normal', approach_params={'mean': 0.0, 'std_dev': 1.5})
    # main(n_simulations=1000, approach='normal', approach_params={'mean': 0.0, 'std_dev': 2.0})
