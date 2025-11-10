from typing import List, Optional
import hmac


class Person:
    """Abstract base class for all people in the system."""

    def __init__(self, person_id: int, name: str, email: str, *, email_verified: bool = False):
        self.person_id = person_id
        self.name = name
        self.email = email
        self.email_verified = email_verified  # New: track verification

    def display_info(self):
        return f"{self.name} ({self.email})"

    # New: simple lifecycle helpers
    def verify_email(self) -> None:
        """Mark the person's email as verified."""
        self.email_verified = True

    def update_email(self, new_email: str) -> None:
        """Update email and reset verification."""
        self.email = new_email
        self.email_verified = False


class User(Person):
    """Represents a registered user who can shop."""

    def __init__(self, user_id: int, name: str, email: str, password: str, *, is_active: bool = True):
        super().__init__(user_id, name, email)
        self._password = password  # Protected: sensitive data
        self._orders: List["Order"] = []  # Protected: internal state
        self._cart: Optional["ShoppingCart"] = None  # Protected: internal state
        self.is_active = is_active  # New: account status
        self.deactivated_reason: Optional[str] = None  # New: optional note

    # Refactor: centralize lazy cart creation
    def _ensure_cart(self) -> "ShoppingCart":
        if not self._cart:
            from .shopping import ShoppingCart
            self._cart = ShoppingCart(self)
        return self._cart

    def login(self, email: str, password: str) -> bool:
        """Authenticate the user (inactive users cannot log in)."""
        return (
            self.is_active
            and self.email == email
            and hmac.compare_digest(self._password, password)
        )

    def change_password(self, old_password: str, new_password: str) -> bool:
        """Change password if the old password matches."""
        if not hmac.compare_digest(self._password, old_password):
            return False
        self._password = new_password
        return True

    def deactivate(self, reason: Optional[str] = None) -> None:
        """Deactivate the user to prevent login/checkout."""
        self.is_active = False
        self.deactivated_reason = reason

    def add_to_cart(self, candy: "Candy", quantity: int):
        """Add candy to shopping cart."""
        cart = self._ensure_cart()
        cart.add_item(candy, quantity)

    def checkout(self, payment_method: "PaymentMethod"):
        """Convert shopping cart into an order."""
        if not self._cart:
            raise ValueError("Cart is empty")
        order = self._cart.create_order(payment_method)
        self._orders.append(order)
        self._cart.clear()
        return order

    def get_orders(self) -> List["Order"]:
        """Get a copy of the user's orders."""
        return self._orders.copy()

    def get_cart(self) -> Optional["ShoppingCart"]:
        """Get the user's shopping cart."""
        return self._cart

    @property
    def order_count(self) -> int:
        """Convenience: number of orders placed by the user."""
        return len(self._orders)


class Staff(User):
    """Represents store employees — inherits from User."""

    def __init__(self, user_id: int, name: str, email: str, password: str, position: str):
        super().__init__(user_id, name, email, password)
        self.position = position

    def update_inventory(self, candy: "Candy", new_quantity: int):
        """Update the quantity of a candy in inventory (with validation)."""
        if new_quantity < 0:
            raise ValueError("Quantity cannot be negative")
        candy.quantity = new_quantity

    def view_sales_report(self, orders: List["Order"], *, currency: str = "$"):
        """Generate a sales report with order count and a configurable currency symbol."""
        total = sum(order.total_amount for order in orders)
        return f"Orders: {len(orders)}, Total sales: {currency}{total:.2f}"
