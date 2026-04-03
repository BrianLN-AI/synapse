# Linker Blob (f_6 Matryoshka)
# This blob allows a Linker to run inside a Linker.

# 1. Get the target task and virtualized root from context
virtual_root = context.get('params', {}).get('virtual_root', 'sub_fabric')
target_h = context.get('params', {}).get('target_h')
sub_context = context.get('params', {}).get('context', {})

log(f"Matryoshka: Initializing sub-fabric at {virtual_root}...")

# 2. Setup Sub-Linker
# We rely on the parent's environment to provide the necessary classes
# since we are running in the same process but a different scope.
try:
    # In a real f_6, we'd import these or they'd be pre-injected
    # For the seed, we assume the parent Linker injected the factory logic.
    adapter = VaultAdapter(root_dir=virtual_root)
    sub_linker = Linker(adapter)
    
    log(f"Matryoshka: Invoking sub-task {target_h}...")
    res = sub_linker.invoke(target_h, sub_context)
    
    result = {
        "status": "success",
        "sub_fabric_root": virtual_root,
        "sub_result": res
    }
except Exception as e:
    log(f"Matryoshka Error: {str(e)}")
    result = {"status": "error", "error": str(e)}
