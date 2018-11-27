import pandas as pd
from math import floor
from dateutil.relativedelta import relativedelta

def contrarian(context, bar_dict):
    
    J = 3 # 排序期。
    K = 1 # 持有期。
    percentage = 0.2 # 赢家、输家依据前后20%分层。
    small = 200 # 交易200小公司，若设为False则忽略此条件。
    large = False # 交易200大公司，若设为False则忽略此条件。
    loser = True # 输家策略。
    winner = False # 赢家策略。
    
    # 交易日期列表。

    trade_list = []

    for i in range(0, 120, K):

        date = (
            context.run_info.start_date + relativedelta(months = i)
        ).strftime('%Y%m')

        context.trade_list.append(date)
    
    if context.now.strftime('%Y%m') not in trade_list:
        
        pass
    
    else:
        
        # 当日全部A股股票列表
        stocks = list(all_instruments('CS')['order_book_id'])

        # 排序期交易日列表

        start = (context.now + relativedelta(months = -J)).strftime('%Y%m%d')

        end = (context.now + relativedelta(days = -1)).strftime('%Y%m%d')

        date_list = get_trading_dates(start, end)
        
        # 赢家输家列表

        data = get_price_change_rate(stocks, len(date_list)).T

        data['Aggregate Return'] = data.sum(axis = 1)

        data.sort_values(by = 'Aggregate Return', inplace = True)

        length = floor(len(data) * percentage) # 等权

        winner_list = list(data.index[-length:])
        
        loser_list = list(data.index[0:length])
        
        # 买入输家。
        if loser == True:
            context.stock_list = loser_list
        
        # 买入赢家。
        elif winner == True:
            context.stock_list = winner_list
        
        # 只交易小市值股票。

        if small == False:
            pass
        
        elif small != False:
           
            # 获取小市值列表
            
            small_df = get_fundamentals(
                query(
                    fundamentals.eod_derivative_indicator.market_cap
                    ).filter(
                        fundamentals.income_statement.stockcode.in_(context.stock_list)))
            
            small_df = small_df.T
            
            small_df.sort_values(by = 'market_cap', inplace = True)

            small_list = list(small_df.index)[:small]

            total_mktcap = small_df['market_cap'].sum()

            # 取二者交集。
            context.stock_list = set(context.stock_list).intersection(small_list) 
        
        # 只交易大市值股票。

        if large == False:
            pass
        
        elif large != False:

            # 获取大市值列表

            large_df = get_fundamentals(
                query(
                    fundamentals.eod_derivative_indicator.market_cap
                    ).filter(
                        fundamentals.income_statement.stockcode.in_(context.stock_list)))
            
            large_df = large_df.T
            
            large_df.sort_values(by = 'market_cap', inplace = True)
            
            index_list = list(large_df.index)
            
            large_list = index_list[-large:]
            
            # 取二者交集。
            context.stock_list = set(context.stock_list).intersection(large_list) 
            
        # 增量调仓。

        sell_list = []

        for holding_stock in context.portfolio.positions.keys():

            if holding_stock not in context.stock_list:

                sell_list.append(holding_stock)
            
        # 卖出当前持仓。

        logger.info("Clearing all the current positions.")

        for holding_stock in sell_list:

            order_target_percent(holding_stock, 0)
                
        # 买入所有下一期持仓

        logger.info("Building new positions for portfolio.")

        for stock in context.stock_list:

            # order_target_percent(stock, 1/len(context.stock_list))

            order_target_percent(
                stock, 
                small_df.loc[stock, 'market_cap'] / total_mktcap
            )

            logger.info("Bought: " + str(1/len(context.stock_list)*100) + " % for stock: " + str(stock))
        
        update_universe(context.stock_list) # 更新股票池
    
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

# Remaining questions:
# sometimes data will have np.nan. 
# use np.isnan(var) to check it out. 
# sometimes context.stock_list != data.index
# use set(l1).intersection(l2) to subset. 