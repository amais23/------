#if defined(__APPLE__)
.global _nn_nnue
.global _nn_nnue_len
_nn_nnue:
    .incbin "weights/nn.nnue"
_nn_nnue_end:
_nn_nnue_len:
    .long _nn_nnue_end - _nn_nnue
#else
.global nn_nnue
.global nn_nnue_len
.type nn_nnue, @object
.type nn_nnue_len, @object
nn_nnue:
    .incbin "weights/nn.nnue"
nn_nnue_end:
nn_nnue_len:
    .long nn_nnue_end - nn_nnue
#endif
