from prosperity4bt.datamodel import Order, TradingState

LIMIT = 80


class Trader:
    def run(self, state: TradingState):
        orders: dict[str, list[Order]] = {}

        for product, od in state.order_depths.items():
            pos = state.position.get(product, 0)

            if product == "ASH_COATED_OSMIUM":
                orders[product] = self._aco(od, pos)
            elif product == "INTARIAN_PEPPER_ROOT":
                orders[product] = self._ipr(od, pos)

        return orders, 0, ""

    def _aco(self, od, pos: int) -> list[Order]:
        # Mean-reverting around fair value ~10000. Market-make at bid/ask,
        # same principle as TOMATOES: quote at the market's own prices to
        # intercept trade flow with priority.
        if not od.buy_orders or not od.sell_orders:
            return []

        best_bid = max(od.buy_orders)
        best_ask = min(od.sell_orders)
        orders = []

        buy_qty = LIMIT - pos
        sell_qty = LIMIT + pos

        if buy_qty > 0:
            orders.append(Order("ASH_COATED_OSMIUM", best_bid, buy_qty))
        if sell_qty > 0:
            orders.append(Order("ASH_COATED_OSMIUM", best_ask, -sell_qty))

        return orders

    def _ipr(self, od, pos: int) -> list[Order]:
        # INTARIAN_PEPPER_ROOT trends +~1000 pts/day consistently.
        # Go max long as fast as possible: take from the order book at each
        # ask level (fills at their price), then place a passive bid to catch
        # sell market trades cheaply.
        buy_qty = LIMIT - pos
        if buy_qty <= 0:
            return []

        orders = []
        remaining = buy_qty

        for ask in sorted(od.sell_orders):
            vol = min(remaining, -od.sell_orders[ask])
            if vol > 0:
                orders.append(Order("INTARIAN_PEPPER_ROOT", ask, vol))
                remaining -= vol
            if remaining == 0:
                return orders

        if remaining > 0 and od.buy_orders:
            orders.append(Order("INTARIAN_PEPPER_ROOT", max(od.buy_orders), remaining))

        return orders
