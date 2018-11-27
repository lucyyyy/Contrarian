# Contrarian Strategy
###### 作者：林新凯
# > 数据来源为CSMAR

# 载入所需模块
import pandas as pd
import datetime as dt
from dateutil.relativedelta import relativedelta
from math import floor
import numpy as np
import itertools
from scipy import stats

# 从本地磁盘读取数据
path = r'C:\\Users\\KasperLin\\OneDrive for Business\\Work\\Quant\\Contrarian\\data'
year_path = r'\\year\\year.csv'
year = pd.read_csv(path + year_path)
month_path = r'\\month\\month.csv'
month = pd.read_csv(path + month_path)

# 清洗数据
year['Trdynt'] = pd.to_datetime(year['Trdynt'], format = '%Y')
month['Trdmnt'] = pd.to_datetime(month['Trdmnt'], format = '%b-%y')

data = month

def timedelta(base, delta):
    '''
    Parameters:
    -----------
        base: 日期，年-'YYYY'，月-'YYYY-MM'。(str)
        delta: 日期变动值，为正则向前变动，为负反之。(int)

    Return:
    -------
        变动后的日期值。(str)
    '''

    tn = (dt.datetime.strptime(base, '%Y-%m') + \
    relativedelta(months = delta)).strftime('%Y-%m')
    return tn

def rank(base, J, percentage = 0.2):

    '''
    Parameters:
    ----------
        base: 日期，年-'YYYY'，月-'YYYY-MM'。(str)
        J: 排序期。(int)
        percentage: 分层比例。(float)
    
    Return:
    ------
        按照排序期股票累计收益率降序排序的股票代码及其收益率列表。(pd.Series)
    '''

    start = timedelta(base, -J)
    end = timedelta(base, 1)

    rank = data[(data['Trdmnt'] > start) & (data['Trdmnt'] < end)]

    aggret = rank.groupby('Stkcd')['Mretwd'].sum()

    aggret.sort_values(inplace = True)

    length = floor(len(aggret) * percentage)

    winner_list = list(aggret.index[-length:])
    loser_list = list(aggret.index[0:length])

    return winner_list, loser_list

def hold_data(
    base, 
    J, 
    K, 
    percentage = 0.2, 
    large = False, 
    small = False, 
):

    '''
    Parameters:
    ----------
    base: 日期，月-'YYYY-MM'。(str)
    J: 排序期。(int)
    K: 持有期。(int)

    Parameters（可选）:
    ----------
    percentage: 分层比例，默认为0.2。(float)
    large: 是否只交易市值最大的前N个股票，默认为否(False)。(int / Bool)
    small: 是否只交易市值最小的前N个股票，默认为否(False)。(int / Bool)
    
    Return:
    ------
    赢家持有数据。(pd.DataFrame)
    输家持有数据。(pd.DataFrame)
    '''

    observe = data[data['Trdmnt'] == base]

    port = rank(base, J, percentage)
    w_list = port[0]
    l_list = port[1]

    if (large == False) | (small == False):
        pass

    elif large != False:
        large = list(observe.sort_values(by = 'Msmvttl').tail(large)['Stkcd'])
        w_list = set(large).intersection(w_list)
        l_list = set(large).intersection(l_list)

    elif small != False:
        small = list(observe.sort_values(by = 'Msmvttl').tail(small)['Stkcd'])
        w_list = set(small).intersection(w_list)
        l_list = set(small).intersection(l_list)
    
    start = timedelta(base, 0)
    end = timedelta(base, K+1)
    hold = data[(data['Trdmnt'] > start) & (data['Trdmnt'] < end)]
    w_hold = hold[hold['Stkcd'].isin(w_list)]
    l_hold = hold[hold['Stkcd'].isin(l_list)]

    return w_hold, l_hold

def hold_df(base, K, data, raw):

    '''
    Parameters:
    ----------
    base: 日期，月-'YYYY-MM'。(str)
    K: 持有期。(int)
    data: 用来处理加工的表格。(pd.DataFrame)
    raw: 原始持有数据。(pd.DataFrame)

    Return: 
    ------
    最终收益率表格。(pd.DataFrame)
    '''

    start = timedelta(base, 1)
    end = timedelta(base, K)

    stock_amount_list = []

    for i in range(timespan(start, end)):
        
        time = timedelta(start, i)
        stock_amount = len(raw[raw['Trdmnt'] == time])

        stock_amount_list.append(stock_amount)

    data['Stock Amount'] = stock_amount_list
    data['Return'] = data['Mretwd'] / data['Stock Amount']

    return data

def hold(
    base, 
    J, 
    K, 
    percentage = 0.2, 
    large = False, 
    small = False
):

    '''
    Parameters:
    ----------
    base: 日期，月-'YYYY-MM'。(str)
    J: 排序期。(int)
    K: 持有期。(int)

    Parameters（可选）:
    ----------
    percentage: 分层比例，默认为0.2。(float)
    large: 是否只交易市值最大的前N个股票，默认为否(False)。(int / Bool)
    small: 是否只交易市值最小的前N个股票，默认为否(False)。(int / Bool)
    
    Return:
    ------
    赢家逐期收益率。(float)
    输家逐期收益率。(float)
    '''

    root = hold_data(
        base = base, 
        J = J, 
        K = K, 
        percentage = 0.2, 
        large = large, 
        small = small
    )
    w_hold = root[0]
    l_hold = root[1]

    w_ret = w_hold.groupby('Trdmnt')['Mretwd'].sum()
    l_ret = l_hold.groupby('Trdmnt')['Mretwd'].sum()

    w_df = pd.DataFrame(w_ret)
    l_df = pd.DataFrame(l_ret)

    w_df = hold_df(base = base, K = K, data = w_df, raw = w_hold)
    l_df = hold_df(base = base, K = K, data = l_df, raw = l_hold)

    return w_df, l_df

def timespan(start, end):
    '''
    Parameters:
    ----------
    start: 开始时间。(str)
    end: 结束时间。(str)

    Return: 
    ------
    时间跨度。(int)
    '''
    start_date = dt.datetime.strptime(start, '%Y-%m')
    end_date = dt.datetime.strptime(end, '%Y-%m')
    length = relativedelta(end_date, start_date).years * 12 + \
    relativedelta(end_date, start_date).months + 1
    return length

def table(
    start, 
    end, 
    freq, 
    n_sample, 
    strategy = 'l', 
    percentage = 0.2, 
    large = False, 
    small = False
):

    '''
    Parameters: 
    ----------
    start: 开始时间，月-'YYYY-MM'。(str)
    end: 结束时间，月-'YYYY-MM'。(str)
    freq: 排序持有期观察频率。(int)
    n_sample: 排序持有期观察次数。(int)

    Parameters（可选）:
    ----------
    strategy: 交易策略，“赢家-输家”-'wl'、“单边输家”-'l'、“单边赢家”-'w'，默认为“赢家-输家”('wl')。(str)
    large: 是否只交易市值最大的前N个股票，默认为否(False)。(int / Bool)
    small: 是否只交易市值最小的前N个股票，默认为否(False)。(int / Bool)
    
    Return:
    ------
    最终表格。(pd.DataFrame)
    '''

    length = timespan(start, end)

    if freq == 1:
        axis = list(range(1, length + 1))[:n_sample]
    else:
        axis = [1] + list(range(
            freq, 
            freq * (length // freq) + 1, 
            freq
        ))[:(n_sample-1)]


    table = pd.DataFrame(index = axis, columns = axis)

    for j in axis:
        for k in axis:
            
            base = list(range(j, length - k + 1, k)) # 基准列表

            if (base == []) & ((j + k) > length):
                table.loc[j, k] = ''

            elif (j + k) <= length:

                return_list = []
                
                for n in base:

                    # 定义引用方法。
                    ret = hold(
                        base = timedelta(start, (n-1)), 
                        J = j, 
                        K = k, 
                        percentage = percentage, 
                        large = large, 
                        small = small
                    )

                    if strategy == 'wl':
                        return_result = ret[0] - ret[1]

                    elif strategy == 'l':
                        return_result = ret[1]

                    elif strategy == 'w':
                        return_result = ret[0]

                    return_list.append(return_result)

                avg_return = sum(return_list) / len(return_list)
                zero_list = list(itertools.repeat(0, len(return_list))) # 用来计算t检验的原假设

                ret = str(round(avg_return * 100 * 12 / k, 2))

                if len(return_list) == 1:
                    table.loc[j, k] = "%s" % ret + "%"
                else:
                    ttest = stats.ttest_ind(return_list, zero_list)[0]
                    table.loc[j, k] = "%s" % ret + "%" + "(%s)" % round(ttest, 2)
    
    return table

def strategy(
    start, 
    end, 
    J, 
    K, 
    strategy = 'l', 
    percentage = 0.2, 
    large = False, 
    small = False, 
    trade_cost = True
):

    '''
    Parameters:
    ----------
    start: 开始时间，月-'YYYY-MM'。(str)
    end: 结束时间，月-'YYYY-MM'。(str)
    J: 排序期。(int)
    K: 持有期。(int)

    Parameters:（可选） 
    ----------
    strategy: 交易策略，“赢家-输家”-'wl'、“单边输家”-'l'、“单边赢家”-'w'，默认为“单边输家”('l')。(str)
    percentage: 分层比例，默认为0.2。(float)
    large: 是否只交易市值最大的前N个股票，默认为否(False)。(int / Bool)
    small: 是否只交易市值最小的前N个股票，默认为否(False)。(int / Bool)
    trade_cost: 是否计入交易成本，默认为是(True)。(Bool)

    Return: 
    ------
    最终表格，目录为日期，Return列为收益率，Equity列为净值。
    (pd.DataFrame)
    '''

    table = pd.DataFrame()
    length = timespan(start, end)
    trade_date = list(range(0, length, K))

    for i in trade_date:

        if strategy == 'w':
            mark = 0
        elif strategy == 'l':
            mark = 1

        table = table.append(
            hold(
                base = timedelta(start, i-1), 
                J = J, 
                K = K, 
                percentage = percentage, 
                large = large, 
                small = small
            )[mark]
        )

    table['Return_calc'] = table['Return'] + 1

    if trade_cost == False:
        table.loc[start, 'Return_calc'] = 1
        table['Cumprod'] = table['Return_calc'].cumprod()
        table['Equity'] = table['Cumprod'] * 100

    elif trade_cost == True:

        equity_list = []

        for i in range(len(table)):

            if i == 0:
                equity = 100 * 0.998 * table['Return_calc'][i]
            elif i in trade_date[1:]:
                equity = equity_list[i-1] * 0.998 * 0.998 * table['Return_calc'][i]
            else:
                equity = equity_list[i-1] * table['Return_calc'][i]

            equity_list.append(equity)
        
        equity_list[-1] = equity_list[-1] * 0.998

        table['Equity'] = equity_list
        table['Equity'].iloc[-1] = table['Equity'].iloc[-1] * 0.998

    table.drop(['Mretwd', 'Stock Amount', 'Return_calc'], axis = 1, inplace = True)
    table['Return'] = table['Return'].apply(lambda x: x * 100)
        
    return table

def get_year(table, year):
    year = table[table.index.year == year]
    return year

def get_return_rate(table):
    return_rate = (table['Equity'][-1] / table['Equity'][0]) ** (12/len(table))
    return return_rate

def get_yearly_result(table):
    df = table[table.index.month == 12]
    ret_list = []
    for i in range(len(df)):
        ret_list.append(get_year(table, table.index.year[12*i])['Return'].sum())
    df['Return'] = ret_list
    return df