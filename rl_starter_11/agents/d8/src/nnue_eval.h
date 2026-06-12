#pragma once
#include <cstdint>
#include <array>
#include <algorithm>
#include <cstring>
#include <cmath>

#if defined(__ARM_NEON)
#include <arm_neon.h>
#elif defined(__AVX2__)
#include <immintrin.h>
#endif

extern "C" {
extern const uint8_t nn_nnue[];
extern const uint32_t nn_nnue_len;
}

namespace NNUE {

struct NNUEParameters {
    const int16_t* friend_ft_bias;      // size 256
    const int16_t* friend_ft_weights;   // size 49216 * 256
    const int16_t* enemy_ft_bias;       // size 256
    const int16_t* enemy_ft_weights;    // size 43840 * 256
    
    struct IsolatedBucket {
        const int32_t* l2_biases;       // size 32
        const int8_t* l2_weights;       // size 32 * 32
        const int32_t* l3_bias;         // size 1
        const int8_t* l3_weights;       // size 32
    } isolated_buckets[4];
    
    struct MainStack {
        const int32_t* l1_biases;       // size 16
        const int8_t* l1_weights;       // size 16 * 1024
        const int32_t* l2_biases;       // size 32
        const int8_t* l2_weights;       // size 32 * 32
        const int32_t* l3_bias;         // size 1
        const int8_t* l3_weights;       // size 32
    } main_stacks[4];
};

inline NNUEParameters get_parameters() {
    NNUEParameters p;
    const uint8_t* base = nn_nnue;
    
    p.friend_ft_bias = reinterpret_cast<const int16_t*>(base + 193);
    p.friend_ft_weights = reinterpret_cast<const int16_t*>(base + 705);
    p.enemy_ft_bias = reinterpret_cast<const int16_t*>(base + 25199297);
    p.enemy_ft_weights = reinterpret_cast<const int16_t*>(base + 25199809);
    
    size_t fc_start = 47645889;
    
    // Isolated Buckets 0-3 (L2 + L3 only, stride 1188 bytes each)
    for (int i = 0; i < 4; i++) {
        size_t bucket_offset = fc_start + 272 + i * 1188;
        p.isolated_buckets[i].l2_biases = reinterpret_cast<const int32_t*>(base + bucket_offset);
        p.isolated_buckets[i].l2_weights = reinterpret_cast<const int8_t*>(base + bucket_offset + 128);
        p.isolated_buckets[i].l3_bias = reinterpret_cast<const int32_t*>(base + bucket_offset + 1152);
        p.isolated_buckets[i].l3_weights = reinterpret_cast<const int8_t*>(base + bucket_offset + 1156);
    }
    
    // Main Stacks 0-3 (L1 + L2 + L3, stride 17640 bytes each)
    size_t main_start = fc_start + 272 + 4 * 1188; // 47650913
    for (int i = 0; i < 4; i++) {
        size_t stack_offset = main_start + i * 17640;
        p.main_stacks[i].l1_biases = reinterpret_cast<const int32_t*>(base + stack_offset + 4);
        p.main_stacks[i].l1_weights = reinterpret_cast<const int8_t*>(base + stack_offset + 68);
        p.main_stacks[i].l2_biases = reinterpret_cast<const int32_t*>(base + stack_offset + 16452);
        p.main_stacks[i].l2_weights = reinterpret_cast<const int8_t*>(base + stack_offset + 16580);
        p.main_stacks[i].l3_bias = reinterpret_cast<const int32_t*>(base + stack_offset + 17604);
        p.main_stacks[i].l3_weights = reinterpret_cast<const int8_t*>(base + stack_offset + 17608);
    }
    
    return p;
}

inline int orient(int pov, int sq) {
    return (pov == 0) ? sq : (sq ^ 56); // 0 = White, 1 = Black
}

inline int friend_idx(int piece_type, int color, int sq, int king_sq, int side_to_move) {
    int p_idx = (piece_type - 1) * 2 + (color != side_to_move);
    int oriented_sq = orient(side_to_move, sq);
    int oriented_king_sq = orient(side_to_move, king_sq);
    return 1 + oriented_sq + p_idx * 64 + oriented_king_sq * 769;
}

inline int enemy_idx(int piece_type, int color, int sq, int king_sq, int side_to_move) {
    int them_pov = !side_to_move;
    
    // Exclude opponent's king (Us King from Them PoV)
    if (piece_type == 6 && color == side_to_move) {
        return -1;
    }
    
    int them_king_sq = orient(them_pov, king_sq);
    int oriented_sq = orient(them_pov, sq);
    int plane_offset = 0;
    
    if (piece_type == 1) { // Pawn
        int pawn_plane = (color == them_pov) ? 0 : 1;
        plane_offset = 1 + pawn_plane * 48 + (oriented_sq - 8);
    } else {
        int pt_idx = (piece_type - 2) * 2 + (color != them_pov);
        plane_offset = 1 + 96 + pt_idx * 64 + oriented_sq;
    }
    
    return plane_offset + them_king_sq * 685;
}

// Add a feature to the accumulator
inline void accum_add(int16_t* acc, const int16_t* weights, int idx) {
    const int16_t* w = weights + idx * 256;
#if defined(__ARM_NEON)
    for (int i = 0; i < 256; i += 8) {
        int16x8_t a = vld1q_s16(acc + i);
        int16x8_t b = vld1q_s16(w + i);
        vst1q_s16(acc + i, vaddq_s16(a, b));
    }
#elif defined(__AVX2__)
    for (int i = 0; i < 256; i += 16) {
        __m256i a = _mm256_load_si256(reinterpret_cast<const __m256i*>(acc + i));
        __m256i b = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(w + i));
        _mm256_store_si256(reinterpret_cast<__m256i*>(acc + i), _mm256_add_epi16(a, b));
    }
#else
    for (int i = 0; i < 256; i++) {
        acc[i] += w[i];
    }
#endif
}

// Subtract a feature from the accumulator
inline void accum_sub(int16_t* acc, const int16_t* weights, int idx) {
    const int16_t* w = weights + idx * 256;
#if defined(__ARM_NEON)
    for (int i = 0; i < 256; i += 8) {
        int16x8_t a = vld1q_s16(acc + i);
        int16x8_t b = vld1q_s16(w + i);
        vst1q_s16(acc + i, vsubq_s16(a, b));
    }
#elif defined(__AVX2__)
    for (int i = 0; i < 256; i += 16) {
        __m256i a = _mm256_load_si256(reinterpret_cast<const __m256i*>(acc + i));
        __m256i b = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(w + i));
        _mm256_store_si256(reinterpret_cast<__m256i*>(acc + i), _mm256_sub_epi16(a, b));
    }
#else
    for (int i = 0; i < 256; i++) {
        acc[i] -= w[i];
    }
#endif
}

inline int32_t floor_div_64(int32_t x) {
    return (x >= 0) ? (x / 64) : ((x - 63) / 64);
}

inline void activate(const int16_t* acc, int8_t* out) {
    for (int i = 0; i < 256; i++) {
        out[i]       = static_cast<int8_t>(std::clamp<int32_t>(acc[i],  0, 127));
        out[i + 256] = static_cast<int8_t>(std::clamp<int32_t>(-acc[i], 0, 127));
    }
}


inline void propagate_l1(const int8_t* in, const int8_t* weights, const int32_t* biases, int32_t* out) {
    for (int r = 0; r < 16; r++) {
        const int8_t* w_row = weights + r * 1024;
        int32_t sum = biases[r];
        
#if defined(__AVX2__)
        __m256i sum_v = _mm256_setzero_si256();
        for (int c = 0; c < 1024; c += 32) {
            __m256i in_v = _mm256_load_si256(reinterpret_cast<const __m256i*>(in + c));
            __m256i w_v = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(w_row + c));
            
            __m256i mad = _mm256_maddubs_epi16(in_v, w_v);
            __m256i one = _mm256_set1_epi16(1);
            __m256i mad32 = _mm256_madd_epi16(mad, one);
            
            sum_v = _mm256_add_epi32(sum_v, mad32);
        }
        alignas(32) int32_t temp[8];
        _mm256_store_si256(reinterpret_cast<__m256i*>(temp), sum_v);
        sum += temp[0] + temp[1] + temp[2] + temp[3] + temp[4] + temp[5] + temp[6] + temp[7];
#elif defined(__ARM_NEON)
        int32x4_t sum_v = vdupq_n_s32(0);
        for (int c = 0; c < 1024; c += 16) {
            int8x16_t in_v = vld1q_s8(in + c);
            int8x16_t w_v = vld1q_s8(w_row + c);
            
            int16x8_t prod_lo = vmull_s8(vget_low_s8(in_v), vget_low_s8(w_v));
            int16x8_t prod_hi = vmull_s8(vget_high_s8(in_v), vget_high_s8(w_v));
            
            sum_v = vaddw_s16(sum_v, vget_low_s16(prod_lo));
            sum_v = vaddw_s16(sum_v, vget_high_s16(prod_lo));
            sum_v = vaddw_s16(sum_v, vget_low_s16(prod_hi));
            sum_v = vaddw_s16(sum_v, vget_high_s16(prod_hi));
        }
        sum += vaddvq_s32(sum_v);
#else
        for (int c = 0; c < 1024; c++) {
            sum += static_cast<int32_t>(in[c]) * static_cast<int32_t>(w_row[c]);
        }
#endif
        out[r] = sum;
    }
}

inline void propagate_l2(const int8_t* in, const int8_t* weights, const int32_t* biases, int32_t* out) {
    for (int r = 0; r < 32; r++) {
        const int8_t* w_row = weights + r * 32;
        int32_t sum = biases[r];
        
#if defined(__AVX2__)
        __m256i in_v = _mm256_load_si256(reinterpret_cast<const __m256i*>(in));
        __m256i w_v = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(w_row));
        __m256i mad = _mm256_maddubs_epi16(in_v, w_v);
        __m256i one = _mm256_set1_epi16(1);
        __m256i mad32 = _mm256_madd_epi16(mad, one);
        
        alignas(32) int32_t temp[8];
        _mm256_store_si256(reinterpret_cast<__m256i*>(temp), mad32);
        sum += temp[0] + temp[1] + temp[2] + temp[3] + temp[4] + temp[5] + temp[6] + temp[7];
#elif defined(__ARM_NEON)
        int32x4_t sum_v = vdupq_n_s32(0);
        for (int c = 0; c < 32; c += 16) {
            int8x16_t in_v = vld1q_s8(in + c);
            int8x16_t w_v = vld1q_s8(w_row + c);
            int16x8_t prod_lo = vmull_s8(vget_low_s8(in_v), vget_low_s8(w_v));
            int16x8_t prod_hi = vmull_s8(vget_high_s8(in_v), vget_high_s8(w_v));
            sum_v = vaddw_s16(sum_v, vget_low_s16(prod_lo));
            sum_v = vaddw_s16(sum_v, vget_high_s16(prod_lo));
            sum_v = vaddw_s16(sum_v, vget_low_s16(prod_hi));
            sum_v = vaddw_s16(sum_v, vget_high_s16(prod_hi));
        }
        sum += vaddvq_s32(sum_v);
#else
        for (int c = 0; c < 32; c++) {
            sum += static_cast<int32_t>(in[c]) * static_cast<int32_t>(w_row[c]);
        }
#endif
        out[r] = sum;
    }
}

inline int32_t propagate_l3(const int8_t* in, const int8_t* weights, int32_t bias) {
    int32_t sum = bias;
#if defined(__AVX2__)
    __m256i in_v = _mm256_load_si256(reinterpret_cast<const __m256i*>(in));
    __m256i w_v = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(weights));
    __m256i mad = _mm256_maddubs_epi16(in_v, w_v);
    __m256i one = _mm256_set1_epi16(1);
    __m256i mad32 = _mm256_madd_epi16(mad, one);
    
    alignas(32) int32_t temp[8];
    _mm256_store_si256(reinterpret_cast<__m256i*>(temp), mad32);
    sum += temp[0] + temp[1] + temp[2] + temp[3] + temp[4] + temp[5] + temp[6] + temp[7];
#elif defined(__ARM_NEON)
    int32x4_t sum_v = vdupq_n_s32(0);
    for (int c = 0; c < 32; c += 16) {
        int8x16_t in_v = vld1q_s8(in + c);
        int8x16_t w_v = vld1q_s8(weights + c);
        int16x8_t prod_lo = vmull_s8(vget_low_s8(in_v), vget_low_s8(w_v));
        int16x8_t prod_hi = vmull_s8(vget_high_s8(in_v), vget_high_s8(w_v));
        sum_v = vaddw_s16(sum_v, vget_low_s16(prod_lo));
        sum_v = vaddw_s16(sum_v, vget_high_s16(prod_lo));
        sum_v = vaddw_s16(sum_v, vget_low_s16(prod_hi));
        sum_v = vaddw_s16(sum_v, vget_high_s16(prod_hi));
    }
    sum += vaddvq_s32(sum_v);
#else
    for (int c = 0; c < 32; c++) {
        sum += static_cast<int32_t>(in[c]) * static_cast<int32_t>(weights[c]);
    }
#endif
    return sum;
}

inline int32_t evaluate(int oriented_king_us, int oriented_king_them, const int16_t* acc_us, const int16_t* acc_them) {
    static NNUEParameters p = get_parameters();
    
    int bucket_us = 7 - (oriented_king_us / 8);
    
    alignas(32) int8_t in_l1[1024];
    activate(acc_us, in_l1);
    activate(acc_them, in_l1 + 512);
    
    int stack_idx = bucket_us % 4;
    alignas(32) int32_t out_l1[16];
    propagate_l1(in_l1, p.main_stacks[stack_idx].l1_weights, p.main_stacks[stack_idx].l1_biases, out_l1);
    
    alignas(32) int8_t in_l2[32];
    for (int i = 0; i < 16; i++) {
        int32_t val_scaled = floor_div_64(out_l1[i]);
        in_l2[i] = std::clamp<int32_t>(val_scaled, 0, 127);
        in_l2[i + 16] = std::clamp<int32_t>(-val_scaled, 0, 127);
    }
    
    alignas(32) int32_t out_l2[32];
    const int8_t* l2_weights;
    const int32_t* l2_biases;
    const int8_t* l3_weights;
    int32_t l3_bias;
    
    if (bucket_us < 4) {
        l2_weights = p.isolated_buckets[bucket_us].l2_weights;
        l2_biases = p.isolated_buckets[bucket_us].l2_biases;
        l3_weights = p.isolated_buckets[bucket_us].l3_weights;
        l3_bias = *p.isolated_buckets[bucket_us].l3_bias;
    } else {
        int main_idx = bucket_us - 4;
        l2_weights = p.main_stacks[main_idx].l2_weights;
        l2_biases = p.main_stacks[main_idx].l2_biases;
        l3_weights = p.main_stacks[main_idx].l3_weights;
        l3_bias = *p.main_stacks[main_idx].l3_bias;
    }
    
    propagate_l2(in_l2, l2_weights, l2_biases, out_l2);
    
    alignas(32) int8_t in_l3[32];
    for (int i = 0; i < 32; i++) {
        int32_t val_scaled = floor_div_64(out_l2[i]);
        in_l3[i] = std::clamp<int32_t>(val_scaled, 0, 127);
    }
    
    int32_t raw_score = propagate_l3(in_l3, l3_weights, l3_bias);
    return raw_score;
}

} // namespace NNUE
