# fixture: logic/python — builds a greeting string, uses log()
name = context.get("name", "World")
log(f"greeting {name}")
result = f"Hello, {name}!"
