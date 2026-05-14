from prosperity4bt.datamodel import Order, OrderDepth, TradingState


class Trader:
    def run(self, state: TradingState):
        orders: dict[str, list[Order]] = {}

        for product, order_depth in state.order_depths.items():
            product_orders: list[Order] = []

            if order_depth.sell_orders:
                best_ask = min(order_depth.sell_orders)
                best_ask_vol = order_depth.sell_orders[best_ask]
                product_orders.append(Order(product, best_ask, -best_ask_vol))

            if order_depth.buy_orders:
                best_bid = max(order_depth.buy_orders)
                best_bid_vol = order_depth.buy_orders[best_bid]
                product_orders.append(Order(product, best_bid, -best_bid_vol))

            orders[product] = product_orders

        return orders, 0, ""
