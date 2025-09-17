import factory
import random
from datetime import datetime, timedelta, UTC


class BaseEventFactory(factory.Factory):
    """Factory base para eventos de cadeia de suprimentos."""

    class Meta:
        model = dict

    event_id = factory.LazyAttribute(
        lambda _: f"EVT-{random.randint(1000,9999)}"
    )
    timestamp = factory.LazyFunction(lambda: datetime.now(UTC).isoformat())
    supplier = factory.Iterator(
        ["Fornecedor_A", "Fornecedor_B", "Fornecedor_C"]
    )
    sku = factory.Iterator(["SKU123", "SKU456", "SKU789", "SKU321"])
    qty = factory.LazyFunction(lambda: random.randint(1, 500))


class OrderCreatedFactory(BaseEventFactory):
    """Evento: pedido criado."""

    event_type = "order_created"
    order_id = factory.LazyAttribute(
        lambda _: f"ORD-{random.randint(10000,99999)}"
    )
    expected_delivery = factory.LazyFunction(
        lambda: (
            datetime.now(UTC) + timedelta(days=random.randint(2, 10))
        ).isoformat()
    )


class OrderDelayedFactory(BaseEventFactory):
    """Evento: pedido atrasado."""

    event_type = "order_delayed"
    order_id = factory.LazyAttribute(
        lambda _: f"ORD-{random.randint(10000,99999)}"
    )
    old_delivery = factory.LazyFunction(
        lambda: (
            datetime.now(UTC) + timedelta(days=random.randint(1, 5))
        ).isoformat()
    )
    new_delivery = factory.LazyFunction(
        lambda: (
            datetime.now(UTC) + timedelta(days=random.randint(6, 15))
        ).isoformat()
    )


class InventoryLowFactory(BaseEventFactory):
    """Evento: estoque baixo."""

    event_type = "inventory_low"
    threshold = factory.LazyFunction(lambda: random.randint(10, 50))
