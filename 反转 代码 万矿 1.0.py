from WindPy import * # 引入万德框架
from WindAlgo import * # 引入回测框架
import datetime as dt # 引入日期框架
import pandas as pd
w.start(show_welcome = False)

def today(long = True, short = False):
    today = dt.datetime.now()
    if long:
        today = today.strftime("%Y-%m-%d")
    if short:
        today = today.strftime("%Y%m%d")
    return today

def argument(stocks_list = True, data = False):
    if stocks_list:
        arg = "date=%s;sectorId=a001010100000000;field=wind_code,sec_name" % today(long = True)
    if data:
        arg = "tradeDate=%s;priceAdj=U;cycle=D" % today(short=True)
    return arg

stocks_list = w.wset(
    "sectorconstituent", # 板块成分
    argument(stocks_list = True) # 包含当前日期的参数
).Data[1]

def initialize(context): # 定义初始化函数
    context.capital = 100000000 # 回测初始资金一亿元
    context.securities = stocks_list # 回测标的，全部A股
    context.start_date = "20090101" # 回测开始时间
    context.end_date = "20171231" # 回测结束时间
    context.period = 'd' # 策略运行周期, 'd' 代表日, 'm'代表分钟
    context.benchmark = '000300.SH'  #设置回测基准为沪深300

def handle_data(bar_datetime, context, bar_data):# 定义策略函数
    pass

def my_schedule(bar_datetime, context, bar_data):
    bar_datetime_str = bar_datetime.strftime("&Y-%m-%d") # 设置时间
    data = w.wss(
        stocks_list, 
        "sec_name,close,open,high,low,chg,pct_chg,volume,amt,dealnum,turn,chg_settlement,pct_chg_settlement,susp_reason,ev,mkt_cap_ard", 
    )
    

bkt = BackTest(init_func = initialize, handle_data_func=handle_data) # 实例化回测对象
bkt.schedule(my_schedule, "m", 0) # m表示在每个月执行一次策略 0表示偏移  表示月初第一个交易日往后0天
res = bkt.run() # 开始运行策略