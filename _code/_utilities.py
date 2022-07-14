import numpy as np

from statistics import NormalDist
from scipy.stats import norm


def calculate_rwa(df,
                  pd='pd', lgd='lgd', ead='ead', maturity='maturity',
                  rw='rw_calc', rwa='rwa_calc',
                  drop_interim_columns=True):
    """
    Calculates RWA on facility level according to CRR par 153 formula (based on PD, LGD, EAD and Maturity)
    :param df: DataFrame on facility level
    :param pd: column to be used as pd estimation
    :param lgd: column to be used as lgd estimation
    :param ead: column to be used as ead estimation
    :param maturity: column to be used as effective maturity
    :param rw: column added to DataFrame with risk weight value
    :param rwa: column added to DataFrame with risk weighted assets value
    :param drop_interim_columns: if True, columns used for interim calculation are dropped from returned DataFrame
    """

    # Calculate maturity adjustment factor [b]
    df['rw_calc_b'] = (0.11852 - 0.05478 * np.log(df[pd])) ** 2
    assert df['rw_calc_b'].isnull().sum() == 0

    # Calculate maturity component
    df['rw_calc_part_maturity'] = (1 + (df[maturity] - 2.5) * df['rw_calc_b']) / (
                1 - 1.5 * df['rw_calc_b'])
    assert df['rw_calc_part_maturity'].isnull().sum() == 0

    # Calculate coefficient of correlation
    df['rw_calc_r'] = 0.12 * (1 - np.e ** (-50 * df[pd])) / (1 - np.e ** (-50)) \
                      + 0.24 * (1 - (1 - np.e ** (-50 * df[pd])) / (1 - np.e ** (-50)))
    assert df['rw_calc_r'].isnull().sum() == 0

    # Calculate sum of inverse cumulative distribution function components
    df['rw_inverse_comp_sum'] = (1 / np.sqrt(1 - df['rw_calc_r'])) * df[pd].apply(NormalDist().inv_cdf) + \
                                np.sqrt(df['rw_calc_r'] / (1 - df['rw_calc_r'])) * NormalDist().inv_cdf(0.999)
    assert df['rw_inverse_comp_sum'].isnull().sum() == 0

    # Calculate PD LGD component
    df['rw_calc_part_pd_lgd_component'] = df[lgd] * df['rw_inverse_comp_sum'].apply(norm.cdf) - df[lgd] * df[pd]

    # Calculate risk weight and RWAs
    df[rw] = df['rw_calc_part_pd_lgd_component'] * df['rw_calc_part_maturity'] * 12.5 * 1.06
    df[rwa] = df[rw] * df[ead]

    # Drop columns added for interim calculation
    if drop_interim_columns:
        cols_to_drop = ['rw_calc_b', 'rw_calc_part_maturity', 'rw_calc_r',
                        'rw_inverse_comp_sum', 'rw_calc_part_pd_lgd_component']
        df.drop(columns=cols_to_drop, inplace=True)

    return df
