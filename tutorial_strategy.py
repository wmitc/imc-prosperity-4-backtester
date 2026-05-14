from prosperity4bt.datamodel import Order, TradingState

LIMIT = 80


class Trader:
    def run(self, state: TradingState):
        orders: dict[str, list[Order]] = {}

        for product, order_depth in state.order_depths.items():
            position = state.position.get(product, 0)

            if product == "EMERALDS":
                orders[product] = self._emeralds(position)
            elif product == "TOMATOES":
                orders[product] = self._tomatoes(order_depth, position)

        return orders, 0, ""

    def _emeralds(self, position: int) -> list[Order]:
        # Fair value is exactly 10000. Market maker permanently quotes 9992/10008.
        # Bidding at 9992 and asking at 10008 intercepts all market trade flow
        # (our orders get priority before the market maker's residual).
        # Fill price = our order price, so lower bid = more profit per unit.
        orders = []

        buy_qty = LIMIT - position
        sell_qty = LIMIT + position

        if buy_qty > 0:
            orders.append(Order("EMERALDS", 9992, buy_qty))
        if sell_qty > 0:
            orders.append(Order("EMERALDS", 10008, -sell_qty))

        return orders

    def _tomatoes(self, order_depth, position: int) -> list[Order]:
        if not order_depth.buy_orders or not order_depth.sell_orders:
            return []

        best_bid = max(order_depth.buy_orders)
        best_ask = min(order_depth.sell_orders)

        # Quote at the market bid/ask levels. Fill price = our order price,
        # so best_bid gives the lowest cost on buys and best_ask the highest
        # revenue on sells. Our orders get priority over the market maker.
        orders = []
        buy_qty = LIMIT - position
        sell_qty = LIMIT + position

        if buy_qty > 0:
            orders.append(Order("TOMATOES", best_bid, buy_qty))
        if sell_qty > 0:
            orders.append(Order("TOMATOES", best_ask, -sell_qty))

        return orders
