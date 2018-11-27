# Contratian and Momentum strategy.
###### 作者：林新凯
# > 数据来源为CSMAR。 

# 0 准备工作

# 载入所需模块。
import pandas as pd 
from scipy import stats
import itertools
import datetime as dt 
from dateutil.relativedelta import relativedelta
from math import floor
import numpy as np
import ffn
import matplotlib

# 1 处理数据。

# 用日、周、月、年频数据研究反转与惯性。
# 数据范围为**1995-01-01至2017-12-31**。

## 1.0 获取基础数据

# 从本地磁盘读取数据。
class Data(object):

    '''
    param: 
        filepath: 子目录
    '''

    # 母目录
    path = r'C:\\Users\\KasperLin\\OneDrive - whu.edu.cn\\work\\study\\quant\\Contrarian\\data'

    def __init__(self, filepath):
        self.filepath = filepath

    def get_data(self):

        '''
        return: 子目录下的文件
        '''

        self.data = pd.read_csv(self.path + self.filepath)
        return self.data 

# 获取数据
# day = Data(r'\\day\\day.csv').get_data() # 日频
# week = Data(r'\\week\\week.csv').get_data() # 周频
month = Data(r'\\month\\month.csv').get_data() # 月频
year = Data(r'\\year\\year.csv').get_data() # 年频

# list_data = Data(r'\\list\\list.csv').get_data() # 上市数据

## 1.1 清洗数据

# 由于年度数据时间的数据类型为整数而不是字符串，统一为字符串。
year = year.astype({'Trdynt':'str'})
# 由于月度数据的格式无法直接进行计算，统一为datetime格式。
month['Trdmnt'] = pd.to_datetime(month['Trdmnt'], format = '%b-%y')

'''
# 由于周频数据时间的数据有BUG，错误地将前12周显示为前12月
# 即所有形如“Jan-96”的日期都应改为"1996-1"
for i in range(len(week)):
    date_str = week['Trdwnt'][i]
    if len(date_str) == 6 and date_str[3] == '-':
        date = dt.datetime.strptime(date_str, '%b-%y')
        date_modified = dt.datetime.strftime(date, '%Y-%m')
        week.iloc[i, 1] = date_modified
    elif len(date_str) == 6 and date_str[2] == '-':
        date = dt.datetime.strptime(date_str, '%y-%b')
        date_modified = dt.datetime.strftime(date, '%Y-%m')
        week.iloc[i, 1] = date_modified
    elif len(date_str) == 5:
        date_str = date_str.zfill(6)
        date = dt.datetime.strptime(date_str, '%y-%b')
        date_modified = dt.datetime.strftime(date, '%Y-%m')
        week.iloc[i, 1] = date_modified
'''


## 1.2 输出数据

class Rank(object):

    '''
    param:
        t: 频率，年-'y'，月-'m'，周-'w'，日-'d'。(str)
    '''

    def __init__(self, t = 'm'):
        if t == 'y':
            self.t = 'y'
            self.data = year
            self.time_label = 'Trdynt'
            self.return_label = 'Yretnd'
            self.value_label = 'Ysmvttl'
        elif t == 'm':
            self.t = 'm'
            self.data = month
            self.time_label = 'Trdmnt'
            self.return_label = 'Mretwd'
            self.value_label = 'Msmvttl'

    def timedelta(self, n, delta):

        '''
        param:
            n: 日期，年-'YYYY'，月-'YYYY-MM'。(str)
            delta: 日期变动值，为正则向前变动，为负反之。(int)
        return:
            变动后的日期值。(str)
        '''

        # 先把字符串格式的日期转换为可计算的日期，计算后再转换回字符串。
        
        if self.t == 'y':
            tn = (dt.datetime.strptime(n, '%Y') + \
            relativedelta(years = delta)).strftime('%Y')

        elif self.t == 'm':
            tn = (dt.datetime.strptime(n, '%Y-%m') + \
            relativedelta(months = delta)).strftime('%Y-%m')

        return tn

    def rank(self, n, J):

        '''
        param:
            n: 日期，年-'YYYY'，月-'YYYY-MM'。(str)
            J: 排序期。(int)
        return:
            按照排序期股票累计收益率降序排序的股票代码及其收益率列表。(pd.Series)
        '''

        start = Rank(self.t).timedelta(n, -J)
        end = Rank(self.t).timedelta(n, 1)
        
        # 取出排名期内的数据。
        rank = self.data[(self.data[self.time_label] > start) & (self.data[self.time_label] < end)]

        # 计算每只股票在排名期的累计收益率。
        aggret = rank.groupby('Stkcd')[self.return_label].agg('sum')

        # 将累计收益率排序。
        aggret.sort_values(inplace = True)

        return aggret

    def get_port(self, n, J, percentage = 0.2):

        '''
        param:
            n: 日期，年-'YYYY'，月-'YYYY-MM'。(str)
            J: 排序期。(int)
        param（可选）:
            percentage: 分层比例。(float)
        return:
            赢家股票列表。(pe.Series)
            输家股票列表。(pe.Series)
        '''

        # 获取排序期股票数据。
        rank = Rank(self.t).rank(n, J)

        length = floor(len(rank) * percentage)

        # 取收益率最高的一层为赢家。
        winner_list = rank.index[-length:]
        # 取收益率最低的一层为输家。
        loser_list = rank.index[0:length]

        return winner_list, loser_list
    
    def hold(self, n, J, K, percentage = 0.2, large = False, small = False, value_weighted = False):

        '''
        param:
            n: 日期，年-'YYYY'，月-'YYYY-MM'。(str)
            J: 排序期。(int)
            K: 持有期。(int)
        param（可选）:
            percentage: 分层比例，默认为0.2。(float)
            large: 是否只交易市值最大的前N个股票，默认为否(False)。(int / Bool)
            small: 是否只交易市值最小的前N个股票，默认为否(False)。(int / Bool)
            value_weighted: 是否市值加权构建投资组合，默认为否(False)。(Bool)
        return:
            赢家收益率。(float)
            输家收益率。(float)
        '''

        start = Rank(self.t).timedelta(n, 0)
        end = Rank(self.t).timedelta(n, K+1)
        observe = self.data[self.data[self.time_label] == n]

        if (large == False) | (small == False):
            port = Rank(self.t).get_port(n, J, percentage = percentage)
            winner_list = list(port[0])
            loser_list = list(port[1])

        if large != False:
            port = Rank(self.t).get_port(n, J, percentage = percentage)
            large = list(observe.sort_values(by = self.value_label).tail(large)['Stkcd'])
            winner_list = set(large).intersection(list(port[0]))
            loser_list = set(large).intersection(list(port[1]))

        if small != False:
            port = Rank(self.t).get_port(n, J, percentage = percentage)
            small = list(observe.sort_values(by = self.value_label).head(small)['Stkcd'])
            winner_list = set(small).intersection(list(port[0]))
            loser_list = set(small).intersection(list(port[1]))
        
        # 取出持有期内的数据。
        hold = self.data[(self.data[self.time_label] > start) & (self.data[self.time_label] < end)]
        hold_winner = hold[hold['Stkcd'].isin(winner_list)]
        hold_loser = hold[hold['Stkcd'].isin(loser_list)]

        # 计算每只股票在持有期的累计收益率。
        aggret_winner = hold_winner.groupby('Stkcd')[self.return_label].sum()
        aggret_loser = hold_loser.groupby('Stkcd')[self.return_label].sum()

        if value_weighted == True:
            # 市值加权构建投资组合计算收益率
            winner = pd.DataFrame(aggret_winner)
            observe_winner = observe[observe['Stkcd'].isin(list(aggret_winner.index))]
            winner['Value'] = list(observe_winner[self.value_label])
            winner_ret = np.average(winner[self.return_label], weights = winner['Value'])

            loser = pd.DataFrame(aggret_loser)
            observe_loser = observe[observe['Stkcd'].isin(list(aggret_loser.index))]
            loser['Value'] = list(observe_loser[self.value_label])
            loser_ret = np.average(loser[self.return_label], weights = loser['Value'])

        if value_weighted == False:
            winner_ret = sum(aggret_winner) / len(aggret_winner)
            loser_ret = sum(aggret_loser) / len(aggret_loser)

        return winner_ret, loser_ret

    def perf(self, start, n_month, J, K, strategy = 'wl', percentage = 0.2, large = False, small = False, value_weighted = False):

        table = pd.DataFrame(columns = ['Return', 'Equity'])

        time_list = []
        return_list = []
        
        for i in range(n_month - K):

            time_list.append(Rank(self.t).timedelta(start, i))

            w = Rank(self.t).hold(
                n = Rank(self.t).timedelta(start, i), 
                J = J, 
                K = K, 
                percentage = percentage, 
                large = large, 
                small = small, 
                value_weighted = value_weighted
            )[0]

            l = Rank(self.t).hold(
                n = Rank(self.t).timedelta(start, i), 
                J = J, 
                K = K, 
                percentage = percentage, 
                large = large, 
                small = small, 
                value_weighted = value_weighted
            )[1]

            if strategy == 'wl':
                ret = (w - l)*100
            elif strategy == 'w':
                ret = w*100
            elif strategy == 'l':
                ret = l*100

            return_list.append(ret)

        table['Time'] = time_list
        table['Time'] = pd.to_datetime(table['Time'], format = '%Y-%m')
        table.set_index('Time', inplace = True)
        table['Return'] = return_list
        table.iloc[0, 0] = 0
        table['Equity'] = table['Return'].cumsum() + 100
        table.iloc[0, 1] = 100

        perf = table['Equity'].calc_stats()

        return perf

### 1.1.1 年频

# 2 实证检验

# > 使用Jegadeesh和Titman(1993)的方法（重叠法）进行收益率检验。

class Test(Rank):

    '''
    param:
        start: 开始时间，年-'YYYY'、月-'YYYY-MM'。(str)
        end: 结束时间，年-'YYYY'、月-'YYYY-MM'。(str)
        t: 频率，年-'y'，月-'m'，周-'w'，日-'d'。(str)
        freq: 排序持有期观察频率。(int)
        n_sample: 排序持有期观察次数。(int)
    '''

    def __init__(self, start, end, freq, t = 'm', n_sample = None):

        if t == 'y':
            self.t = 'y'
            start_date = int(start)
            end_date = int(end)
            self.length = end_date - start_date + 1

        if t == 'm':
            self.t = 'm'
            start_date = dt.datetime.strptime(start, '%Y-%m')
            end_date = dt.datetime.strptime(end, '%Y-%m')
            self.length = relativedelta(end_date, start_date).years * 12 + \
            relativedelta(end_date, start_date).months + 1

        self.start = start
        self.end = end
        self.freq = freq

        if freq == 1:
            self.axis = list(range(1, self.length + 1))[:n_sample]
        else:
            self.axis = [1] + list(range(self.freq, self.freq * (self.length // self.freq) + 1, self.freq))[:(n_sample-1)]

    def table(
        self, 
        strategy = 'wl', 
        percentage = 0.2, 
        large = False, 
        small = False, 
        value_weighted = False):

        '''
        param（可选）:
            strategy: 交易策略，“赢家-输家”-'wl'、“单边输家”-'l'、“单边赢家”-'w'，默认为“赢家-输家”('wl')。(str)
            large: 是否只交易市值最大的前N个股票，默认为否(False)。(int / Bool)
            small: 是否只交易市值最小的前N个股票，默认为否(False)。(int / Bool)
            value_weighted: 是否市值加权构建投资组合，默认为否(False)。(Bool)
        return:
            最终表格。(pd.DataFrame)
        '''
        
        table = pd.DataFrame(index = self.axis, columns = self.axis)

        for j in self.axis:
            for k in self.axis:
                
                base = list(range(j, self.length - k + 1, k)) # 基准列表

                if (base == []) & ((j + k) > self.length):
                    table.loc[j, k] = ''

                elif (j + k) <= self.length:

                    return_list = []
                    
                    for n in base:

                        # 定义引用方法。
                        ret = Rank(self.t).hold(
                            n = Rank(self.t).timedelta(self.start, +(n-1)), 
                            J = j, 
                            K = k, 
                            percentage = percentage, 
                            large = large, 
                            small = small, 
                            value_weighted = value_weighted)

                        if strategy == 'wl':
                            return_result = ret[0] - ret[1]

                        elif strategy == 'l':
                            return_result = ret[1]

                        elif strategy == 'w':
                            return_result = ret[0]

                        return_list.append(return_result)

                    avg_return = sum(return_list) / len(return_list)
                    zero_list = list(itertools.repeat(0, len(return_list)))

                    if self.t == 'y':
                        ret = str(round(avg_return * 100 / k, 2))
                    if self.t == 'm':
                        ret = str(round(avg_return * 100 * 12 / k, 2))

                    if len(return_list) == 1:
                        table.loc[j, k] = "%s" % ret + "%"
                    else:
                        ttest = stats.ttest_ind(return_list, zero_list)[0]
                        table.loc[j, k] = "%s" % ret + "%" + "(%s)" % round(ttest, 2)
        
        return table

# ## 2.1 年频
# ## 2.2 月频
'''
month_sample = Test(
    start = '2008-01', 
    end = '2017-12', 
    t = 'm', 
    freq = 3, 
    n_sample = 5
    ).table(
        strategy = 'l', 
        large = False, 
        small = 200, 
        value_weighted = False
    )
'''
# ## 2.3 周频
# ## 2.4 日频

# 3 优化模型

# ## 3.1 数据优化

# ### 3.1.1 尝试剔除上市新股数据
# ### 3.1.2 尝试剔除ST、PT
# ### 3.1.3 尝试区分时间段研究
# ### 3.1.4 尝试不同分层
# ### 3.1.5 尝试不同间隔期
# ### 3.1.6 尝试不同周度计算方法

# ## 3.2 引入其它因子

# ### 3.2.1 引入市值
# ### 3.2.2 引入交易量

# ## 3.3 其它优化

# ### 3.3.1 单边交易-只做输家

# 4 搭建策略