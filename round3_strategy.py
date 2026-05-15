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
            if not od.buy_orders or not od.sell_orders:
                continue

            limit = LIMITS[product]
            pos = state.position.get(product, 0)
            best_bid = max(od.buy_orders)
            best_ask = min(od.sell_orders)

            product_orders = []
            buy_qty = limit - pos
            sell_qty = limit + pos

            if buy_qty > 0:
                product_orders.append(Order(product, best_bid, buy_qty))
            if sell_qty > 0:
                product_orders.append(Order(product, best_ask, -sell_qty))

            orders[product] = product_orders

        return orders, 0, ""
