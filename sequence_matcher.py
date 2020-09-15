from difflib import SequenceMatcher


def match(a, b):
    if SequenceMatcher(None, a, b).ratio() >= 0.65:
        return True
    for i in b.split():
        if SequenceMatcher(None, a, i).ratio() >= 0.65:
            return True

    for i in a.split():
        if SequenceMatcher(None, b, i).ratio() >= 0.65:
            return True

    return False
