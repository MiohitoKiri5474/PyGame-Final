import extensions


def test_run_ticks_calls_registered_callbacks_with_world_and_dt(monkeypatch):
    monkeypatch.setattr(extensions, "_tick_callbacks", [])
    calls = []
    extensions.register_tick(lambda world, dt: calls.append((world, dt)))
    extensions.register_tick(lambda world, dt: calls.append((world, dt)))

    sentinel_world = object()
    extensions.run_ticks(sentinel_world, 0.5)

    assert calls == [(sentinel_world, 0.5), (sentinel_world, 0.5)]


def test_run_ticks_is_a_no_op_with_no_callbacks(monkeypatch):
    monkeypatch.setattr(extensions, "_tick_callbacks", [])
    extensions.run_ticks(object(), 1.0)  # must not raise


def test_run_ticks_calls_in_registration_order(monkeypatch):
    monkeypatch.setattr(extensions, "_tick_callbacks", [])
    order = []
    extensions.register_tick(lambda world, dt: order.append("first"))
    extensions.register_tick(lambda world, dt: order.append("second"))

    extensions.run_ticks(object(), 0.1)

    assert order == ["first", "second"]
