class PaperBroker:
    def __init__(self, balance):
        """
        Initialize the paper broker with a starting balance
        """
        self.balance = balance
        self.positions = {}  # symbol -> {qty, avg_price}
        self.trades = []     # history of executed trades

    def buy(self, symbol, price, qty):
        """
        Buy a given quantity at the given price.
        Returns True if successful, False if insufficient balance.
        """
        cost = price * qty
        if cost > self.balance:
            return False  # Not enough balance

        # Update balance and positions
        self.balance -= cost
        if symbol in self.positions:
            # Update average price for existing position
            pos = self.positions[symbol]
            total_qty = pos["qty"] + qty
            avg_price = (pos["qty"] * pos["avg_price"] + qty * price) / total_qty
            self.positions[symbol]["qty"] = total_qty
            self.positions[symbol]["avg_price"] = avg_price
        else:
            self.positions[symbol] = {"qty": qty, "avg_price": price}

        # Record the trade
        self.trades.append(("BUY", symbol, price, qty))
        return True

    def sell(self, symbol, price):
        """
        Sell the entire position for the given symbol.
        Returns the PnL from this trade.
        """
        pos = self.positions.get(symbol)
        if not pos:
            return 0  # No position to sell

        pnl = (price - pos["avg_price"]) * pos["qty"]
        self.balance += price * pos["qty"]

        # Record the trade and remove position
        self.trades.append(("SELL", symbol, price, pos["qty"], pnl))
        del self.positions[symbol]
        return pnl
