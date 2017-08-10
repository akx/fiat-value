from decimal import Decimal
from collections import defaultdict


def parse_balance_pairs(pairs):
    balances = defaultdict(Decimal)
    for pair in pairs:
        try:
            asset, value = pair.split('=')
            balances[asset] += Decimal(value)
        except Exception as exc:
            raise ValueError('Unable to parse %s (%s)' % (pair, exc))
    return balances


def merge_balances(bal_dicts):
    merged_bal = defaultdict(Decimal)
    for bal in bal_dicts:
        for key, value in bal.items():
            merged_bal[key] += value
    return merged_bal
