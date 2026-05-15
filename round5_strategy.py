import json

from prosperity4bt.datamodel import Order, TradingState

LIMIT = 10
TS_500 = 50000
TS_2000 = 200000

# Go max long from tick 0 (consistently up all 3 days)
LONG0 = {"PANEL_2X4", "UV_VISOR_RED", "SNACKPACK_STRAWBERRY"}

# Go max short from tick 0 (consistently down all 3 days)
SHORT0 = {"MICROCHIP_OVAL", "PEBBLES_XS", "UV_VISOR_AMBER", "PEBBLES_S"}

# Wait until tick 500; signal > 0 → long, signal < 0 → short
NORM500 = {
    "MICROCHIP_RECTANGLE", "PEBBLES_L", "PANEL_1X4",
    "GALAXY_SOUNDS_PLANETARY_RINGS", "MICROCHIP_CIRCLE",
    "TRANSLATOR_VOID_BLUE", "UV_VISOR_MAGENTA",
    "ROBOT_VACUUMING", "ROBOT_DISHES", "TRANSLATOR_ASTRO_BLACK",
}

# Wait until tick 500; price dips early → goes up (signal < 0 → long, > 0 → short)
INV500 = {
    "UV_VISOR_YELLOW", "OXYGEN_SHAKE_GARLIC", "GALAXY_SOUNDS_BLACK_HOLES",
    "SLEEP_POD_POLYESTER", "SLEEP_POD_COTTON", "ROBOT_IRONING",
    "GALAXY_SOUNDS_SOLAR_FLAMES", "GALAXY_SOUNDS_DARK_MATTER",
    "ROBOT_LAUNDRY", "OXYGEN_SHAKE_CHOCOLATE", "SNACKPACK_PISTACHIO",
    "TRANSLATOR_SPACE_GRAY",
}

# Wait until tick 2000; signal > 0 → long, signal < 0 → short
NORM2000 = {
    "PEBBLES_XL", "MICROCHIP_SQUARE", "PEBBLES_M", "SLEEP_POD_NYLON",
    "SLEEP_POD_SUEDE", "OXYGEN_SHAKE_EVENING_BREATH", "OXYGEN_SHAKE_MORNING_BREATH",
}

# Wait until tick 2000; price dips/peaks early → reverses (signal < 0 → long, > 0 → short)
INV2000 = {
    "PANEL_4X4", "ROBOT_MOPPING", "PANEL_2X2", "SLEEP_POD_LAMB_WOOL",
    "UV_VISOR_ORANGE", "OXYGEN_SHAKE_MINT", "TRANSLATOR_ECLIPSE_CHARCOAL",
    "TRANSLATOR_GRAPHITE_MIST", "GALAXY_SOUNDS_SOLAR_WINDS", "PANEL_1X2",
    "SNACKPACK_RASPBERRY", "MICROCHIP_TRIANGLE", "SNACKPACK_CHOCOLATE",
    "SNACKPACK_VANILLA",
}

ALL_PRODUCTS = LONG0 | SHORT0 | NORM500 | INV500 | NORM2000 | INV2000


class Trader:
    def run(self, state: TradingState):
        data = json.loads(state.traderData) if state.traderData else {}
        opens: dict[str, float] = data.get("opens", {})
        dirs: dict[str, str] = data.get("dirs", {})

        orders: dict[str, list[Order]] = {}
        ts = state.timestamp

        for product, od in state.order_depths.items():
            if product not in ALL_PRODUCTS:
                continue
            if not od.buy_orders or not od.sell_orders:
                continue

            pos = state.position.get(product, 0)
            mid = (max(od.buy_orders) + min(od.sell_orders)) / 2

            if product not in opens:
                opens[product] = mid

            direction: str | None = dirs.get(product)

            if product in LONG0:
                direction = "long"
            elif product in SHORT0:
                direction = "short"
            elif direction is None:
                signal = mid - opens[product]
                if product in NORM500 and ts >= TS_500:
                    dirs[product] = "long" if signal > 0 else "short"
                    direction = dirs[product]
                elif product in INV500 and ts >= TS_500:
                    dirs[product] = "long" if signal < 0 else "short"
                    direction = dirs[product]
                elif product in NORM2000 and ts >= TS_2000:
                    dirs[product] = "long" if signal > 0 else "short"
                    direction = dirs[product]
                elif product in INV2000 and ts >= TS_2000:
                    dirs[product] = "long" if signal < 0 else "short"
                    direction = dirs[product]

            if direction is None:
                continue

            if direction == "long":
                orders[product] = self._go_long(product, od, pos)
            else:
                orders[product] = self._go_short(product, od, pos)

        data["opens"] = opens
        data["dirs"] = dirs
        return orders, 0, json.dumps(data)

    def _go_long(self, product: str, od, pos: int) -> list[Order]:
        buy_qty = LIMIT - pos
        if buy_qty <= 0:
            return []
        orders = []
        remaining = buy_qty
        for ask in sorted(od.sell_orders):
            vol = min(remaining, -od.sell_orders[ask])
            if vol > 0:
                orders.append(Order(product, ask, vol))
                remaining -= vol
            if remaining == 0:
                return orders
        if remaining > 0:
            orders.append(Order(product, max(od.buy_orders), remaining))
        return orders

    def _go_short(self, product: str, od, pos: int) -> list[Order]:
        sell_qty = LIMIT + pos
        if sell_qty <= 0:
            return []
        orders = []
        remaining = sell_qty
        for bid in sorted(od.buy_orders, reverse=True):
            vol = min(remaining, od.buy_orders[bid])
            if vol > 0:
                orders.append(Order(product, bid, -vol))
                remaining -= vol
            if remaining == 0:
                return orders
        if remaining > 0:
            orders.append(Order(product, min(od.sell_orders), -remaining))
        return orders
