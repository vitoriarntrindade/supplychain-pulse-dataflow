from scripts.factories import (
    OrderCreatedFactory,
    OrderDelayedFactory,
    InventoryLowFactory,
)


def test_order_created_factory() -> None:
    event = OrderCreatedFactory()
    assert event["event_type"] == "order_created"
    assert "expected_delivery" in event


def test_order_delayed_factory() -> None:
    event = OrderDelayedFactory()
    assert event["event_type"] == "order_delayed"
    assert "new_delivery" in event


def test_inventory_low_factory() -> None:
    event = InventoryLowFactory()
    assert event["event_type"] == "inventory_low"
    assert event["threshold"] > 0
