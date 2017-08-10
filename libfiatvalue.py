from decimal import Decimal
from collections import defaultdict


def get_order_prices_and_vols(kraken_api, fiat='USD'):
    orders = kraken_api.query_private('ClosedOrders')

    buy_prices_and_vols = defaultdict(list)
    sell_prices_and_vols = defaultdict(list)

    for id, order in orders['result']['closed'].items():
        order_d = order['descr']
        coin = order_d['pair'][:3]
        o_fiat = order_d['pair'][3:]
        if fiat != o_fiat:
            continue
        price = Decimal(order['price'])
        qty = Decimal(order['vol_exec'])
        if order_d['type'] == 'buy':
            buy_prices_and_vols[coin].append((price, qty))
        elif order_d['type'] == 'sell':
            sell_prices_and_vols[coin].append((price, qty))
        else:
            raise NotImplementedError('...', order)

    return {
        'buy': buy_prices_and_vols,
        'sell': sell_prices_and_vols,
    }


def get_balances(kraken_api):
    balances = kraken_api.query_private('Balance')['result']
    return {asset[-3:]: Decimal(value) for (asset, value) in balances.items()}


def get_ticker(kraken_api, coins, fiat='USD'):
    pairs = ['%s%s' % (coin, fiat) for coin in coins if coin not in ('EUR', 'USD', fiat)]
    values = {}
    for pair, info in kraken_api.query_public('Ticker', {'pair': ','.join(pairs)})['result'].items():
        assert pair.endswith(fiat)
        if len(pair) == 8:
            coin = pair[1:4]
        elif len(pair) == 6:
            coin = pair[0:3]
        else:
            raise ValueError(pair)
        values[coin] = Decimal(info['o'])
    return values


def compute_fiat_values(kraken_api, *, balances, pvs, fiat='USD'):
    ticker = get_ticker(kraken_api, coins=balances.keys(), fiat=fiat)
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
