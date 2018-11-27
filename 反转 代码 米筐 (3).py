# import modules. 
from dateutil.relativedelta import relativedelta
from math import floor

# Contrarian strategy. 
def contrarian(
    context, 
    bar_dict
):
    
    # --------------------------------------------------
    # Parameters:
    rank = 3
    hold = 1
    percentage = 0.2
    small = 200
    large = False
    loser = False
    winner = False
    winner_loser = False
    roe = loser
    total_market_capital = False
    outstanding_market_capital = False
    equally_weighted = True
    small_mktcap_weighted = False
    large_mktcap_weighted = False
    ST = False

    # Parameters description:  
    # rank: how many months to rank. 
    # hold: how many months to hold. 
    # percentage: 
        # Define specific group as the first/last \
        # [percentage] of best/worst ranking stocks \
        # in the entire A-share. 
    # small: 
        # only trade [small] amount of small \
        # (market capital) stocks.
        # If set as False then ignore this limitation.  
    # only trade [large] amount of large \
    # (market capital) stocks.
    # If set as False then ignore this limitation.
    large = False

    # Bool, define whether execute loser strategy.  
    loser = True 

    # Bool, define whether execute winner strategy.
    winner = False

    # Bool, define whether execute winner-loser\
    # strategy or not. 
    winner_loser = False

    # ROE. 
    roe = True

    # Determine which market capital to use.
    total_market_capital = False # total market capital
    outstanding_market_capital = True # outstanding market capital

    # Whether weighted or not, and how. 

    # equally weighted. 
    equally_weighted = False
    # The smaller mktcap the lighter it's weighted
    small_mktcap_weighted = True
    # The larger mktcap the lighter it's weighted
    large_mktcap_weighted = False

    # Trade ST or not. 
    ST = False


    # ----------------------------------------------------------------


    # get trading date list. 
    trade_date = [] # an empty list for containing

    # 120 is actually a randomly picked number, \
    # just for generating a long enough list for
    # filtering, 120 in here simply means 10 years\
    # (120 months).
    for i in range(0, 120, hold): 

        # Pick the months that I wanna trade in. 
        date = (
            context.run_info.start_date + \
            relativedelta(months = i)
        ).strftime('%Y%m')

        # Put them altogether. 
        trade_date.append(date)

    context.trade_date = trade_date
    
    # If now is not in my specified list, \
    # simply don't do anything. 
    if context.now.strftime('%Y%m') not in trade_date:
        pass
    
    # Otherwise, execute my trading strategy. 
    else:
        
        # Entire A-share list. 
        all_stocks = list(
            all_instruments('CS')[
                'order_book_id'
            ]
        )

        # Rank period trading date list. 
        
        # Start ranking since [rank] months ago. 
        rank_start = (
            context.now + \
            relativedelta(months = -rank)
        ).strftime('%Y%m%d')

        # End ranking on yesterday. 
        rank_end = (
            context.now + \
            relativedelta(days = -1)
        ).strftime('%Y"m%d')

        # Form the ranking trading interval date list. 
        rank_trade_date = get_trading_dates(
            rank_start, 
            rank_end
        )

        # List of winner & loser. 

        # Add up 
        data['Aggregate Return'] = data.sum(axis = 1)

        # Sort by aggregate return, rank from \
        # minimum to maximum. 
        data.sort_values(
            by = 'Aggregate Return', 
            inplace = True
        )

        # Define how many stocks are there in a group. 
        portfolio_length = floor(
            len(data) * \
            percentage
        )

        # Define the winner & loser group. 
        winner_stocks = list(
            data.index[
                -portfolio_length:
            ]
        )
        loser_stocks = list(
            data.index[
                :portfolio_length
            ]
        )

        # Loser strategy. 
        if loser:
            context.stock_list = loser_stocks
        
        # Winner strategy. 
        elif winner:
            context.stock_list = winner_stocks
        
        # ROE strategy. 

        # Get profit data to form winner/loser group. 
        data = get_price_change_rate(
            all_stocks, # entire A-share
            len(rank_trade_date) # rank period
        ).T 
        # Transpose to make the index is stock list, \
        # while the column is date list. 

        if roe == True:

            # Get roe data to form roe group. 
            data = get_fundamentals(
                query(
                    fundamentals.current_performance.roe
                ).filter(
                    fundamentals.income_statement.stockcode.in_(
                        all_stocks
                    )
                )
            ).T

            data.sort_values(
                by = 'roe', 
                inplace = True
            )

            portfolio_length = floor(
                len(data) * \
                percentage
            )

            context.stock_list = list(
                data.index[
                    :portfolio_length
                ]
            )

        # Market capital data for small & large strategy.
        if total_market_capital:
            market_capital_code =  fundamentals.eod_derivative_indicator.market_cap
            market_capital_name = 'market_cap'
        elif outstanding_market_capital:
            market_capital_code = fundamentals.eod_derivative_indicator.a_share_market_val_2
            market_capital_name = 'a_share_market_val_2'

        # Get market capital data. 
        market_capital_data = get_fundamentals(
            query(
                market_capital_code
            ).filter(
                fundamentals.income_statement.stockcode.in_(
                    context.stock_list
                )
            )
        ).T
        # Transpose it to make index be stock list, \
        # while column be variable list. 

        market_capital_data['Rank'] = market_capital_data[
            market_capital_name
        ].rank()

        if small_mktcap_weighted:

            market_capital_data[
                'Rank'
            ] = market_capital_data[
                market_capital_name
            ].rank(ascending = False)

            total_weight = market_capital_data[
                market_capital_name
            ].sum()
        
        elif large_mktcap_weighted:

            market_capital_data[
                'Rank'
            ] = market_capital_data[
                market_capital_name
            ].rank()

            total_weight = market_capital_data[
                market_capital_name
            ].sum()
        
        # Small strategy. 
        if small:
            
            # Sort by market capital, \
            # from smallest to largest. 
            market_capital_data.sort_values(
                by = market_capital_name, 
                inplace = True
            )

            # Generate small stocks list. 
            small_stocks = list(
                market_capital_data.index
            )[
                :small
            ]

            # Pick the intersection of small & winner/loser\ 
            # as the final trading list. 
            context.stock_list = set(
                context.stock_list
            ).intersection(
                small_stocks
            )
        
        if large:
            
            # Sort by market capital, \
            # from largest to smallest. 
            market_capital_data.sort_values(
                by = market_capital_name, 
                inplace = True, 
                ascending = False
            )

            # Generate large stocks list. 
            large_stocks = list(
                market_capital_data.index
            )[
                :large
            ]

            # Pick the intersection of large & winner/loser\ 
            # as the final trading list. 
            context.stock_list = set(
                context.stock_list
            ).intersection(
                large_stocks
            )
        
        if ST == False:
            context.stock_list = [
                x for x in context.stock_list if is_st_stock(x) == False
            ]
        
        elif ST == 'only':
            context.stock_list = [
                x for x in context.stock_list if is_st_stock(x) == True
            ]

        # Increment position adjustment. 
        
        # Sell out the stocks that's \
        # not included in the next positions. 

        # Form the sell list. 
        sell_stocks = []
        for holding_stock in \
        context.portfolio.positions.keys():
            if holding_stock not in context.stock_list:
                sell_stocks.append(holding_stock)
        
        for holding_stock in sell_list:
            order_target_percent(
                holding_stock, 
                0 # sell them
            )
        
        # Report at the end of a month. 
        logger.info(
            "End, clear short positions in the last month."
        )
        
        # Buy the next positions. 
        for stock in context.stock_list:

            # Equally weighted. 
            if equally_weighted:
                order_target_percent(
                    stock, 
                    1 / len(context.stock_list)
                )
            
            # Small market capital weighted. 
            elif small_mktcap_weighted:
                order_target_percent(
                    stock, 
                    market_capital_data.loc[
                        stock, 
                        'Rank'
                    ] / total_weight
                )
            
            # Large market capital weighted. 
            elif large_mktcap_weighted:
                order_target_percent(
                    stock, 
                    market_capital_data.loc[
                        stock, 
                        'Rank'
                    ] / total_weight
                )
            
            # Report trading info. 
            logger.info(
                "Bought: " + \
                str(stock)
            )

        # Report at the start of a month. 
        logger.info(
            "Start, build long positions for the next month."
        )

        # Update portfolio. 
        update_universe(
            context.stock_list
        )

# Initialize logic. 

def init(context):

    # Adjust position on the first trading day of each month. 
    scheduler.run_monthly(
        contrarian, 
        tradingday = 1 # the first trading day
    )

    # Report trading. 
    logger.info(
        "Trading information: {}".format(
            context.run_info
        )
    )

def before_trading(context):
    pass

def handle_bar(context, bar_dict):
    pass

def after_trading(context):
    pass