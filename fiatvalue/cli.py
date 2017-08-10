from argparse import ArgumentParser
from configparser import RawConfigParser, NoOptionError

from collections import defaultdict
from tabulate import tabulate

from .call_cacher import CallCacher
from .compute import compute_fiat_values
from .exchanges.bitstamp import BitstampAPI
from .exchanges.kraken import KrakenAPI
from .utils import merge_balances, parse_balance_pairs


def get_balances(active_apis, add_balances, set_balances):
    balance_dicts = [add_balances] + [api.get_balances() for api in active_apis]
    balances = merge_balances(balance_dicts)
    balances.update(set_balances)
    return balances


def get_pvs(active_apis, fiat):
    merged_pvs = {'buy': defaultdict(list), 'sell': defaultdict(list)}
    for api in active_apis:
        pvs = api.get_order_prices_and_vols(fiat)
        for kind in ('buy', 'sell'):
            for coin in pvs.get(kind, {}):
                merged_pvs[kind][coin].extend(pvs[kind][coin])
    return merged_pvs


def initialize_apis(config, cache_ttl):
    api_classes = [KrakenAPI, BitstampAPI]
    for klass in api_classes:
        try:
            api = klass(
                client_id=config.get(klass.id, 'customer_id', fallback=None),
                api_key=config.get(klass.id, 'key'),
                api_secret=config.get(klass.id, 'secret'),
            )
        except NoOptionError:
            continue
        if cache_ttl > 0:
            api = CallCacher(klass.id, api, ttl=cache_ttl)
        yield api


def main():
    ap = ArgumentParser()
    ap.add_argument('--fiat', default='USD', help='fiat currency (default %(default)s)')
    ap.add_argument('--set-balance', '-B', nargs='*', help='set balance of given asset to X, e.g. BTC=10', metavar='ASSET=VALUE')
    ap.add_argument('--add-balance', '-b', nargs='*', help='add to balance of given asset to X, e.g. BTC=10', metavar='ASSET=ADD')
    ap.add_argument('--cache-ttl', type=int, default=1280, help='data caching TTL (set to zero to disable; default %(default)s sec)')
    args = ap.parse_args()
    config = RawConfigParser()
    config.read('fiat-value.cfg')
    set_balances = parse_balance_pairs(args.set_balance or ())
    add_balances = parse_balance_pairs(args.add_balance or ())
    fiat = args.fiat
    apis = list(initialize_apis(config, cache_ttl=args.cache_ttl))
    active_apis = [api for api in apis if api.enabled]
    balances = get_balances(active_apis, add_balances, set_balances)
    pvs = get_pvs(active_apis, fiat)
    ticker = active_apis[0].get_ticker(coins=list(balances.keys()), fiat=fiat)
    rows = compute_fiat_values(ticker=ticker, balances=balances, pvs=pvs, fiat=fiat)
    print(tabulate(rows, headers='keys', floatfmt='+.2f'))
    print('--')
    total_fiat = sum(r['current_%s' % fiat] for r in rows)
    pos_fiat = sum(r['position_%s' % fiat] for r in rows)
    free_fiat = sum(r['free_%s' % fiat] for r in rows)
    print('Total %s: %.2f' % (fiat, total_fiat))
    print('Pos.. %s: %.2f' % (fiat, pos_fiat))
    print(' Free %s: %.2f' % (fiat, free_fiat))
