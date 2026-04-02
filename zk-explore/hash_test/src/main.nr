fn main() {
    let d: [u8; 4] = [1, 2, 3, 4];
    let _h = std::hash::blake2s(d);
    let _b = std::hash::blake3(d);
    let _p = std::hash::pedersen_hash([1, 2, 3, 4]);
}
