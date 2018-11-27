# import modules. 
from dateutil.relativedelta import relativedelta
from math import floor

# Contrarian strategy. 
def contrarian(
    context, 
    bar_dict
):

    # Parameters:
    # Basics:
    rank = 3
    hold = 1
    percentage = 0.2
    # Mktcap: 
    small = 200
    large = False
    total_mktcap = False
    outstanding_mktcap = False
    A_share_mktcap = True
    # Strategy:
    loser = False
    winner = False
    winner_loser = False
    # Weighted:
    equally = False
    small_mktcap = False
    large_mktcap = False
    volatility = True
    # Others: 
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
        # large: 
            # only trade [large] amount of large \
            # (market capital) stocks.
            # If set as False then ignore this limitation.
        # total_mktcap: use total mktcap to determine mktcap. 
        # outstanding_mktcap: use outstanding_mktcap to determine mktcap. 
        # A_share_mktcap: use A-share mktcap to determine mktcap. 
        # loser: Bool, loser strategy. 
        # winner: Bool, winner strategy.
        # winner_loser: Bool, winner-loser strategy. 
        # roe: Bool, roe strategy. 
        # equally weighted. 
        # small_mktcap: 
            # The smaller mktcap the lighter it's weighted. 
        # larger_mktcap: 
            # The largerer mktcap the lighter it's weighted. 
        # ST: Trade ST or not. If set to 'only' then trade ST only. 

    # get trading date list. 
    trade_date = [] # an empty list for containing

    # 120 is actually a randomly picked number, \
    # just for generating a long enough list for \
    # filtering, 120 in here simply means 10 years. 
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
        
        # Start ranking since [rank] months ago. 
        rank_start = (
            context.now + \
            relativedelta(months = -rank)
        ).strftime('%Y%m%d')

        # End ranking on yesterday. 
        rank_end = (
            context.now + \
            relativedelta(days = -1)
        ).strftime('%Y%m%d')

        # Form the ranking trading interval date list. 
        rank_trade_date = get_trading_dates(
            rank_start, 
            rank_end
        )

        # winner & loser strategy.
        if winner | loser | winner_loser == True: 

            # Get profit data to form winner/loser group. 
            data = get_price_change_rate(
                all_stocks, # entire A-share
                len(rank_trade_date) # rank period
            ).T 
            # Transpose to make the index is stock list, \
            # while the column is date list. 

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

            # Loser strategy. 
            if loser:
                context.stock_list = list(
                    data.index[
                        :portfolio_length
                    ]
                )
            
            # Winner strategy. 
            elif winner:
                context.stock_list = list(
                    data.index[
                        -portfolio_length:
                    ]
                )
        


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
                inplace = True, 
                ascending = False
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

        if small | large != False:

            # Market capital data for small & large strategy.
            if total_mktcap:
                code =  fundamentals.eod_derivative_indicator.market_cap
                name = 'market_cap'
            elif outstanding_mktcap:
                code = fundamentals.eod_derivative_indicator.a_share_market_val_2
                name = 'a_share_market_val_2'
            elif A_share_mktcap:
                code = fundamentals.eod_derivative_indicator.a_share_market_val
                name = 'a_share_market_val'

            # Get market capital data. 
            mktcap_data = get_fundamentals(
                query(
                    code
                ).filter(
                    fundamentals.income_statement.stockcode.in_(
                        all_stocks
                    )
                )
            ).T
            # Transpose it to make index be stock list, \
            # while column be variable list. 

            # Small strategy. 
            if small:
                
                # Sort by market capital, \
                # from smallest to largest. 
                mktcap_data.sort_values(
                    by = name, 
                    inplace = True
                )

                # Pick the intersection of small & winner/loser\ 
                # as the final trading list. 
                context.stock_list = set(
                    all_stocks
                ).intersection(
                    list(
                        mktcap_data.index
                    )[
                        :small
                    ]
                )
            
            if large:
                
                # Sort by market capital, \
                # from largest to smallest. 
                mktcap_data.sort_values(
                    by = name, 
                    inplace = True, 
                    ascending = False
                )

                # Pick the intersection of large & winner/loser\ 
                # as the final trading list. 
                context.stock_list = set(
                    all_stocks
                ).intersection(
                    list(
                        mktcap_data.index
                    )[
                        :large
                    ]
                )

        if ST == False:
            context.stock_list = [
                x for x in context.stock_list if is_st_stock(x) == False
            ]
        
        elif ST == 'only':
            context.stock_list = [
                x for x in context.stock_list if is_st_stock(x) == True
            ]

        if small_mktcap | large_mktcap == True:

            mktcap_data = get_fundamentals(
                query(
                    code
                ).filter(
                    fundamentals.income_statement.stockcode.in_(
                        context.stock_list
                    )
                )
            ).T
        
            if small_mktcap:

                mktcap_data[
                    'Rank'
                ] = mktcap_data[
                    name
                ].rank(ascending = False)
            
            elif large_mktcap:

                mktcap_data[
                    'Rank'
                ] = mktcap_data[
                    name
                ].rank()

            total_weight = mktcap_data[
                'Rank'
            ].sum()

        if volatility:

            # Get profit data to form winner/loser group. 
            volatility_data = get_price_change_rate(
                context.stock_list, 
                len(rank_trade_date) # rank period
            ).T 
            # Transpose to make the index is stock list, \
            # while the column is date list. 

            # Add volatility column, defined as the variance\
            # of the price change rate in rank period. 
            volatility_data['Volatility'] = volatility_data.var(axis = 1)

            volatility_data['Rank'] = volatility_data[
                'Volatility'
            ].rank(
                ascending = False
            )

            total_weight = volatility_data['Rank'].sum()

        # Increment position adjustment. 
        
        # Sell out the stocks that's \
        # not included in the next positions. 

        # Form the sell list. 
        sell_stocks = []
        for holding_stock in \
        context.portfolio.positions.keys():
            if holding_stock not in context.stock_list:
                sell_stocks.append(holding_stock)
        
        for holding_stock in sell_stocks:
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
            if equally:
                order_target_percent(
                    stock, 
                    1 / len(context.stock_list)
                )
            
            # Small market capital weighted. 
            elif small_mktcap:
                order_target_percent(
                    stock, 
                    mktcap_data.loc[
                        stock, 
                        'Rank'
                    ] / total_weight
                )
            
            # Large market capital weighted. 
            elif large_mktcap:
                order_target_percent(
                    stock, 
                    mktcap_data.loc[
                        stock, 
                        'Rank'
                    ] / total_weight
                )
            
            # Volatility weighted. 
            elif volatility:
                order_target_percent(
                    stock, 
                    volatility_data.loc[
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