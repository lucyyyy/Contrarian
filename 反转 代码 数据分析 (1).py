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

# 1 处理数据。

# 用日、周、月、年频数据研究反转与惯性。
# 数据范围为**1995-01-01至2017-12-31**。

## 1.0 获取基础数据

# 从本地磁盘读取数据。
class Data(object):

    def __init__(self, filepath):
        self.filepath = filepath
        self.path = r'C:\\Users\\KasperLin\\OneDrive - whu.edu.cn\\work\\study\\quant\\Contrarian\\data'

    def get_data(self):
        self.data = pd.read_csv(self.path + self.filepath)
        return self.data 

# day = Data(r'\\day\\day.csv').get_data() # 日频
# week = Data(r'\\week\\week.csv').get_data() # 周频
month = Data(r'\\month\\month.csv').get_data() # 月频
year = Data(r'\\year\\year.csv').get_data() # 年频

# list_data = Data(r'\\list\\list.csv').get_data() # 上市数据

## 1.1 清洗数据

# 由于年度数据时间的数据类型为整数而不是字符串，统一为字符串。
year = year.astype({'Trdynt':'str'})

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

import os 
# 尝试从本地读取数据。
path = r'C:\\Users\\KasperLin\\OneDrive - whu.edu.cn\\work\\study\\quant\\Contrarian\\data\\week\\week.csv'
# 由于库本身的bug，必须先用os模块切换到文件所在目录。
pwd = os.getcwd()
os.chdir(os.path.dirname(path))
# 保存数据。
week = pd.read_csv(os.path.basename(path))
# 再切换回去原来的工作目录。
os.chdir(pwd)
'''


## 1.2 输出数据

# * J、K分别代表排序期、持有期。
# 获取最终结果的函数格式为：
# 频率：年、月、周、日分别用'y'、'm'、'w'、'd'代替（都是字符串）
# 赢家组合：“Return(频率).hold_winner_return(基准期，排序期, 持有期)”
# 输家组合：输家组合：“Return(频率).hold_loser_return(基准期，排序期, 持有期)”
# * 年回报率采用CSMAR数据库中的“考虑现金红利再投资的年个股回报率”。
class Return(object):

    def __init__(self, t):
        if t == 'y':
            self.t = 'y'
            self.data = year
            self.time_label = 'Trdynt'
            self.return_label = 'Yretwd'
            self.return_column = 7
            self.open_label = 'Yopnprc'
            self.close_label = 'Yclsprc'
            self.name = 'year'
        elif t == 'm':
            self.t = 'm'
            self.data = month
            self.time_label = 'Trdmnt'
            self.return_label = 'Mretwd'
            self.return_column = 7
            self.open_label = 'Mopnprc'
            self.close_label = 'Mclsprc'
            self.name = 'month'
        elif t == 'w':
            self.t = 'w'
            self.data = week
            self.time_label = 'Trdwnt'
            self.return_label = 'Wretwd'
            self.return_column = 7
            self.open_label = 'Wopnprc'
            self.close_label = 'Wclsprc'
            self.name = 'week'
        elif t == 'd':
            self.t = 'd'
            self.data = day
            self.time_label = 'Trddnt'
            self.return_label = 'Dretwd'
            self.return_column = 7
            self.open_label = 'Dopnprc'
            self.close_label = 'Dclsprc'
            self.name = 'day'

    def get_list(self):
        time_list = self.data[self.time_label].drop_duplicates()
        return time_list

    # 定义函数get_data(基准期)获取第N期（包含第N期）的按照收益率从大到小排序的数据。
    # 剔除样本缺失的数据。
    def get_data(self, n):
        data = self.data[self.data[self.time_label] == n].dropna()\
        .sort_values(by = self.return_label, ascending = False)
        return data

    def timedelta(self, n, delta):
        if self.t == 'y':
            tn = (dt.datetime.strptime(n, '%Y') + \
            relativedelta(years = delta)).strftime('%Y')
        elif self.t == 'm':
            tn = (dt.datetime.strptime(n, '%b-%y') + \
            relativedelta(months = delta)).strftime('%b-%y')
        return tn

    # 定义函数sort(基准期，排序期)获取第N期按照前J期排序得到的收益率数据。
    def sort(self, n, J):

        data = Return(self.t).get_data(n)
        return_list = [] # 空列表保存平均收益率数据

        # 取过去J期的股票数据的交集。
        past_data = Return(self.t).get_data(Return(self.t).timedelta(n, -J))
        data = data[data['Stkcd'].isin(past_data['Stkcd'])]

        # 遍历data的i个股票数据到过去J期的数据中取得过去的收益率。
        for i in range(len(data)):

            code = data.iloc[i, 0] # 基准期的第i个股票代码

            base_price = Return(self.t).get_data(n)[self.close_label].iloc[i]
            past_data = Return(self.t).get_data(Return(self.t).timedelta(n, -J)) # 第J期的数据
            past_price = past_data[past_data['Stkcd'] == code][self.open_label].iloc[0] # 第i个股票第J期的历史收益率
            cum_return = (base_price - past_price) / past_price

            return_list.append(cum_return) # 在列表加上平均收益率
        
        data.loc[:, 'past_ret'] = return_list
        data = data.sort_values(by = "past_ret", ascending = False)

        return data

    # 定义函数get_winner(基准期，排序期)获取排序期赢家组合的数据。
    def get_winner(self, n, J):
        data = Return(self.t).sort(n, J)
        return data.head(int(len(data) / 5))

    # 定义函数winner_return(基准期，排序期)获取排序期赢家组合的收益率。
    def winner_return(self, n, J):
        return Return(self.t).get_winner(n, J)[self.return_label].mean()

    # 定义函数get_loser(基准期，排序期)获取排序期输家组合的数据。
    def get_loser(self, n, J):
        data = Return(self.t).sort(n, J)
        return data.tail(int(len(data) / 5))

    # 定义函数loser_return(基准期，排序期)获取排序期输家组合的收益率。
    def loser_return(self, n, J):
        return Return(self.t).get_loser(n, J)[self.return_label].mean()

    # 定义函数hold(基准期，排序期，持有期，)
    def hold(self, n, J, K, port):

        return_list = [] # 空列表保存平均收益率数据

        # 清洗数据
        future_data = Return(self.t).get_data(Return(self.t).timedelta(n, +K))
        port = port[port['Stkcd'].isin(future_data['Stkcd'])] 

        for i in range(len(port)):

            code = port.iloc[i, 0]
            base_price = Return(self.t).get_data(Return(self.t).timedelta(n, +1))[self.open_label].iloc[i]
            future_data = Return(self.t).get_data(Return(self.t).timedelta(n, +K))
            future_price = future_data[future_data['Stkcd'] == code]\
            [self.close_label].iloc[0]
            cum_return = (future_price - base_price) / base_price

            return_list.append(cum_return / K)

        port.loc[:, 'hold_ret'] = return_list
        port = port.sort_values(by = 'hold_ret', ascending = False)

        return port

    def hold_winner(self, n, J, K):
        data = Return(self.t).hold(n, J, K, Return(self.t).get_winner(n, J))
        return data

    def hold_loser(self, n, J, K):
        return Return(self.t).hold(n, J, K, Return(self.t).get_loser(n, J))

    def hold_winner_return(self, n, J, K):
        return Return(self.t).hold_winner(n, J, K)['hold_ret'].mean()

    def hold_loser_return(self, n, J, K):
        return Return(self.t).hold_loser(n, J, K)['hold_ret'].mean()    

### 1.1.1 年频

# 2 实证检验

# > 使用Jegadeesh和Titman(1993)的方法（重叠法）进行收益率检验。

# 列表总结结果并检验。
# 获得最终检验统计表格的函数格式为：
# “Test(频率, 开始期, 结束期, 排序期持有期样本选择跨度)”
class Test(object):

    def __init__(self, t, start, end, freq, n_sample = None):

        if t == 'y':
            self.t = 'y'
            start_date = dt.datetime.strptime(start, '%Y')
            end_date = dt.datetime.strptime(end, '%Y')
            self.length = relativedelta(end_date, start_date).years + 1

        if t == 'm':
            self.t = 'm'
            start_date = dt.datetime.strptime(start, '%b-%y')
            end_date = dt.datetime.strptime(end, '%b-%y')
            self.length = relativedelta(end_date, start_date).years * 12 + \
            relativedelta(end_date, start_date).months + 1

        if t == 'w':
            self.t = 'w'
            start_date = dt.datetime.strptime(start, '%Y-%W')
            end_date = dt.datetime.strptime(end, '%Y-%W')
            self.length = (relativedelta(end_date, start_date).years * 365 + \
            relativedelta(end_date, start_date).months * 30 + \
            relativedelta(end_date, start_date).days) / 7


        self.start = start
        self.end = end
        self.freq = freq

        if freq == 1:
            self.axis = list(range(1, self.length + 1))[:n_sample]
        else:
            self.axis = [1] + list(range(self.freq, self.freq * int(self.length / self.freq) + 1, self.freq))[:n_sample]

    def table(self, strategy):

        table = pd.DataFrame(index = self.axis, columns = self.axis)

        for j in self.axis:
            for k in self.axis:
                # 赢家 - 输家组合
                base = list(range(j, self.length - k + 1)) # 基准年列表

                if base == []:
                    table.loc[j, k] = ''

                elif (j + k) > self.length:
                    table.loc[j, k] = ''

                elif (j + k) <= self.length:
                    return_list = []
                    for n in base:
                        if strategy == 'wl':
                            return_result = \
                            Return(self.t).hold_winner_return(Return(self.t).timedelta(self.start, +(n-1)), j, k) - \
                            Return(self.t).hold_loser_return(Return(self.t).timedelta(self.start, +(n-1)), j, k)
                        if strategy == 'l':
                            return_result = Return(self.t).hold_loser_return(Return(self.t).timedelta(self.start, +(n-1)), j, k)
                        return_list.append(return_result)
                    sum_return = 0
                    for i in return_list:
                        sum_return += i
                    avg_return = sum_return / len(base)
                    zero_list = list(itertools.repeat(0, len(return_list)))
                
                    if len(return_list) == 1:
                        table.loc[j, k] = str(round(avg_return, 4))
                    else:
                        ttest = stats.ttest_ind(return_list, zero_list)[0]
                        if type(ttest) == str:
                            table.loc[j, k] = str(round(avg_return, 4))
                        else:
                            table.loc[j, k] = str(round(avg_return, 4)) + "(%s)" % round(ttest, 4)
        
        return table

# ## 2.1 年频
# ## 2.2 月频
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