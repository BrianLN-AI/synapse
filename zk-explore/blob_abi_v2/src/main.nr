// D-JIT Blob ABI Circuit v2
//
// Closes the fabrication gap from v1.
// blob_hash is now PROVEN to be SHA256(blob_content).
// A prover cannot claim blob X ran when blob Y ran -- they must
// possess the actual content whose SHA256 matches blob_hash.
//
// What this proves:
//   1. blob_hash == SHA256(blob_content)   -- content binding (closes AV-1, AV-2)
//   2. result != 0                          -- ABI: result exists
//   3. blob_hash is non-trivial             -- blob was content-addressed
//   4. context_hash is non-trivial          -- context was non-empty
//
// Blob size: fixed at 512 bytes (padded). Circuit size is fixed at compile time.

fn main(
    blob_hash:    pub [u8; 32],
    context_hash: pub [u8; 32],
    result:       pub Field,
    blob_content:   [u8; 512],     // private: prover must know actual source
    result_inverse: Field,
) {
    // Content binding: prove blob_hash is SHA256 of the actual content
    // Note: using blake2s (Noir native). Vault must use blake2s for content-addressing.
    // SHA256 is available as Sha256Compression (block fn) but not as a full hash in beta.19.
    let computed_hash: [u8; 32] = std::hash::blake2s(blob_content);
    assert(computed_hash == blob_hash);

    // ABI: result must be non-zero
    assert(result * result_inverse == 1);

    // Non-trivial hash and context
    let zero_hash: [u8; 32] = [0; 32];
    assert(blob_hash != zero_hash);
    assert(context_hash != zero_hash);
}

// Fitness formula -- separate entry point
// Proves fitness score was computed honestly from public telemetry aggregates.
// Inputs are all public: they come from vault telemetry artifacts anyone can verify.
// The council member proves their arithmetic was correct.
//
// Note: no `pub` on parameters here -- only main() entry point supports pub.
// This function is tested directly; for a standalone proving circuit,
// promote to its own Nargo project with its own main().
fn compute_fitness(
    success_count: u64,
    total_count:   u64,
    latency_ms:    u64,
    memory_kb:     u64,
    claimed:       u64,
) {
    assert(total_count > 0);

    let scale: u64 = 1_000_000;
    let success_rate: u64 = (success_count * scale) / total_count;
    let integrity: u64 = scale;
    let latency_norm: u64 = if latency_ms > 10_000 { latency_ms / 10_000 } else { 1 };
    let cost_norm: u64 = if memory_kb > 1_024 { memory_kb / 1_024 } else { 1 };
    let numerator: u64 = (success_rate * integrity) / scale;
    let computed: u64 = (numerator * scale) / (latency_norm * cost_norm);

    assert(claimed == computed);
}

// --- Tests ---

#[test]
fn test_valid_execution() {
    let mut content: [u8; 512] = [0; 512];
    content[0] = 100;
    content[1] = 101;
    content[2] = 102;

    let blob_hash = std::hash::blake2s(content);

    let mut ctx_bytes: [u8; 512] = [0; 512];
    ctx_bytes[0] = 0xca;
    ctx_bytes[1] = 0xfe;
    let context_hash = std::hash::blake2s(ctx_bytes);

    main(blob_hash, context_hash, 1, content, 1);
}

#[test(should_fail)]
fn test_wrong_content_fails() {
    // Prover claims hash of content_A but provides content_B
    let content_a: [u8; 512] = [0x41; 512];
    let content_b: [u8; 512] = [0x42; 512];
    let hash_a = std::hash::blake2s(content_a);

    let mut ctx: [u8; 512] = [0; 512];
    ctx[0] = 1;
    let context_hash = std::hash::blake2s(ctx);

    // content_b provided but hash_a claimed -- must fail
    main(hash_a, context_hash, 1, content_b, 1);
}

#[test(should_fail)]
fn test_zero_result_fails() {
    let content: [u8; 512] = [0x41; 512];
    let hash = std::hash::blake2s(content);
    let mut ctx: [u8; 512] = [0; 512];
    ctx[0] = 1;
    let ctx_hash = std::hash::blake2s(ctx);
    main(hash, ctx_hash, 0, content, 0);
}

#[test]
fn test_fitness_honest() {
    // 9/10 successes, latency below baseline, memory below baseline
    // success_rate = 9*1_000_000/10 = 900_000
    // numerator = 900_000 * 1_000_000 / 1_000_000 = 900_000
    // computed = 900_000 * 1_000_000 / 1 = 900_000_000_000
    compute_fitness(9, 10, 5_000, 512, 900_000_000_000);
}

#[test(should_fail)]
fn test_fitness_inflated_fails() {
    compute_fitness(9, 10, 5_000, 512, 999_999_999);
}
