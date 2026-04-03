# Prover Logic (f_11)
params = context.get('params', context)
target_h = params.get('target_h')
sub_context = params.get('context', {})

try:
    log(f"Prover: Initiating verified execution for {target_h}...")
    
    if not target_h:
        raise ValueError("Prover Error: No target_h provided")

    # --- f_11: PREVENT RECURSION ---
    if 'params' in sub_context:
        sub_context['params']['verify'] = False
    else:
        sub_context['verify'] = False

    # 1. Execute the logic
    # primitives (invoke, json, hashlib) are injected by Linker
    res_envelope = invoke(target_h, sub_context)
    result_val = res_envelope.get('result')
    
    # 2. Generate the Commitment (The Mock ZK-Proof)
    # Use pre-injected json and hashlib
    res_json = json.dumps(result_val, sort_keys=True)
    result_hash = hashlib.sha256(res_json.encode()).hexdigest()
    commitment_data = f"{target_h}:{result_hash}"
    
    # Sign commitment
    signature = crypto_sign(commitment_data)
    pubkey = get_public_key()
    
    log(f"Prover: Execution complete. Commitment signed.")
    
    result = {
        "status": "success",
        "result": result_val,
        "proof": {
            "type": "mock_zk_proof",
            "blob_hash": target_h,
            "result_hash": result_hash,
            "signature": signature,
            "prover_pubkey": pubkey
        }
    }
except Exception as e:
    log(f"Prover Error: {str(e)}")
    result = {"status": "error", "error": str(e)}
