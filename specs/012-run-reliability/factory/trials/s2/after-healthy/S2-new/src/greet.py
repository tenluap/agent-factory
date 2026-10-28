def greet(name):
    if not name.strip():
        name = "stranger"
    return f"Hello, {name}!"
