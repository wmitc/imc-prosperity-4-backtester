from prosperity4bt.datamodel import Order, TradingState

LIMITS = {
    "HYDROGEL_PACK": 200,
    "VELVETFRUIT_EXTRACT": 200,
    "VEV_4000": 300, "VEV_4500": 300, "VEV_5000": 300,
    "VEV_5100": 300, "VEV_5200": 300, "VEV_5300": 300,
    "VEV_5400": 300, "VEV_5500": 300,
}


class Trader:
    def run(self, state: TradingState):
        orders: dict[str, list[Order]] = {}

        for product, od in state.order_depths.items():
            if product not in LIMITS:
                continue

            limit = LIMITS[product]
            pos = state.position.get(product, 0)

            if product == "HYDROGEL_PACK":
                orders[product] = self._hp(pos, limit)
            elif product == "VELVETFRUIT_EXTRACT":
                orders[product] = self._vef_long(od, pos, limit)
            else:
                orders[product] = self._market_make(product, od, pos, limit)

        return orders, 0, ""

    def _hp(self, pos: int, limit: int) -> list[Order]:
        # Fixed fair-value quotes: HP mean-reverts to ~10000, spread 16
        product_orders = []
        buy_qty = limit - pos
        sell_qty = limit + pos
        if buy_qty > 0:
            product_orders.append(Order("HYDROGEL_PACK", 9992, buy_qty))
        if sell_qty > 0:
            product_orders.append(Order("HYDROGEL_PACK", 10008, -sell_qty))
        return product_orders

    def _vef_long(self, od, pos: int, limit: int) -> list[Order]:
        # VEF trends up ~+15-28 pts/day; go max long aggressively
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

    def _market_make(self, product: str, od, pos: int, limit: int) -> list[Order]:
        if not od.buy_orders or not od.sell_orders:
            return []
        best_bid = max(od.buy_orders)
        best_ask = min(od.sell_orders)
        product_orders = []
        buy_qty = limit - pos
        sell_qty = limit + pos
        if buy_qty > 0:
            product_orders.append(Order(product, best_bid, buy_qty))
        if sell_qty > 0:
            product_orders.append(Order(product, best_ask, -sell_qty))
        return product_orders
