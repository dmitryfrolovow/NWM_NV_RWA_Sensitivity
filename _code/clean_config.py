import numpy as np
import pandas as pd

from _code._config import Confs

config = Confs()


def clean_swaps_matrix():
    # Read raw config
    swaps_matrix_path = config.data_path + 'config_data/config_pd_swaps.xlsx'
    swaps_matrix = pd.read_excel(swaps_matrix_path, sheet_name='swaps_matrix', skiprows=4)

    cols_to_drop = [c for c in swaps_matrix.columns if 'Unnamed' in c]
    swaps_matrix.drop(columns=cols_to_drop, inplace=True)

    # Get list of buckets
    buckets = list(swaps_matrix['bucket'].values)

    # Transform matrix into list of swaps to be executed
    rows = []
    for i in range(0, len(buckets)):
        for j in range(i, len(buckets)):
            from_bucket = buckets[i]
            to_bucket = buckets[j]
            percent = swaps_matrix.loc[swaps_matrix['bucket'] == from_bucket, to_bucket].values[0]
            row = [from_bucket, to_bucket, percent]
            rows.append(row)

    df_swaps = pd.DataFrame(data=rows, columns=['from_bucket', 'to_bucket', 'percent'])

    # Delete migrations within the same bucket
    df_swaps = df_swaps[df_swaps['from_bucket'] != df_swaps['to_bucket']]
    df_swaps.reset_index(drop=True, inplace=True)

    # Save cleaned data
    df_swaps.to_csv(config.data_path + 'clean_data/config_swaps_matrix.csv', index=False)


def clean_mgs_mapping():
    # Read raw config
    mgs_mapping_path = config.data_path + 'config_data/config_pd_swaps.xlsx'
    mgs_mapping = pd.read_excel(mgs_mapping_path, sheet_name='mgs_mapping', skiprows=11)

    cols_to_drop = [c for c in mgs_mapping.columns if 'Unnamed' in c]
    mgs_mapping.drop(columns=cols_to_drop, inplace=True)

    # Rename and truncate necessary columns
    mgs_mapping.columns = mgs_mapping.columns.str.lower()
    rename_dict = {
        'mgs': 'mgs',
        'low': 'pd_low',
        'mid': 'pd_mid',
        'high': 'pd_high',
        'bucket': 'bucket'
    }
    columns_to_keep = list(rename_dict.keys())
    mgs_mapping = mgs_mapping[columns_to_keep]
    mgs_mapping.rename(columns=rename_dict, inplace=True)

    # Save cleaned data
    mgs_mapping.to_csv(config.data_path + 'clean_data/config_mgs_mapping.csv', index=False)


def main():
    clean_swaps_matrix()
    clean_mgs_mapping()


if __name__ == '__main__':
    main()
