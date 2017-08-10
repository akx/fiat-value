def compute_fiat_values(*, ticker, balances, pvs, fiat='USD'):

    rows = []
    for coin, balance in sorted(balances.items()):
        if pvs['buy'][coin]:
            buy_prices, buy_vols = zip(*pvs['buy'][coin])
            bought_total = sum(buy_vols)
            avg_buy_price = sum(buy_prices) / len(buy_prices)  # TODO: This could be better
            price_of_bought = avg_buy_price * bought_total
        else:
            avg_buy_price = None
            bought_total = 0
            price_of_bought = 0

        free_total = balance - bought_total
        ticker_value = ticker.get(coin, 1)
        curr_value_of_free = free_total * ticker_value
        curr_value_of_bought = bought_total * ticker_value
        curr_value_total = (curr_value_of_free + curr_value_of_bought)
        fiat_position = curr_value_of_free + (curr_value_of_bought - price_of_bought)
        position_perc = (
            '%+.2f%%' % (((curr_value_total / price_of_bought) - 1) * 100)
            if (fiat_position and price_of_bought)
            else (
                'free money :)'
                if curr_value_total > 0 and price_of_bought == 0
                else None
            )
        )
        rows.append({
            'coin': coin,
            'avg_buy_price': avg_buy_price,
            'balance': balance,
            'bought_total': bought_total,
            'free_total': free_total,
            'buy_value': price_of_bought,
            ('current_%s' % fiat): curr_value_total,
            ('free_%s' % fiat): curr_value_of_free,
            ('bought_%s' % fiat): curr_value_of_bought,
            ('position_%s' % fiat): fiat_position,
            'position%': position_perc,
        })
    return rows
