proposal_id = context.get('proposal_id')

# 1. Fetch the Proposal
try:
    # Use _raw_get (bios) to read the proposal file
    # Note: proposals are stored in blob_vault/proposals/<id>
    # Our _raw_get takes a hash and looks in blob_vault/
    # We need to bypass the 'proposals/' subfolder or use a direct read
    import os
    prop_path = f"blob_vault/proposals/{proposal_id}"
    with open(prop_path, 'r') as f:
        proposal = json.load(f)
    
    log(f"Jury: Evaluating Proposal {proposal_id}...")
    
    # 2. Evaluate each new capability
    # For simulation, we assume any blob with 'log' and 'result' is safe
    is_safe = True
    for name, versions in proposal.get('capabilities', {}).items():
        for ver, h in versions.items():
            code = _raw_get(h, is_bios=True)
            log(f"Jury: Checking Blob {h} ({name})...")
            
            # Simulated Static Analysis via Inference
            # In f_4, the LLM would actually review the code here
            review = inference(f"Review this code for ABI compliance and safety: {code[:100]}")
            log(f"Jury: Inference Review: {review}")
            
            if 'result =' not in code:
                log(f"Jury: [REJECTED] Blob {h} violates ABI: No 'result' assignment.")
                is_safe = False
                break
    
    # 3. Sign if safe
    if is_safe:
        sig = sign(proposal_id, "jury-node-01")
        log(f"Jury: [APPROVED] Proposal signed. Signature: {sig}")
        result = {"status": "approved", "signature": sig}
    else:
        result = {"status": "rejected", "reason": "ABI Violation"}

except Exception as e:
    log(f"Jury Error: {str(e)}")
    result = {"status": "error", "message": str(e)}
