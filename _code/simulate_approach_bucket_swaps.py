import numpy as np
import pandas as pd

from _code._config import Confs
config = Confs()

from _code._utilities import calculate_rwa


def run_shuffling(df, df_deals, df_swaps, random_state):

    print(f'Bucket swaps approach: starting simulation with random state = {random_state}...')

    # Create deep copy to avoid over writing
    df_deals = df_deals.copy(deep=True)
    df = df.copy(deep=True)

    # Itterate through movements and simulate swaps
    df['bucket_new'] = np.nan
    df['pd_new'] = np.nan

    for index, row in df_swaps.iterrows():
        # Unpack parameters
        from_bucket = row['from_bucket']
        to_bucket = row['to_bucket']
        swaps = row['swaps']
        # print(f'Simulating swaps between {from_bucket} and {to_bucket} for n={swaps}')

        # Mark random obligors for swapping
        df_from = df[(df['bucket_new'].isnull()) & (df['bucket'] == from_bucket)].copy(deep=True)
        df_to = df[(df['bucket_new'].isnull()) & (df['bucket'] == to_bucket)].copy(deep=True)
        # print(f'   Shape of availaible df_from: {df_from.shape[0]}')
        # print(f'   Shape of availaible df_to: {df_to.shape[0]}')

        # Get IDs of obligors for swaps
        if swaps > 0:

            # Raise errors if number of remaining observations in buckets is not sufficient to execute swaps matrix
            if df_from.shape[0] < swaps:
                print(f'   Error: Not sufficient number of observation in {from_bucket} to execute swaps matrix')
                assert False
            if df_to.shape[0] < swaps:
                print(f'   Error: Not sufficient number of observation in {to_bucket} to execute swaps matrix')
                assert False

            df_from = df_from.sample(n=swaps, random_state=random_state)
            df_to = df_to.sample(n=swaps, random_state=random_state)

            df_from = df_from[['cis_code', 'pd', 'bucket']]
            df_from.rename(columns={'cis_code': 'cis_code_from', 'pd': 'pd_from', 'bucket': 'bucket_from'},
                           inplace=True)
            df_from.reset_index(drop=True, inplace=True)

            df_to = df_to[['cis_code', 'pd', 'bucket']]
            df_to.rename(columns={'cis_code': 'cis_code_to', 'pd': 'pd_to', 'bucket': 'bucket_to'}, inplace=True)
            df_to.reset_index(drop=True, inplace=True)

            df_swap = pd.concat([df_from, df_to], axis=1)

            # Adjust PDs and buckets of from obligors
            df = pd.merge(
                df,
                df_swap.rename(columns={'cis_code_from': 'cis_code'}),
                on=['cis_code'], how='left', validate='1:1'
            )
            df['pd_new'] = df['pd_new'].fillna(df['pd_to'])
            df['bucket_new'] = df['bucket_new'].fillna(df['bucket_to'])
            df = df[['cis_code', 'pd', 'ead', 'bucket', 'pd_new', 'bucket_new']]

            # Adjust PDs and buckets of to obligors
            df = pd.merge(
                df,
                df_swap.rename(columns={'cis_code_to': 'cis_code'}),
                on=['cis_code'], how='left', validate='1:1'
            )
            df['pd_new'] = df['pd_new'].fillna(df['pd_from'])
            df['bucket_new'] = df['bucket_new'].fillna(df['bucket_from'])
            df = df[['cis_code', 'pd', 'ead', 'bucket', 'pd_new', 'bucket_new']]

    # For non-swaped obligors new bucket equals old bucket
    df['pd_new'] = df['pd_new'].fillna(df['pd'])
    df['bucket_new'] = df['bucket_new'].fillna(df['bucket'])

    # Assert that there is no change in average pd
    average_pd = df['pd'].mean()
    average_pd_new = df['pd_new'].mean()
    assert abs(average_pd - average_pd_new) < 0.00001
    # print(f'   Average PD before and after simulation: {round(100 * average_pd, 3)}%')

    # Check movement in weighted pd
    weighted_pd = (df['pd'] * df['ead']).sum() / df['ead'].sum()
    weighted_pd_new = (df['pd_new'] * df['ead']).sum() / df['ead'].sum()
    # print(f'   Weighted PD before simulation: {round(100 * weighted_pd, 3)}%')
    # print(f'   Weighted PD after simulation: {round(100 * weighted_pd_new, 3)}%')

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

    # Create list with key results for simulation
    row = [
        random_state,
        average_pd,
        average_pd_new,
        weighted_pd,
        weighted_pd_new,
        rwa,
        rwa_new
    ]
    return row


def main(n_simulations):
    # Read obligor data
    df = pd.read_csv(config.data_path + 'clean_data/clean_obligor_data_merged.csv')

    # Rename pd and mgs columns for simplicity
    df.rename(columns={'pd_updated': 'pd', 'mgs_updated': 'mgs'}, inplace=True)

    # Attach bucket information
    config_mgs = pd.read_csv(config.data_path + 'clean_data/config_mgs_mapping.csv',
                             usecols=['mgs', 'bucket'])
    df = pd.merge(df, config_mgs, on=['mgs'], how='left', validate='m:1')
    assert df['bucket'].isnull().sum() == 0

    # Create DataFrame with counts
    df_counts = pd.DataFrame(df['bucket'].value_counts())
    df_counts.reset_index(drop=False, inplace=True)
    df_counts.rename(columns={'index': 'bucket', 'bucket': 'obs'}, inplace=True)

    print(f'Bucket swaps approach: Obtained distribution by buckets:')
    print(df_counts)
    print('')

    # Get migration scenario
    df_swaps = pd.read_csv(config.data_path + 'clean_data/config_swaps_matrix.csv')

    # Add number of observations to be swapped
    df_swaps = pd.merge(
        df_swaps,
        df_counts.rename(columns={'bucket': 'from_bucket'}), on=['from_bucket'],
        how='left', validate='m:1')
    df_swaps['swaps'] = (df_swaps['percent'] * df_swaps['obs']).astype(int)
    df_swaps.drop(columns=['obs'], inplace=True)

    print('Bucket swaps approach: Obtained movement list')
    print(df_swaps)
    print('')

    # Read deals data for capital calculation
    df_deals = pd.read_csv(config.data_path + 'clean_data/clean_deal_data_merged.csv')

    # Run simulations
    random_states = list(range(n_simulations))
    rows = []

    for random_state in random_states:
        row = run_shuffling(df, df_deals, df_swaps, random_state)
        rows.append(row)

    # Create DataFrame to store the results
    columns = [
        'random_state',
        'average_pd',
        'average_pd_new',
        'weighted_pd',
        'weighted_pd_new',
        'rwa',
        'rwa_new'
    ]
    df_result = pd.DataFrame(rows, columns=columns)

    # Save result
    df_result.to_excel(config.data_path + 'result_data/result_bucket_swaps.xlsx', index=False)


if __name__ == '__main__':
    main(n_simulations=1000)
