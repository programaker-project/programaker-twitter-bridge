def ws_endpoint_to_callback_url(ws_endpoint):
    assert ws_endpoint.startswith("ws")
    assert ws_endpoint.endswith("communication")
    rest_root = ws_endpoint[: -len("communication")].replace("ws", "http", 1)
    return rest_root + "oauth_return"
