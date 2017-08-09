from argparse import ArgumentParser
from configparser import RawConfigParser

import krakenex
from decimal import Decimal

from collections import defaultdict
from tabulate import tabulate

from call_cacher import CallCacher
from libfiatvalue import compute_fiat_values, get_balances, get_order_prices_and_vols

config = RawConfigParser()
config.read('fiat-value.cfg')


def parse_balance_pairs(pairs):
    balances = defaultdict(Decimal)
    for pair in pairs:
        try:
            asset, value = pair.split('=')
            balances[asset] += Decimal(value)
        except Exception as exc:
            raise ValueError('Unable to parse %s (%s)' % (pair, exc))
    return balances

def main():
    ap = ArgumentParser()
    ap.add_argument('--fiat', default='USD', help='fiat currency (default %(default)s)')
    ap.add_argument('--set-balance', '-B', nargs='*', help='set balance of given asset to X, e.g. BTC=10', metavar='ASSET=VALUE')
    ap.add_argument('--add-balance', '-b', nargs='*', help='add to balance of given asset to X, e.g. BTC=10', metavar='ASSET=ADD')
    ap.add_argument('--cache-ttl', type=int, default=1280, help='data caching TTL (set to zero to disable; default %(default)s sec)')
    args = ap.parse_args()
    set_balances = parse_balance_pairs(args.set_balance or ())
    add_balances = parse_balance_pairs(args.add_balance or ())
    fiat = args.fiat
    kraken_api = krakenex.API(key=config.get('kraken', 'key'), secret=config.get('kraken', 'secret'))
    if args.cache_ttl > 0:
        kraken_api = CallCacher('kraken', kraken_api, ttl=args.cache_ttl)

    process_and_print(kraken_api, fiat, set_balances, add_balances)


def process_and_print(kraken_api, fiat, set_balances={}, add_balances={}):
    balances = get_balances(kraken_api)
    balances.update(set_balances)
    for asset, value in add_balances.items():
        balances[asset] = balances.get(asset, 0) + value
    pvs = get_order_prices_and_vols(kraken_api, fiat=fiat)
    rows = compute_fiat_values(kraken_api, balances=balances, pvs=pvs, fiat=fiat)
    print(tabulate(rows, headers='keys', floatfmt='+.2f'))
    print('--')
    total_fiat = sum(r['current_%s' % fiat] for r in rows)
    pos_fiat = sum(r['position_%s' % fiat] for r in rows)
    free_fiat = sum(r['free_%s' % fiat] for r in rows)
    print('Total %s: $%.2f' % (fiat, total_fiat))
    print('Pos.. %s: $%.2f' % (fiat, pos_fiat))
    print(' Free %s: $%.2f' % (fiat, free_fiat))


if __name__ == '__main__':
    main()
