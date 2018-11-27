from WindPy import *
from datetime import *
import pandas as pd
from WindAlgo import * #引入回测框架
w.start(show_welcome=False)
import datetime as dt
from WindCharts import *

today = dt.datetime.now().strftime("%Y-%m-%d")
start = w.tdaysoffset(-1, today, "Period=M;Days=Alldays").Data[0][0].strftime("%Y-%m-%d")
stocks_list = w.wset(
    "sectorconstituent", # 板块成分
    "date="+today+";sectorId=a001010100000000;field=wind_code,sec_name" # 包含当前日期的参数
).Data[0]

def initialize(context): # 定义初始化函数
    context.capital = 100000000 # 回测初始资金一亿元
    context.securities = stocks_list # 回测标的，全部A股
    context.start_date = "20090101" # 回测开始时间
    context.end_date = "20181031" # 回测结束时间
    context.period = 'd' # 策略运行周期, 'd' 代表日, 'm'代表分钟
    context.benchmark = '000300.SH'  #设置回测基准为沪深300

def handle_data(bar_datetime, context, bar_data):# 定义策略函数
    pass

def my_schedule(bar_datetime, context, bar_data):
    fields = list(context.fields)
    today = bar_datetime.strftime("%Y-%m-%d") # 设置时间
    start = w.tdaysoffset(-1, today, "Period=M;Days=Alldays").Data[0][0].strftime("%Y-%m-%d")
    data = w.wss(
        stocks_list, 
        "sec_name,windcode,pct_chg_per,mkt_cap_ashare2", 
        "startDate="+today+";endDate="+today+";tradeDate="+today+"", 
        usedf = True
    )[1]
    data = data.dropna()
    data = data.sort_values('MKT_CAP_ASHARE2')
    data = data[:round(len(data)/10)]
    
    data = data.sort_values('PCT_CHG_PER')
    loser = list(data[:round(len(data)/10)].index)
    
    wa.change_securities(loser)
    context.securities = loser # 改变证券池
    
    list_sell = wa.query_position().get_field('code')
    for code in list_sell:
        volumn = wa.query_position()[code]['volume']
        # 卖出上一个月初买入的所有股票
        res = wa.order(code, volumn, 'sell', price = 'close', volume_check = False)
        
def my_schedule2(bar_datetime, context,bar_data):
    buy_code_list=list(set(context.securities)-(set(context.securities)-set(list(bar_data.get_field('code')))))  # 在单因子选股的结果中 剔除 没有行情的股票
    for code in buy_code_list:
        res = wa.order_percent(code,1/len(buy_code_list),'buy',price='close', volume_check=False)  
    #对最终选择出来的股票建仓 每个股票仓位相同   '本月建仓完毕'

wa = BackTest(init_func = initialize, handle_data_func = handle_data)
wa.schedule(my_schedule, "m", 0) # 每个月的第一个交易日执行策略
wa.schedule(my_schedule2, "m", 0) #在月初第一个交易日进行交易
res = wa.run(show_progress = True)
nav_df = wa.summary('nav')
history_pos = wa.summary('trade')