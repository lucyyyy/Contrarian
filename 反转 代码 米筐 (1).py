import pandas as pd
from math import floor
import datetime as dt
from dateutil.relativedelta import relativedelta

def contrarian(context, bar_dict):
    
    J = 3 # 排序期为3个月。
    K = 1 # 持有期为1个月。
    percentage = 0.2 # 赢家、输家依据前后20%分层。
    small = 200 # 交易200小公司，若设为False则忽略此条件。
    
    # 全部A股股票列表
    stocks = list(all_instruments('CS')['order_book_id'])
    # 排序期交易日列表
    start = (context.now + relativedelta(months = -J)).strftime('%Y%m%d')
    end = (context.now + relativedelta(days = -1)).strftime('%Y%m%d')
    date_list = get_trading_dates(start, end)
    
    # 赢家输家列表
    data = get_price_change_rate(stocks, len(date_list))
    data = data.T
    data['Aggregate Return'] = data.sum(axis = 1)
    data.sort_values(by = 'Aggregate Return', inplace = True)
    length = floor(len(data) * percentage) # 等权
    context.winner_list = list(data.index[-length:])
    context.loser_list = list(data.index[0:length])
    
    if small == False:
        pass
    elif small != False:
        # 获取小市值列表
        small_df = get_fundamentals(
            query(
                fundamentals.eod_derivative_indicator.market_cap
                ).filter(
                    fundamentals.income_statement.stockcode.in_(context.loser_list)))
        small_df = small_df.T
        small_df.sort_values(by = 'market_cap', inplace = True)
        index_list = list(small_df.index)
        small_list = index_list[:small]
        # 取二者交集。
        context.loser_list = set(context.loser_list).intersection(small_list) 
        
    # 增量调仓。
    sell_list = []
    for holding_stock in context.portfolio.positions.keys():
        if holding_stock not in context.loser_list:
            sell_list.append(holding_stock)
        
    # 卖出当前持仓。
    logger.info("Clearing all the current positions.")
    for holding_stock in sell_list:
        order_target_percent(holding_stock, 0)
            
    # 买入所有下一期持仓
    logger.info("Building new positions for portfolio.")
    for stock in context.loser_list:
        order_percent(stock, 1/len(context.loser_list))
    
    update_universe(context.loser_list) # 更新股票池
    
# 初始化逻辑
def init(context):
    # 每月第一个交易日调仓
    scheduler.run_monthly(contrarian, tradingday=1)
    # 打印交易日志
    logger.info("RunInfo: {}".format(context.run_info))
    
def before_trading(context):
    pass

def handle_bar(context, bar_dict):
    pass

def after_trading(context):
    pass