# Qwen3-ASR on the Dedicated Mac mini

- Type: investigation
- Status: benchmark policy accepted; no model has been installed or benchmarked
- Date: 2026-07-18
- Scope: Roy AI Editor Concert Live; dedicated M4 Mac mini with 24 GB unified memory

## Executive decision

Qwen3-ASR is worth a controlled benchmark, but it is **not yet a production dependency** and it must not become the text authority for Concert Live.

The useful split is:

- `Qwen3-ASR-0.6B` is a candidate for language/transcript evidence and rough acoustic navigation.
- `Qwen3-ForcedAligner-0.6B` is a candidate for timestamps against the already-approved Japanese lyrics.
- `Qwen3-ASR-1.7B` is an accuracy challenger, not the default first download.
- `stable-ts`/Whisper remains the current benchmark baseline until Qwen passes the same Japanese-singing fixtures.
- The Production Core must keep an `AlignmentAdapter`; no manifest or subtitle stage should depend on Qwen-specific output.

The 24 GB M4 has plausible *memory capacity* for the nominal 0.6B ASR plus 0.6B aligner, and probably for 1.7B plus 0.6B at batch size 1. That is an engineering estimate, not a compatibility result. Qwen currently documents Transformers and vLLM/CUDA paths, not a supported Metal or MLX path. Therefore the Mac experiment is `unsupported/unknown until measured`, not “Mac supported.” Move inference to NVIDIA only if the same model passes quality but the Mac fails the operational gates below; a GPU cannot repair bad singing alignment.

## What Qwen released

The official collection contains six checkpoints: original `qwen-asr` variants and matching Transformers-native `-hf` variants for two ASR sizes and one forced aligner. All are Apache-2.0 licensed.

| Role | Original checkpoint | Transformers-native checkpoint | Official capability relevant here |
| --- | --- | --- | --- |
| ASR, higher accuracy | `Qwen/Qwen3-ASR-1.7B` | `Qwen/Qwen3-ASR-1.7B-hf` | Offline/streaming ASR, language ID, long audio |
| ASR, smaller | `Qwen/Qwen3-ASR-0.6B` | `Qwen/Qwen3-ASR-0.6B-hf` | Same task surface, smaller accuracy/throughput trade-off |
| Forced alignment | `Qwen/Qwen3-ForcedAligner-0.6B` | `Qwen/Qwen3-ForcedAligner-0.6B-hf` | Text–audio alignment, word or character timestamps, maximum five minutes |

The ASR checkpoints list 30 languages plus 22 Chinese dialects. Japanese is explicitly included. Their supported audio-type table explicitly includes `Speech`, `Singing Voice`, and `Songs with BGM`. By contrast, the forced aligner's table says `NAR Speech`; it lists Japanese among 11 supported languages, but does **not** claim singing support. See the [official collection](https://huggingface.co/collections/Qwen/qwen3-asr), [Qwen3-ASR model card](https://huggingface.co/Qwen/Qwen3-ASR-1.7B), and [Transformers-native model card](https://huggingface.co/Qwen/Qwen3-ASR-1.7B-hf).

This distinction is decisive for Roy AI Editor:

- Qwen officially claims that ASR can recognize singing and music-backed vocals.
- It does not establish that the forced aligner accurately follows elongated vowels, breaths, melisma, ad-libs, overlapping singers, crowd vocals, or repeated lyric lines.
- Word/character timestamps are not mora timestamps. Japanese orthographic characters also do not map one-to-one to sung morae.
- Qwen output may propose timing evidence; the approved Lyrics Packet, performed repeats, singer attribution, and line map remain the Concert Live text authority.

## Runtime and Apple Silicon support

Qwen's official Python package exposes two backends:

1. Transformers, installed via `qwen-asr`.
2. vLLM, installed via `qwen-asr[vllm]`, which Qwen recommends for fastest inference and streaming.

The published examples use `torch.bfloat16`, `device_map="cuda:0"`, and optionally FlashAttention 2. The streaming path is vLLM-only and does not return timestamps. Timestamp output requires the separate forced aligner. The native Transformers checkpoints are newer integration points and currently instruct installing Transformers from source. These details are in the [official Qwen repository](https://github.com/QwenLM/Qwen3-ASR) and [native model card](https://huggingface.co/Qwen/Qwen3-ASR-1.7B-hf).

Support status:

| Path | Status for this project | Reason |
| --- | --- | --- |
| NVIDIA CUDA + Qwen Transformers | Officially documented | Qwen examples use CUDA and bf16 |
| NVIDIA CUDA + vLLM | Officially documented and preferred for throughput | Qwen and vLLM document this deployment path |
| macOS CPU + Transformers | Technically testable, but not a Qwen performance target | Generic PyTorch path; no Qwen Mac result supplied |
| macOS MPS/Metal + Transformers | **Unsupported/unknown** | PyTorch has an MPS backend, but Qwen provides no MPS recipe, compatibility matrix, or benchmark |
| Apple MLX | **No official implementation/checkpoint found** | Neither the Qwen collection/repository nor Apple's MLX project lists an official Qwen3-ASR port |
| vLLM on macOS | Not a production option | vLLM's documented full runtime is Linux-oriented; Qwen's install path is CUDA |

[PyTorch's MPS documentation](https://docs.pytorch.org/docs/stable/notes/mps) shows that generic PyTorch models can move to the `mps` device. It does not guarantee that every Qwen3-ASR operator is implemented or fast. PyTorch documents `PYTORCH_ENABLE_MPS_FALLBACK` for unsupported operations; a run that silently spends material time on CPU should fail this project's Metal gate rather than be reported as GPU success. [MLX](https://github.com/ml-explore/mlx) is Apple's Apple-silicon framework, but framework availability is not model support.

### 24 GB capacity estimate

Using checkpoint names as nominal parameter counts:

- 0.6B ASR + 0.6B aligner: about 1.2B parameters, or roughly 2.4 GB of bf16 weights before runtime overhead.
- 1.7B ASR + 0.6B aligner: about 2.3B parameters, or roughly 4.6 GB of bf16 weights before runtime overhead.

This is only a lower-bound inference estimate. Audio features, activations, KV cache, temporary tensors, PyTorch, and macOS all share the 24 GB pool. Batch size 1 and one short song at a time are therefore plausible; concurrency and whole-concert inference are not justified. Reserve at least 6 GB for the OS and editor services, and fail the trial if peak process plus GPU allocation exceeds 18 GB or causes swap pressure.

The official collection supplies no Qwen- or Apple-published 8-bit/4-bit or MLX-quantized checkpoint. Third-party conversions may exist, but they are outside this decision. Do not make an unverified quantized conversion part of the Production Toolchain; first establish the bf16 reference output and then require a separate parity benchmark.

## Long audio policy

Qwen says the ASR models handle long audio, while forced alignment is limited to five minutes. Concert Live already has better segmentation evidence: Roy's Provided Setlist Timeline.

The adapter should therefore:

1. cut each selected track from its timeline anchor with boundary padding;
2. run ASR only as evidence, with Japanese supplied as a language hint;
3. feed the **approved** performed lyric text to the aligner;
4. keep each alignment request at four minutes or less, leaving overlap below the official five-minute ceiling;
5. split longer songs at approved line boundaries with 5–10 seconds overlap, reconcile duplicated lines deterministically, and preserve source offsets;
6. reject non-monotonic, missing, duplicated, or out-of-range timestamps rather than silently repairing the Lyrics Packet.

Streaming adds no value to the first Production Golden Path because Qwen's streaming mode does not return timestamps. Offline, song-scoped jobs are easier to checkpoint and reproduce.

## Benchmark before adoption

Use the same extracted 16 kHz mono WAV and approved lyrics for every candidate. Keep at least 12 fixtures:

- four clean solo Japanese songs;
- two songs with dense BGM;
- two elongated/melismatic songs;
- two repeated-line/ad-lib cases;
- one duet or overlapping-vocal case;
- one song longer than five minutes, exercised through deterministic chunking.

Hand-label line starts and ends and a smaller sample of mora/character landmarks. The mora landmarks evaluate observed usefulness only; they do not redefine Qwen's output as a mora aligner.

| Candidate | Host/backend | Purpose |
| --- | --- | --- |
| Current baseline | Mac, stable-ts/Whisper | Control; current adapter behavior |
| Qwen small | Mac CPU, `Qwen3-ASR-0.6B-hf` + aligner | Compatibility fallback and correctness reference |
| Qwen small | Mac MPS, same checkpoints | Preferred local experiment if all operators remain on Metal |
| Qwen large | Mac MPS, 1.7B ASR + aligner | Test only if small ASR loses material lyric evidence |
| Qwen small/large | NVIDIA CUDA Transformers | Determine whether failures are Mac backend/runtime failures |
| Qwen small/large | NVIDIA CUDA vLLM | Throughput challenger, not required for single-job correctness |

### Pass/fail metrics

All quality metrics are computed against Roy-approved lyrics and hand-reviewed timing, not the model's free transcription.

| Gate | Pass | Fail consequence |
| --- | --- | --- |
| Reproducibility | Same model/revision/input produces the same line map and timestamps within 20 ms across three runs | Do not adopt |
| Coverage | At least 98% of approved performed lines receive monotonic in-range timing; no invented or silently dropped line | Exception Review / baseline wins |
| Line timing | Median absolute boundary error <= 250 ms and p95 <= 600 ms | Not production-ready |
| Severe cuts | Zero clipped first syllables, missing performed repeats, or early cuts of sustained final vocals in the fixture | Not production-ready |
| Human repair | No more than 2% of lines need manual boundary repair, and not worse than stable-ts | Baseline wins |
| Local throughput | End-to-end real-time factor <= 1.0 for 0.6B ASR + aligner at batch 1 | Quality may pass, but use remote GPU or keep baseline |
| Local stability | Completes all fixtures, peak allocation <= 18 GB, no swap storm, no crash, and no material CPU fallback in the MPS run | Mac path fails |
| Chunk seam | No duplicate/missing approved line and <= 250 ms seam discontinuity | Chunker fails |

Also record Japanese character error rate for free ASR, language-ID mistakes, model revision, package revisions, device, dtype, wall time, peak memory, and every fallback. CER helps compare transcript evidence; it does not override the Lyrics Packet.

## When to use NVIDIA

Escalate to an external NVIDIA worker only when all of the following are true:

1. Qwen beats or materially complements stable-ts on the fixture's alignment/coverage gates.
2. The identical checkpoint succeeds on CUDA.
3. The M4 run fails only an operational gate: unsupported MPS op, memory pressure, crash, or real-time factor above 1.0.
4. The remote worker can accept a content-addressed audio job, return a versioned evidence artifact, and avoid becoming the project store.

Do **not** escalate merely because CUDA is faster, and do not escalate a model that fails Japanese singing quality: hardware changes runtime, not the learned alignment behavior. A first CUDA worker should have at least 16 GB VRAM as a conservative engineering target for bf16 ASR plus aligner and runtime headroom; measure before permitting concurrency.

## Comparison with the current baseline

[`stable-ts`](https://github.com/jianfch/stable-ts) already provides Whisper transcription, forced alignment of supplied text, word timestamps, refinement, silence suppression, and adapters for other ASR outputs; it also documents an MLX Whisper option on Apple Silicon. Its own documentation warns that silence-based adjustment is most reliable when speech is clearly louder than background sound, which is specifically questionable for a mastered concert mix.

Qwen's advantages to test are explicit Japanese support, official ASR claims for singing/BGM, and a dedicated 0.6B aligner. Its disadvantages today are the aligner's speech-only support claim, the five-minute alignment limit, and the absence of an official Apple backend. Neither system may be treated as authoritative mora karaoke timing without fixture evidence and burned-pixel review.

## Recommended implementation order

1. Keep the existing `AlignmentAdapter` and stable-ts baseline.
2. Add a benchmark-only Qwen adapter interface, with model and revision pinned; do not add Qwen to bootstrap yet.
3. Benchmark `0.6B-hf + ForcedAligner-0.6B-hf` on CPU and MPS without downloading 1.7B first.
4. If compatible and within memory, compare its line timings to stable-ts.
5. Test 1.7B only when the small model's ASR evidence fails and the aligner's timing remains promising.
6. Test NVIDIA only under the escalation rule above.
7. Promote an adapter only after all fixtures pass; continue to store timing as evidence with its exact model/backend versions.

No installation decision should be made from model-card benchmark claims alone. For Roy AI Editor, the acceptance target is the actual Japanese 3D Live mix and the approved performed lyric structure.
