# Small/Local LLMs and VLMs on Edge Hardware for Robot Agents (2024–2026)

Notes compiled 2026-10-17. Verification status: "[verified]" means I opened the page and read the number there. "[search-snippet only]" means the number came from a search summary and I did not open the page. Leaderboard numbers carry their snapshot dates.

## 1. How accurate are 1–8B models at tool calling, compared with frontier models? Are there robot-specific evaluations?

### Takeaway
On BFCL, 7–8B models fine-tuned for tool use (xLAM-2-8B, ToolACE-2-8B, Hammer2.1-7B, Tool-N1-7B) match or beat GPT-4o-class models on single-turn calls. They also hold up much better than general instruct models on multi-turn calls. Below 3B, accuracy drops off clearly. General instruct models such as Qwen2.5-7B and Llama-3.1-8B score 5–11 points below the fine-tuned ones. Robot-specific evaluations of small models are scarce and mostly informal.

### Cited Findings
- BFCL v3 snapshot dated 04/03/2025, overall / multi-turn accuracy: xLAM-2-70b-fc-r 78.19 / 75.12; xLAM-2-8b-fc-r 72.83 / 69.25 (rank 4); GPT-4o-2024-11-20 (Prompt) 72.08 / 47.62; GPT-4o-2024-11-20 (FC) 69.58 / 41.0; ToolACE-2-8B 68.39 / 36.88; xLAM-2-3b-fc-r 65.11 / 56.00 (rank 14); Qwen2.5-14B-Instruct (FC) 58.90 / 15.88; xLAM-2-1b-fc-r 58.90 / 43.12; ToolACE-8B 58.42 / 7.75. [verified] — [APIGen-MT / xLAM-2 paper, arXiv 2504.03601 (HTML v4)](https://arxiv.org/html/2504.03601v4)
- τ-bench pass@1, Retail / Airline / Overall: xLAM-2-8b-fc-r 58.2 / 35.2 / 46.7; xLAM-2-70b-fc-r 67.1 / 45.2 / 56.2; gpt-4o-2024-11-20 62.8 / 43.0 / 52.9. So the 8B model falls about 6 points short of GPT-4o on long-horizon agentic tasks. [verified] — [arXiv 2504.03601](https://arxiv.org/html/2504.03601v4)
- BFCL non-live/live category averages, last updated 2025-04-13 (the "Overall" column here is the mean of the two categories and is not comparable to the v3 overall score above): Tool-N1-7B 84.82; Tool-N1-14B 85.97; GPT-4o 83.97; GPT-4o-mini 81.64; ToolACE-8B 82.57; Hammer2.1-7B 81.88; xLAM-2-70b 80.70; Qwen2.5-7B-Instruct 76.95; Llama-3.1-8B-Instruct 72.65. Tool-N1 is Qwen2.5-Instruct trained with RL using a rule-based reward on whether the tool call is correct. [verified] — [Nemotron-Research-Tool-N1, arXiv 2505.00024v2](https://arxiv.org/html/2505.00024v2)
- In the same Tool-N1 table, the live gap between general instruct models and fine-tuned ones is large: Qwen2.5-7B-Instruct 67.44 live vs Tool-N1-7B 80.38; Llama-3.1-8B 61.08 live. [verified] — [arXiv 2505.00024v2](https://arxiv.org/html/2505.00024v2)
- The Hammer models (ICLR 2025) were built for on-device function calling. They are trained with function-masking augmentation so that they respond correctly when the available functions are irrelevant. [search-snippet only; PDF not opened] — [Hammer, ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/file/d45e0bfb5a39477d56b55c0824200008-Paper-Conference.pdf)
- The live BFCL leaderboard page says "Last Updated: 2026-04-12". The table did not render in my fetch, so I have no current (2026) scores for Qwen3 0.6–8B, Gemma 3, Phi-4-mini, or SmolLM3. — [BFCL leaderboard](https://gorilla.cs.berkeley.edu/leaderboard.html)
- Robot-specific: a 2026 paper (ALRM) benchmarks ten LLMs on robotic manipulation, including small models up to 8B such as Qwen3-8B, to see whether models that run locally on a single GPU can do the job. [search-snippet only] — [ALRM, arXiv 2601.19510](https://arxiv.org/pdf/2601.19510)
- Robot-specific, informal: a ROS 2 tool-awareness evaluation (turtlesim and robot-arm agents) reportedly found that gpt-4o-mini, gpt-4o, qwen2.5:32b/70b and qwen3:8b/32b passed, while "the 7b parameter model almost succeeded but failed in the fourth task". [search-snippet only; the page returned 403 when fetched; blog post, not peer-reviewed] — [Hackster / AlbertaBeef](https://www.hackster.io/AlbertaBeef/evaluating-tool-awareness-of-llms-for-robotics-control-ba6f4b)
- A Fraunhofer FOKUS paper (ICCR 2025) tests small and medium off-the-shelf LMs, without fine-tuning, as an on-device planning layer for manipulation. It runs on a Jetson AGX Orin with Ollama and uses a minimal action vocabulary. [search-snippet only; the page was bot-blocked when fetched] — [Fraunhofer publica](https://publica.fraunhofer.de/handle/publica/507982)

### Inferences
- For a robot tool schema with about 5–15 tools, a 7–8B model fine-tuned for tool use (xLAM-2-8B, ToolACE-2-8B, Hammer2.1-7B) should beat stock Qwen2.5-7B-Instruct. The live BFCL subset gap is about 13 points (Tool-N1-7B vs Qwen2.5-7B). The user's current choice, Qwen2.5-7B via Ollama, is a reasonable baseline but not the strongest model in its size class.
- Multi-turn is where small general models fail most (Qwen2.5-14B scores 15.88% multi-turn), and a conversational robot agent is a multi-turn setting. Fine-tuning that targets multi-turn, as xLAM-2 does, matters more than raw parameter count.
- 1–3B models (xLAM-2-1b/3b) still reach 59–65% BFCL v3 overall. That is usable for a Pi-resident fallback with a small, fixed tool set, but not as the main planner.

### Gaps
- 2026 BFCL v4 scores for Qwen3 (0.6B–8B), Gemma 3, Phi-4-mini, Llama 3.2 1B/3B, and SmolLM2/3: the leaderboard table did not load. Check the live page or the BFCL-Result repo and date-stamp the numbers.
- API-Bank and ACEBench numbers for Tool-N1 appear only in a figure and could not be extracted.
- I found no peer-reviewed benchmark that measures small-model tool calling against ROS 2 / Nav2 action schemas with reported accuracy numbers.

## 2. Measured LLM/VLM inference speeds on the Pi 5, Hailo AI HAT, Jetson Orin, and consumer GPUs

### Takeaway
The Pi 5 CPU (Ollama, Q4_K_M) generates about 10–12 tokens/s for 1B-class models and about 5 tokens/s for 3B models. That is fine for short tool-call JSON, but only if the CPU is not already busy with Nav2/SLAM. The Hailo-10H AI HAT+ 2 shows no clear LLM advantage over the Pi 5 CPU in independent testing. A Jetson Orin Nano Super (8 GB) runs a 7B model at about 22 tokens/s, but VLMs on it are slow (single-digit tokens/s at best).

### Cited Findings
- Raspberry Pi 5, Ollama, Q4_K_M, tokens/s (RAM in MB): gemma3:1b 11.53 (1394); llama3.2:1b 11.22 (2416); qwen2.5:1.5b 9.97 (1849); smollm2:1.7b 8.23; granite3.1-dense:2b 5.81; qwen2.5:3b 5.2 (3026); llama3.2:3b 4.69 (4659); bitnet-b1.58-2B-4T (bitnet.cpp) 8.13 (1500). The page reports only one tokens/s figure per model and gives neither the Pi RAM size nor the date. [verified] — [Stratosphere Lab, Pi 5 LLM performance](https://stratospherelinuxips.readthedocs.io/en/develop/immune/research_rpi_llm_performance.html)
- llama.cpp is reportedly about 10–20% faster than Ollama on a Pi 5. [search-snippet only; Medium blog] — [Ollama vs llama.cpp on Pi 5](https://medium.com/@omkar121212/ollama-vs-llama-cpp-on-raspberry-pi-5-8e7fbeb310de)
- Raspberry Pi AI HAT+ 2 (Hailo-10H, 40 TOPS INT4, 8 GB on-board RAM): independent testing found "low single digits to around 8 tokens per second", and "in several cases the Pi 5 CPU can run the same small models faster" when it uses all cores. Supported models at launch were Llama 3.2 1B, Qwen2/2.5 1.5B, and DeepSeek-R1-Distill 1.5B, as INT4 Hailo builds. Article dated 2026-01-15. [verified] — [Hardware Corner](https://www.hardware-corner.net/local-llms-raspberry-pi-ai-hat-plus-2/). This contradicts a third-party claim of about 30–50 tokens/s for Llama 3.2 1B [search-snippet only] — [raspberry.tips](https://raspberry.tips/en/raspberrypi-tutorials/raspberry-pi-ai-hat-2-hailo-10h-40-tops-llm)
- Jetson Orin Nano 8GB, original → Super mode (JetPack 6.2, INT4, MLC), tokens/s: Llama 3.2 3B 27.7 → 43.1; Qwen 2.5 7B 14.2 → 21.8; Llama 3.1 8B 14.0 → 19.1; Phi-3.5 3.8B 24.7 → 38.1; Gemma 2 2B 21.5 → 35.0; SmolLM2 1.7B 41.0 → 64.5; Gemma 2 9B 7.2 → 9.2. Orin NX 16GB Super: Qwen 2.5 7B 23.5; Llama 3.2 3B 45.8. NVIDIA blog, 2025-01-16. NVIDIA notes that throttling affects results, and some table headers are mislabeled. [verified] — [NVIDIA JetPack 6.2 Super Mode blog](https://developer.nvidia.com/blog/nvidia-jetpack-6-2-brings-super-mode-to-nvidia-jetson-orin-nano-and-jetson-orin-nx-modules)
- VLMs on the Orin Nano 8GB, original → Super, tokens/s: PaliGemma2 3B (FP4, HF Transformers) 13.7 → 21.6; SmolVLM 2B 8.1 → 12.9; InternVL2.5 4B 2.5 → 5.1; Qwen2-VL 2B 2.8 → 4.4; VILA 1.5 3B (INT4, MLC) 0.7 → 1.1; LLaVA 1.6 7B 0.4 → 0.6. [verified] — [NVIDIA JetPack 6.2 blog](https://developer.nvidia.com/blog/nvidia-jetpack-6-2-brings-super-mode-to-nvidia-jetson-orin-nano-and-jetson-orin-nx-modules)
- A user on the NVIDIA forum measured 19.23 tokens/s for Qwen2.5 7B against the 21.75 published figure. NVIDIA replied that the published number requires Super mode. [search-snippet only] — [NVIDIA forum](https://forums.developer.nvidia.com/t/jetson-orin-nano-super-performance-test-issue/331700)
- A pre-Super Jetson AI Lab SLM tutorial lists Llama-3.2-1B at 54.8 tokens/s and Llama-3.2-3B at 27.7 tokens/s on the Orin Nano (MLC). [search-snippet only] — [Jetson AI Lab SLM tutorial](https://jetson-ai-lab.com/tutorial_slm.html)

### Inferences
- From the Pi 5 numbers, a tool call of about 40 output tokens takes roughly 4 s on a 1B model or roughly 8 s on a 3B model, plus prompt processing (not measured in this source, and usually the larger cost for long tool schemas). With Nav2 + SLAM already using about 1.5 cores, on-Pi LLMs fit only as a degraded-mode fallback, not as the main loop.
- The Hailo-10H HAT is not a good investment for robot LLM speed, based on current independent evidence. Its 8 GB of separate RAM may still help by keeping LLM memory off the Pi's RAM (inference, not measured).
- Qwen 2.5 7B on an Orin Nano Super (21.8 tokens/s) is in the same range as a mid-range laptop GPU running Ollama. So a Jetson is a viable on-robot replacement for the laptop, but only on a larger chassis than the Pi.

### Gaps
- I did not verify laptop and consumer GPU tokens/s for Ollama with Qwen2.5-7B Q4 (for example RTX 3060/4060/4090). There is no authoritative benchmark page.
- Pi 5 prompt-processing (prefill) speed for long tool schemas: none of the verified sources reported it.
- I did not verify Jetson AGX Orin or Jetson Thor figures. The Jetson AI Lab benchmarks page itself was not opened.
- No verified Pi 5 measurements of VLMs (Moondream, SmolVLM) were found.

## 3. VLAs and small VLMs on edge robots, and on-device speech latency

### Takeaway
SmolVLA (450M parameters) beats OpenVLA (7B) and π0 (3.3B) on LIBERO and Meta-World. Its asynchronous inference roughly doubles task throughput, so a small VLA running on a laptop GPU (or as an off-board policy server) is now practical. Edge VLMs give sub-second responses only at about 2B parameters, and at a cost in accuracy. Whisper on the Pi 5 is workable at tiny/base sizes, but Pi-specific benchmarks are poor.

### Cited Findings
- SmolVLA has about 450M parameters, about 100M of them in the action expert. It is described as able to "run on CPU, train on a single consumer GPU, or even a MacBook". Blog dated 2025-06-03. [verified] — [HF SmolVLA blog](https://huggingface.co/blog/smolvla)
- LIBERO average success: SmolVLA 0.45B 87.3%; SmolVLA 2.25B 88.75%; π0 3.3B 86.0%; OpenVLA 7B 76.5%. Meta-World: SmolVLA 0.45B 57.3%; π0 47.9%. SmolVLA reportedly uses about 6× less memory than π0. The paper names no inference hardware and gives no per-inference latency in ms. [verified] — [SmolVLA paper, arXiv 2506.01844](https://arxiv.org/html/2506.01844)
- Asynchronous inference (perception and action prediction decoupled from execution, using action chunks): SO100 pick-place completes in 9.70 s async vs 13.75 s sync (about 30% faster), and 19 vs 9 cubes are moved in a fixed time window. Success: sync 78.3% vs async 73.3%, according to the paper. The blog describes success as "similar (≈78%)", so the paper and blog differ slightly. [verified] — [arXiv 2506.01844](https://arxiv.org/html/2506.01844); [HF blog](https://huggingface.co/blog/smolvla)
- Edge VLMs for humanoid perception (Unitree G1, ORAN/MEC edge, WebRTC): LLaMA-3.2-11B-Vision at the edge keeps near-cloud accuracy and cuts end-to-end latency by about 5%. Qwen2-VL-2B gives "sub-second responsiveness" and cuts latency by "more than half", but loses accuracy. The abstract gives no absolute ms figures and does not name the edge hardware. Ahmad, Hafeez, Zaidi, 2026-01-21. [verified, abstract only] — [arXiv 2601.14921](https://arxiv.org/abs/2601.14921v1)
- Whisper on the Pi 5: faster-whisper with Whisper Tiny reportedly transcribes 10 s of audio in about 2–3 s (8 GB Pi 5), versus about 6 s for the original Python Whisper. [search-snippet only; vendor guide] — [fast.io guide](https://fast.io/resources/openclaw-raspberry-pi-speech-recognition-offline-voice-agent/). Sources disagree on whether whisper.cpp or faster-whisper is faster on the Pi [search-snippet only] — [GoTranscript](https://gotranscript.com/public/enhance-raspberry-pi-5-with-whisper-for-live-transcription)
- Whisper on Hailo-8L with a Pi exists as a community project. [search-snippet only] — [Hailo community](https://community.hailo.ai/t/real-time-asr-on-raspberry-pi-hailo8l-with-whisper/17936)

### Inferences
- For a Pi-based mobile robot, a VLA would run off-board (laptop GPU as the policy server), using async chunked execution to absorb network latency. SmolVLA's async design maps directly onto a robot–laptop split.
- Whisper small.en on a Pi 5 probably would not reach the user's current ~1 s voice-to-action, given that tiny takes about 2–3 s per 10 s clip. STT should stay on the laptop, with tiny/base on the Pi as a fallback (inference from unverified numbers).

### Gaps
- No verified latency data for Moondream 2, OpenVLA-quantized, or TinyVLA on Jetson or the Pi.
- No primary benchmark of whisper.cpp or faster-whisper on the Pi 5 for small.en. Benchmark it locally.
- SmolVLA inference ms per chunk on a specific GPU is not reported in the paper's main text.

## 4. Edge–cloud and robot–laptop split architectures: what runs where, latency and robustness, fallback when the link drops

### Takeaway
Recent work (2026) pushes cloud/off-board models to send higher-level, delay-tolerant outputs (task representations, waypoint buffers) while closed-loop control and visual feedback stay on the robot. However, sustained disconnection is still explicitly an open problem, and authors call for a local fallback policy.

### Cited Findings
- A latency-tolerant cloud–edge VLA sends task-level representations from the cloud and keeps visual feedback on the edge. The authors say robustness was shown only for the delay distributions they tested, and that timestamped features plus a local fallback policy are still needed for prolonged disconnection. [search-snippet only] — [arXiv 2608.00569](https://arxiv.org/pdf/2608.00569)
- Speculative Policy Orchestration (2026-03): a cloud world model streams future waypoints into an edge buffer, decoupling control rate from network round-trip time, with an ε-tube verifier bounding execution error. [search-snippet only] — [arXiv 2603.19418 (via Emergent Mind)](https://www.emergentmind.com/papers/2603.19418)
- In the Unitree G1 edge-vs-cloud VLM study, edge deployment cut end-to-end latency by about 5% at 11B and by more than half with a 2B model. [verified, abstract] — [arXiv 2601.14921](https://arxiv.org/abs/2601.14921v1)
- Earlier foundational work learns when to offload robot perception using deep RL, given wireless congestion and loss. [search-snippet only] — [Chinchali et al., arXiv 1902.05703](https://arxiv.org/pdf/1902.05703)
- SmolVLA's asynchronous inference stack supports a remote policy server, so execution keeps running from the action queue while the next chunk is computed. [verified] — [arXiv 2506.01844](https://arxiv.org/html/2506.01844)

### Inferences
- A sensible split for the user's setup: the Pi runs Nav2, SLAM, motor control, safety stops, and a small rule-based or 1B-model fallback (for example "stop", "return to dock"). The laptop runs Qwen-7B-class planning and tool calling plus faster-whisper. Tool calls should be idempotent, time-stamped goals (Nav2 actions) rather than streamed velocity commands, so that link loss degrades to "finish or cancel the current goal" instead of losing control.

### Gaps
- No verified study measured LLM-agent robot behaviour under Wi-Fi packet loss or outages with concrete numbers. Both of the 2026 papers above say this is unsolved.
- No measured comparison of robot–laptop (LAN) vs robot–cloud round-trip time for LLM tool calls was found.

## 5. Grammar-constrained decoding, structured output, and fine-tuning small models on robot tool schemas

### Takeaway
Constrained decoding (GBNF, JSON schema, XGrammar) reliably removes malformed calls, and its serving overhead is now near zero. But for sub-3B models, hard schema constraints can lower semantic correctness: valid but wrong calls. Fine-tuning for tool use (xLAM, ToolACE, Hammer, and RL as in Tool-N1) gives the larger accuracy gains.

### Cited Findings
- "The Constraint Tax" (J. Ray, 2026-05-20) tested Qwen2.5-0.5B, Qwen2.5-1.5B, and SmolLM2-1.7B over 15,000 generations. Hard answer-only schema decoding raised schema validity from 61.5% to 100.0% but lowered answer accuracy from 19.7% to 11.0%. The wrong-but-schema-valid rate went from 49.5% to 88.9%. [verified, abstract] — [arXiv 2605.26128](https://arxiv.org/abs/2605.26128)
- On a calendar tool-call task, Qwen2.5-1.5B scored 91.5% executable accuracy with prompt-only JSON and 48.0% with a hard tool-call schema, even though both were 100% schema-valid. The recommendation is to "reason free, constrain late" and to report validity, accuracy, executable accuracy, and wrong-valid rate separately. A direct-schema tax persists even at the 3B boundary. [verified, abstract] — [arXiv 2605.26128](https://arxiv.org/abs/2605.26128)
- XGrammar-2 (2026-01-07, revised 2026-08-05) is a structured-generation engine for agentic LLMs with "near-zero end-to-end overhead" and more than 6× faster grammar compilation than prior engines. [verified, abstract] — [arXiv 2601.04426](https://arxiv.org/abs/2601.04426). A search snippet claimed that XGrammar-2 lets Llama-3.2-3B beat unconstrained Llama-3.1-70B on BFCL. This was not confirmed in the abstract and is unverified.
- "Repair, Not Improvement" argues that constraints help small models in tool-call abstention mainly by repairing malformed output, not by improving the decision itself. [search-snippet only] — [arXiv 2608.13959](https://arxiv.org/pdf/2608.13959)
- JSONSchemaBench evaluates constrained-decoding frameworks on about 10K real-world JSON schemas. [search-snippet only] — [arXiv 2501.10868](https://arxiv.org/abs/2501.10868v2)
- Fine-tuning and RL: Tool-N1-7B (Qwen2.5-7B with rule-based RL) raises the BFCL average from 76.95 (base instruct) to 84.82, above GPT-4o's 83.97. [verified] — [arXiv 2505.00024v2](https://arxiv.org/html/2505.00024v2). The xLAM-2 models trained on APIGen-MT multi-turn synthetic data lead small models on BFCL v3 multi-turn. [verified] — [arXiv 2504.03601](https://arxiv.org/html/2504.03601v4)

### Inferences
- For a 7B model on a laptop, enforcing the tool-call JSON with Ollama's `format`/JSON schema or llama.cpp GBNF is low-risk and removes parse failures. For 0.5–1.7B fallback models on the Pi, prefer letting the model choose the tool freely (or with a short reasoning step) and then validating or repairing, rather than imposing a hard schema from the first token.
- Fine-tuning a small model (LoRA on Qwen2.5/Qwen3 1.5–7B) on the robot's own fixed tool schema plus synthetic multi-turn dialogs (the APIGen-MT style) is the method best supported by evidence for raising accuracy. The literature has no robot-specific numbers for this yet.

### Gaps
- No verified paper reports fine-tuning a small LM specifically on ROS 2 / Nav2 tool schemas with measured accuracy.
- Ollama's structured-output accuracy effect for Qwen2.5-7B specifically was not measured in any source found.
