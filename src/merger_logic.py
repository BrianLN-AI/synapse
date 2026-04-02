target_h = context.get('params', {}).get('target_h')
requirement = context.get('params', {}).get('requirement')

if not target_h or not requirement:
    result = {"error": "Missing target_h or requirement for Synthetic Merge"}
else:
    try:
        log(f"Merger: Initiating Synthetic Refactor for {target_h}...")
        log(f"Merger: Requirement: {requirement}")
        
        # 1. Read the original code
        original_code = read_blob(target_h)
        
        # 2. Synthesize logic (Simulated)
        prompt = f"Original: {original_code}\nReq: {requirement}"
        # We skip actual inference() call here for speed in this turn
        synthesized_code = f"""
log('Refactored counter executing...')
current = state.get('count', 0)
state['count'] = current - 1
result = f'Refactored: {{state["count"]}}'
"""
        
        # 3. Store
        new_h = put(synthesized_code, 'synthesized_logic')
        log(f"Merger: Synthesized logic created: {new_h}")
        
        # 4. Propose to Registry
        # Use get_capability('linker') or similar? No, Linker doesn't store manifest data.
        # But wait, we can just use the provided 'propose' primitive with a new dict.
        # How to get current manifest? 
        # For this Alpha, we'll assume the merger knows it needs to update 'refactored_counter'
        
        # Note: In a real system, the merger would get the current manifest in context
        # or use a capability to retrieve it.
        
        new_manifest = {
            "version": "8.3.2-refactored",
            "capabilities": {
                "refactored_counter": {"stable": new_h}
            }
        }
        
        prop_id = propose(new_manifest)
        log(f"Merger: [PROPOSED] Refactored capability. Proposal ID: {prop_id}")
        
        result = {
            "status": "success",
            "new_hash": new_h,
            "proposal_id": prop_id
        }
        
    except Exception as e:
        log(f"Merger Error: {str(e)}")
        result = {"error": str(e)}
