h1 = context.get('params', {}).get('h1')
h2 = context.get('params', {}).get('h2')

if not h1 or not h2:
    result = {"error": "Missing h1 or h2 for diff"}
else:
    try:
        log(f"Differ: Comparing {h1} vs {h2}...")
        
        # Use the secure 'read_blob' primitive injected by the Linker
        # This replaces the need for 'import os' and direct file access
        m1_raw = read_blob(h1)
        m2_raw = read_blob(h2)
            
        if not m1_raw or not m2_raw:
            result = {"error": "One or both manifests could not be read."}
        else:
            m1 = json.loads(m1_raw).get("capabilities", {})
            m2 = json.loads(m2_raw).get("capabilities", {})
            
            diff_report = {"added": {}, "removed": {}, "updated": {}, "identical": []}
            all_caps = set(m1.keys()) | set(m2.keys())
            for cap in all_caps:
                if cap not in m1: diff_report["added"][cap] = m2[cap]
                elif cap not in m2: diff_report["removed"][cap] = m1[cap]
                elif m1[cap] != m2[cap]: diff_report["updated"][cap] = {"old": m1[cap], "new": m2[cap]}
                else: diff_report["identical"].append(cap)
            
            result = diff_report
            log("Differ: Diff complete.")
    except Exception as e:
        result = {"error": str(e)}
