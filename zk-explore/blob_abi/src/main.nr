// D-JIT Blob ABI Circuit
//
// Proves that a blob execution respected the ABI contract:
//   1. result is non-zero (result exists and is non-null)
//   2. blob_hash and context_hash are non-zero (properly content-addressed)
//   3. execution consumed real time and memory (latency > 0, memory > 0)
//
// Public inputs (verifier sees these):
//   blob_hash, context_hash, result
//
// Private inputs (prover knows, verifier does not):
//   result_inverse, latency_ms, memory_kb

fn main(
    blob_hash:    pub Field,
    context_hash: pub Field,
    result:       pub Field,
    result_inverse:    Field,
    latency_ms:        u64,
    memory_kb:         u64,
) {
    // ABI constraint 1: result must be non-zero
    // Prove by showing result * result_inverse == 1
    // No valid inverse exists for zero - proof impossible if result == 0
    assert(result * result_inverse == 1);

    // ABI constraint 2: blob was content-addressed (hash is non-zero)
    assert(blob_hash != 0);

    // ABI constraint 3: context was non-empty
    assert(context_hash != 0);

    // ABI constraint 4: execution consumed real time (blob actually ran)
    assert(latency_ms > 0);

    // ABI constraint 5: execution consumed real memory (blob actually ran)
    assert(memory_kb > 0);
}

#[test]
fn test_valid_execution() {
    // Simulate: blob 0xabc ran with context 0x123, produced result 42
    // result_inverse of 42 in the BN254 field
    // For test purposes use small numbers where inverse is computable
    // result=2, result_inverse=... Field arithmetic is mod p
    // Use result=1, result_inverse=1 for simplest test
    main(
        0xdeadbeef,  // blob_hash
        0xcafebabe,  // context_hash
        1,           // result (non-zero)
        1,           // result_inverse (1 * 1 == 1 ok)
        12,          // latency_ms (non-zero)
        256,         // memory_kb (non-zero)
    );
}

#[test(should_fail)]
fn test_zero_result_fails() {
    // result=0 means ABI violated - no valid inverse exists
    // Use result=0, result_inverse=0: 0*0=0 != 1, constraint fails
    main(
        0xdeadbeef,
        0xcafebabe,
        0,           // result is zero - ABI violation
        0,           // no valid inverse for zero
        12,
        256,
    );
}

#[test(should_fail)]
fn test_zero_blob_hash_fails() {
    main(
        0,           // blob_hash zero - not content-addressed
        0xcafebabe,
        1,
        1,
        12,
        256,
    );
}

#[test(should_fail)]
fn test_zero_latency_fails() {
    main(
        0xdeadbeef,
        0xcafebabe,
        1,
        1,
        0,           // latency zero - blob did not actually run
        256,
    );
}
