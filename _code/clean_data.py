import pandas as pd

from _code._utilities import calculate_rwa

from _code._config import Confs
config = Confs()


def clean_data_incumbent():
    # Read data
    file_path = 'raw_data/OWC_EXTRACT2.xlsx'
    df = pd.read_excel(config.data_path + file_path)

    # Rename columns
    df.columns = df.columns.str.lower()
    rename_dict = {
        #'rp_cis_code': 'rp_cis_code',
        'cis_code': 'cis_code',
        'pd_model': 'pd_model',
        'approved_approach_code': 'approach',
        'irb_ead': 'ead',
        'irb_rwa': 'rwa_incumbent_data',
        #'std_ead': 'std_ead',
        #'std_rwa': 'std_rwa',
        #'deal_id': 'deal_id',
        'lgd': 'lgd',
        'pd': 'pd_incumbent',
        #'curr_mgs_grade': 'mgs_incumbent',
        'effective_maturity_yrs': 'maturity',
        'grading_id': 'grading_id',
        'adj_cascade_rule_desc': 'adj_cascade_rule_desc',
        'adjusted_parent_cis_code': 'adjusted_parent_cis_code',
        'adjusted_cascade_flag': 'adjusted_cascade_flag',
    }
    columns_to_keep = list(rename_dict.keys())
    df = df[columns_to_keep]
    df.rename(columns=rename_dict, inplace=True)

    # Assert that certain columns are unique per obligor
    columns_to_test = ['pd_incumbent']
    agg_dict = {c: 'nunique' for c in columns_to_test}
    df_check = df.groupby(by=['cis_code'], as_index=False).agg(agg_dict)

    for c in columns_to_test:
        assert df_check[c].max() == 1

    del df_check

    # Exclude observations with PD = 1.0
    mask = (df['pd_incumbent'] == 1)
    assert df.loc[mask, 'rwa_incumbent_data'].sum() == 0
    df = df[~mask]

    # Reset index
    df.reset_index(drop=True, inplace=True)

    # Save DataFrame at deal level
    df.to_csv(config.data_path + 'clean_data/interim_deal_data_incumbent.csv', index=False)


def clean_data_updated():

    # Read data
    file_path = 'raw_data/OWC_EXTRACT3.xlsx'
    df = pd.read_excel(config.data_path + file_path)

    # Rename columns
    df.columns = df.columns.str.lower()
    rename_dict = {
        'le_cis_code': 'cis_code',
        'cascade_flag': 'cascade_flag',
        'asis_grade': 'mgs_incumbent',
        'tobe_grade': 'mgs_updated',
        'sum of exposure': 'ead',
        'sum of current rwa': 'rwa_incumbent_data',
        'sum of new rwa': 'rwa_updated_data',
        'sum of diff rwa': 'rwa_diff',
        'sum of current el': 'el_incumbent',
        'sum of new el': 'el_updated',
        'sum of diff_el': 'el_diff'
    }
    columns_to_keep = list(rename_dict.keys())
    df = df[columns_to_keep]
    df.rename(columns=rename_dict, inplace=True)

    # Exclude observations with PD = 1.0
    mask = (df['mgs_updated'] == 27)
    assert df.loc[mask, 'rwa_incumbent_data'].sum() == 0
    assert df.loc[mask, 'rwa_updated_data'].sum() == 0
    df = df[~mask]

    # Save DataFrame at obligor level
    df.to_csv(config.data_path + 'clean_data/interim_obligor_data_updated.csv', index=False)


def merge_data():

    # Read data
    path_incumbent = config.data_path + 'clean_data/interim_deal_data_incumbent.csv'
    path_updated = config.data_path + 'clean_data/interim_obligor_data_updated.csv'
    df_incumbent = pd.read_csv(path_incumbent)
    df_updated = pd.read_csv(path_updated)

    # Assert that two datasets match in terms of obligors
    obligors_incumbent = set(list(df_incumbent['cis_code'].unique()))
    obligors_updated = set(list(df_updated['cis_code'].unique()))
    assert len(obligors_incumbent - obligors_updated) == 0
    assert len(obligors_updated - obligors_incumbent) == 0

    # Merge updated grades to incumbent deal dataset
    df = pd.merge(
        df_incumbent,
        df_updated[['cis_code', 'mgs_updated']],
        on=['cis_code'], how='left', validate='m:1'
    )

    # Add PDs for updated mgs based on scale
    config_mgs = pd.read_csv(config.data_path + 'clean_data/config_mgs_mapping.csv',
                             usecols=['mgs', 'pd_mid'])
    df = pd.merge(
        df,
        config_mgs.rename(columns={'mgs': 'mgs_updated', 'pd_mid': 'pd_updated'}),
        on=['mgs_updated'], how='left', validate='m:1'
    )

    # Calculate RWA based on Basel II formula
    df = calculate_rwa(
        df,
        pd='pd_updated',
        rw='rw_updated_calc', rwa='rwa_updated_calc')
    df = calculate_rwa(
        df,
        pd='pd_incumbent',
        rw='rw_incumbent_calc', rwa='rwa_incumbent_calc'
    )

    # Change currency to EUR from GBP
    columns_to_fx = ['ead', 'rwa_updated_calc', 'rwa_incumbent_calc', 'rwa_incumbent_data']
    fx_rate = 1.1902636  # December 2021
    for col in columns_to_fx:
        df[col] = df[col] * fx_rate

    # Save DataFrame at deal level
    df.to_csv(config.data_path + 'clean_data/clean_deal_data_merged.csv', index=False)

    # Aggregate to obligor level
    agg_dict = {
        'mgs_updated': 'first',
        'pd_updated': 'first',

        'ead': 'sum',

        'rwa_updated_calc': 'sum',
        'rwa_incumbent_calc': 'sum',
        'rwa_incumbent_data': 'sum'
    }
    df_obligor = df.groupby(by=['cis_code'], as_index=False).agg(agg_dict)

    # Merge rwa_updated
    df_obligor = pd.merge(
        df_obligor,
        df_updated[['cis_code', 'rwa_updated_data']],
        on=['cis_code'], how='outer', validate='1:1'
    )

    # Save DataFrame at obligor level
    df_obligor.to_csv(config.data_path + 'clean_data/clean_obligor_data_merged.csv', index=False)


def main():
    clean_data_incumbent()
    clean_data_updated()
    merge_data()


if __name__ == '__main__':
    main()
