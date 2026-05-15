import json

from prosperity4bt.datamodel import Order, TradingState

LIMITS = {
    "HYDROGEL_PACK": 200,
    "VELVETFRUIT_EXTRACT": 200,
    "VEV_4000": 300, "VEV_4500": 300, "VEV_5000": 300,
    "VEV_5100": 300, "VEV_5200": 300, "VEV_5300": 300,
    "VEV_5400": 300, "VEV_5500": 300,
}

# Wait until timestamp 50000 (tick 500, 5% of day) before committing VEF direction.
# If price is ≥10 pts below the open, the day is in a downtrend → short.
# Otherwise assume uptrend → long.
VEF_SIGNAL_TS = 50000
VEF_DOWN_THRESHOLD = -10


class Trader:
    def run(self, state: TradingState):
        data = json.loads(state.traderData) if state.traderData else {}
        vef_open = data.get("vef_open")
        vef_dir = data.get("vef_dir")  # "long" or "short"; None = not yet determined

        orders: dict[str, list[Order]] = {}

        for product, od in state.order_depths.items():
            if product not in LIMITS:
                continue
            limit = LIMITS[product]
            pos = state.position.get(product, 0)

            if product == "HYDROGEL_PACK":
                orders[product] = self._hp(pos, limit)
            elif product == "VELVETFRUIT_EXTRACT":
                if od.buy_orders and od.sell_orders:
                    mid = (max(od.buy_orders) + min(od.sell_orders)) / 2
                    if vef_open is None:
                        vef_open = mid
                    if vef_dir is None and state.timestamp >= VEF_SIGNAL_TS:
                        vef_dir = "short" if mid - vef_open < VEF_DOWN_THRESHOLD else "long"
                    if vef_dir == "long":
                        orders[product] = self._vef_long(od, pos, limit)
                    elif vef_dir == "short":
                        orders[product] = self._vef_short(od, pos, limit)
                    # else: no trade during the wait window
            else:
                orders[product] = self._market_make(product, od, pos, limit)

        data["vef_open"] = vef_open
        data["vef_dir"] = vef_dir
        return orders, 0, json.dumps(data)

    def _hp(self, pos: int, limit: int) -> list[Order]:
        orders = []
        buy_qty = limit - pos
        sell_qty = limit + pos
        if buy_qty > 0:
            orders.append(Order("HYDROGEL_PACK", 9992, buy_qty))
        if sell_qty > 0:
            orders.append(Order("HYDROGEL_PACK", 10008, -sell_qty))
        return orders

    def _vef_long(self, od, pos: int, limit: int) -> list[Order]:
        buy_qty = limit - pos
        if buy_qty <= 0:
            return []
        orders = []
        remaining = buy_qty
        for ask in sorted(od.sell_orders):
            vol = min(remaining, -od.sell_orders[ask])
            if vol > 0:
                orders.append(Order("VELVETFRUIT_EXTRACT", ask, vol))
                remaining -= vol
            if remaining == 0:
                return orders
        if remaining > 0 and od.buy_orders:
            orders.append(Order("VELVETFRUIT_EXTRACT", max(od.buy_orders), remaining))
        return orders

    def _vef_short(self, od, pos: int, limit: int) -> list[Order]:
        sell_qty = limit + pos
        if sell_qty <= 0:
            return []
        orders = []
        remaining = sell_qty
        for bid in sorted(od.buy_orders, reverse=True):
            vol = min(remaining, od.buy_orders[bid])
            if vol > 0:
                orders.append(Order("VELVETFRUIT_EXTRACT", bid, -vol))
                remaining -= vol
            if remaining == 0:
                return orders
        if remaining > 0 and od.sell_orders:
            orders.append(Order("VELVETFRUIT_EXTRACT", min(od.sell_orders), -remaining))
        return orders

    def _market_make(self, product: str, od, pos: int, limit: int) -> list[Order]:
        if not od.buy_orders or not od.sell_orders:
            return []
        best_bid = max(od.buy_orders)
        best_ask = min(od.sell_orders)
        orders = []
        buy_qty = limit - pos
        sell_qty = limit + pos
        if buy_qty > 0:
            orders.append(Order(product, best_bid, buy_qty))
        if sell_qty > 0:
            orders.append(Order(product, best_ask, -sell_qty))
        return orders
