# LLM Agents Controlling Robots via ROS / ROS 2 Tool Calling (2024–2026)

Verification legend: **[V]** = I opened the arXiv abstract/HTML page or the GitHub repo/source in this session and confirmed the title, authors and date. **[S]** = seen only in a search-result snippet, not opened (treat as unverified). Background work from before 2024 is marked **BACKGROUND**.

## Q1. Which systems exist, how do they work, and how are they classified?

### Takeaway
By 2026 the field has settled on a few patterns. One is LangChain-style tool-calling agents over ROS introspection tools (NASA JPL ROSA). Another maps LLM output to atomic ROS actions, services or behavior trees (ROS-LLM). The newest is protocol bridges (MCP servers over rosbridge, and the OpenClaw-based ROSClaw) that expose topics, services and actions to any client LLM. The main taxonomy (Salimpour et al., arXiv:2508.05294) sorts these into Protocol, Interface, Orchestration and Embedded integration. It places ROSA under "Interface" and ROS-LLM and the ROS-MCP servers under "Protocol".

### Cited Findings
**Surveys and taxonomy**
- [V] Salimpour, Fu, Rachwał, Bertrand, O'Sullivan, Jakob, Keramat, Militano, Toffetti, Edelman, Peña Queralta, "Towards Embodied Agentic AI: Review and Classification of LLM- and VLM-Driven Robot Autonomy and Interaction", arXiv:2508.05294, v1 7 Aug 2025, v4 12 Nov 2025, cs.RO. No journal or conference is listed. The paper proposes "a taxonomy for classifying model integration approaches" and analyses agent roles as "coordinators, planners, perception actors, or generalist interfaces" — [arXiv abs](https://arxiv.org/abs/2508.05294)
- [V] It defines four integration categories (Sec. III). **Protocol Integration**: the LLM translates user input into predefined tools or commands, e.g. MCP servers and ROS CLI bindings, with Code-as-Policies discussed here. **Interface Integration**: tool outputs affect later model actions, or the focus is HRI and user interaction (OpenMind cited as the most complete open-source example). **Orchestration-Oriented Integration**: the model manages resources, subsystems or multiple agents. **Embedded/Direct Integration**: the model produces actions end-to-end or serves as a subsystem such as perception — [arXiv HTML v4](https://arxiv.org/html/2508.05294v4)
- [V] It defines six agent roles (Sec. IV): Planner (SayCan, SELP, ConceptAgent), Orchestration (AutoRT, LABOR Agent, Smart-LLM), Task-Specific (LGX, NavGPT, ARNA, BUMBLE), Model-Centric (LEO, RoboCat, RoboAgent), Generalist (Voyager, CaP, ODYSSEY, RoboGPT), and Generalist Systemic, meaning reusable frameworks with separate perception, reasoning and action modules (ROSA, RAI) — [arXiv HTML v4](https://arxiv.org/html/2508.05294v4)
- [V] Table II classifies these systems. Protocol: CaP, ros2ai, ROS-LLM, ROS-MCP servers (ros-mcp-server, robotmcp), explainable ros, llama ros. Protocol/Interface: ROScribe, ChatGPT for Robotics. Interface: ROSA, RAI, Embedded Agents, BUMBLE. Interface/Framework: OpenMind OM1. Orchestration: AutoRT, Stretch AI. Embedded: Gemini Robotics, MoManip VLA, ARNA. Framework: UROSA — [arXiv HTML v4](https://arxiv.org/html/2508.05294v4)
- [V] The survey is internally inconsistent. ROSA is "Interface" in Table II but "Generalist Systemic" in Sec. IV-6, and ARNA is "Embedded" in the table but "task-specific" in the text. The category is also named "Protocol Integration" in the text but "Protocol-Focused Integration" in Table I — [arXiv HTML v4](https://arxiv.org/html/2508.05294v4)
- [V] ROSGPT and OpenClaw do not appear in that survey's text (checked in the first ~100k characters of the HTML) — [arXiv HTML v4](https://arxiv.org/html/2508.05294v4)

**NASA JPL ROSA**
- [V] Royce, Kaufmann, Becktor, Moon, Carpenter, Pak, Towler, Thakker, Khattak, "Enabling Novel Mission Operations and Interactions with ROSA: The Robot Operating System Agent", arXiv:2410.06472, v1 9 Oct 2024, v2 13 Feb 2025. The comments field says it was accepted at IEEE Aerospace Conference 2025. ROSA uses "well-defined tools" to interface with ROS1/ROS2. Safety comes from "parameter validation and constraint enforcement", with ethics framed around Asimov's Three Laws. The evaluation consists of mock-up operations in JPL's Mars Yard, a lab, and a simulation with three robots, with no quantitative results in the abstract — [arXiv abs](https://arxiv.org/abs/2410.06472)
- [V] ROSA is built on LangChain and installed with `pip3 install jpl-rosa`. It requires Python 3.9+ and ROS Noetic or newer, and the demos are TurtleSim (Docker), NeBula-Spot in the Mars Yard, and IsaacSim via the ROS bridge — [GitHub nasa-jpl/rosa](https://github.com/nasa-jpl/rosa)
- [V] In the source code, the agent is built with LangChain `create_tool_calling_agent` and run by `AgentExecutor(handle_parsing_errors=True)`. The constructor takes `ros_version`, `llm` (tested with ChatOpenAI, AzureChatOpenAI, ChatAnthropic and ChatOllama), `tools`, `tool_packages`, `prompts` (a RobotSystemPrompts object appended to the default prompts), `blacklist` ("A list of ROS tools to exclude from the agent", passed to `ROSATools(...)` and `add_packages(...)`), `accumulate_chat_history=True`, `streaming=True`, `max_iterations=100`, and `return_intermediate_steps=False` — [rosa.py source](https://raw.githubusercontent.com/nasa-jpl/rosa/main/src/rosa/rosa.py)
- [V] Custom tools are LangChain `@tool` functions, and their docstrings (e.g. "Move the robot forward by the specified distance", plus `:param distance:`) become the tool description. They are passed through `tools` or `tool_packages`. The `RobotSystemPrompts` example sets `embodiment_and_persona` — [ROSA wiki: Custom Agents](https://github.com/nasa-jpl/rosa/wiki/Custom-Agents)
- [V] The Salimpour survey describes ROSA's safety as parameter validation, constraint enforcement and optional human approval for critical actions. It names tight coupling to ROS middleware as a limitation — [arXiv HTML v4](https://arxiv.org/html/2508.05294v4)

**ROS-LLM (Mower et al., Huawei Noah's Ark)**
- [V] Mower, Gonzalez-Billandon, Zimmer, ... Hutter, ... Peters, ... Wang, Bou-Ammar, "ROS-LLM: A ROS framework for embodied AI with task feedback and structured reasoning", arXiv:2406.19741 (v3 12 Jul 2024). No peer-reviewed venue is named on the page — [arXiv HTML v3](https://arxiv.org/html/2406.19741v3)
- [V] The LLM emits one of three output formats, and a regex extracts the code block. (a) Python, run in a terminal with ROS access. (b) A JSON action sequence, where each step calls a ROS service of type `rosllm_srvs/AtomicAction` (input, prev_output → output) and the steps run in order. (c) XML interpreted as a behavior tree, which was "not yet evaluated experimentally". Each atomic action in the library has a `name`, a `type` (ROS action, service, or code) and a textual `description`. An `observation_manager` package turns sensor readings into text. New atomic actions can be added through DMP imitation learning — [arXiv HTML v3](https://arxiv.org/html/2406.19741v3)
- [V] Evaluation used DeepSeek 7B Coder served by vLLM in Europe, controlling a UR5 with a Robotiq 2F-85 under ROS Noetic in Asia. There were 35 tabletop tasks (2–8 boxes), and success with and without human feedback appears only in Fig. 7, with no exact numbers in the text. In remote supervision, 7 participants averaged 6:09 and 9:00 (min:sec) on two tasks, with 2–3 s network lag. A coffee-making task is reported only qualitatively. The abstract mentions many LLMs, but no multi-LLM comparison appears in the text — [arXiv HTML v3](https://arxiv.org/html/2406.19741v3)

**ROSGPT (Koubaa)**
- [S] **BACKGROUND (2023).** ROSGPT is a ROS 2 package that uses prompt engineering and an ontology to turn free-form commands into structured JSON. A REST-server node sends the text to ChatGPT and publishes the result to `/voice_cmd`, where parser nodes for Turtlesim and TurtleBot3 navigation convert it. The preprint is preprints.org 202304.0827. Search snippets say a later version appeared in *Software: Practice and Experience* (2024) as "Next-Generation Human-Robot Interaction with ChatGPT and Robot Operating System". I did not open the preprint or the journal page — [preprints.org](https://www.preprints.org/manuscript/202304.0827); [GitHub README](https://raw.githubusercontent.com/aniskoubaa/rosgpt/main/README.md)

**MCP servers for ROS**
- [V] robotmcp/ros-mcp-server is a bridge that lets LLMs "publish & subscribe to topics, call services & actions, set parameters, read sensor data, and monitor robot state". It needs only the rosbridge node added, with no robot code changes, and supports ROS 2 (Jazzy, Humble) and ROS 1. Supported clients are Claude Code, Codex CLI, Gemini CLI, Claude Desktop, ChatGPT, Cursor and any MCP client. The repo had about 1.5k stars and 215 forks when I fetched it. The README lists "Action support" and "Permissions" as features contributors could add, which suggests these are incomplete — [GitHub](https://github.com/robotmcp/ros-mcp-server)
- [S] Listing sites mention a v3.1.0 release dated 2026-06-17, but the GitHub Releases section was empty in my fetch, so this is unverified — [glama listing](https://glama.ai/mcp/servers/robotmcp/ros-mcp-server)
- [V] Fu, Salimpour, Militano, Edelman, Peña Queralta, Toffetti, "ROSBag MCP Server: Analyzing Robot Data with LLMs for Agentic Embodied AI Applications", arXiv:2511.03497 (5 Nov 2025). It is an MCP server over ROS/ROS 2 bags, with tools for trajectories, laser scans, transforms, time series, `ros2 bag list/info`, topic and time filtering, and a benchmarking UI. It benchmarks eight LLMs/VLMs. The abstract says tool-calling success depends on the number of tools, the tool description schema and the number of arguments — [arXiv abs](https://arxiv.org/abs/2511.03497)

**OpenClaw / ROSClaw**
- [V] Cardenas, Arnett, Yeo, Sah, Kim, "ROSClaw: An OpenClaw ROS 2 Framework for Agentic Robot Control and Interaction", arXiv:2603.26997 (27 Mar 2026). It is a "model-agnostic executive layer" between the OpenClaw agent runtime and ROS 2. Its components are dynamic capability discovery with standardized affordance injection, multimodal observation normalization, **pre-execution action validation within a configurable safety envelope**, and structured audit logging. It was deployed on wheeled, quadruped and humanoid robots with four model backends — [arXiv abs](https://arxiv.org/abs/2603.26997)
- [S] Another paper also called "ROSClaw" (Apr 2026) covers multi-robot orchestration, and the names should not be confused. There is also an open-source RosClaw plugin on GitCode that uses rosbridge over WebSocket, plus Intel's "OpenClaw + AgenticROS" demo with a local VLM controlling a simulated JAKA arm in Gazebo (ROS 2 Jazzy, Ubuntu 24.04) — [emergentmind topic](https://www.emergentmind.com/topics/rosclaw); [GitCode README](https://gitcode.com/ib_robot/rosclaw/blob/main/README.md); [Intel docs](https://docs.openedgeplatform.intel.com/dev/edge-ai-suites/robotics-ai-suite/embodied/sample_pipelines/openclaw_agenticros_demo.html)

**RAI (Robotec.AI)**
- [S] Rachwał et al., "RAI: Flexible Agent Framework for Embodied AI", arXiv:2505.07532. It is built on three abstractions, Agents, Connectors and Tools, and its Connectors support ROS 2 pub/sub, services and actions. It was validated on a physical Husarion ROSbot XL with a digital twin, plus manipulator and tractor simulations. I saw the PDF link in search results but did not open the abstract page — [arXiv PDF](https://arxiv.org/pdf/2505.07532)
- [V] The Salimpour survey notes that RAI has safety-monitor agents, but also limited spatial reasoning and unreliable self-correction — [arXiv HTML v4](https://arxiv.org/html/2508.05294v4)

**Background (pre-2024; IDs from memory, not opened this session)**
- [S] **BACKGROUND:** SayCan (arXiv:2204.01691), Code as Policies (arXiv:2209.07753) and "ChatGPT for Robotics" (Vemprala et al., arXiv:2306.17582) are classified in the Salimpour survey (CaP under Protocol, ChatGPT for Robotics under Protocol/Interface, SayCan as a Planner agent). I did not open the arXiv IDs listed here this session — [Salimpour survey](https://arxiv.org/html/2508.05294v4)

### Inferences
- ROSA is the most mature "agent library" option: a LangChain tool-calling agent with a blacklist (a deny-list, not an allow-list). It ships a built-in set of ROS introspection tools that a deployment has to restrict or replace. The user's 9-tool fleet setup is effectively an allow-list built on top of ROSA's deny-list model.
- MCP bridges such as ros-mcp-server optimise for generality (any topic or service through rosbridge) and, per their README, do not yet have mature permissions or action support. The safety burden therefore falls on the robot side or on an executive layer like ROSClaw's.

### Gaps
- I found no primary paper or official doc for a dedicated "LangChain/LangGraph robot agent" framework apart from ROSA (LangChain) and RAI. No LangGraph-specific ROS system was verified.
- I did not open the separate robotmcp project (the survey names "robotmcp" separately from ros-mcp-server) or other ROS 2 MCP servers.
- I could not see ROSGPT's journal version or its ontology details.

## Q2. How are tools defined and restricted, how are long-running actions exposed, and how is feedback returned?

### Takeaway
Tools are almost always natural-language-described functions: LangChain `@tool` docstrings in ROSA, name/type/description JSON entries in ROS-LLM, and MCP tool schemas. Restriction usually means a deny-list (ROSA `blacklist`), parameter validation, or a pre-execution validator ("safety envelope" in ROSClaw). Long-running ROS actions are poorly documented in agent frameworks. ROS-LLM wraps them as blocking atomic services, and ros-mcp-server lists action support as a feature still to add.

### Cited Findings
- [V] ROSA: tools are LangChain `@tool` functions whose docstrings serve as the schema description, and a `blacklist` excludes named ROS tools — [rosa.py](https://raw.githubusercontent.com/nasa-jpl/rosa/main/src/rosa/rosa.py); [wiki](https://github.com/nasa-jpl/rosa/wiki/Custom-Agents)
- [V] ROSA caps the reasoning loop at `max_iterations=100` by default, and `handle_parsing_errors=True` means malformed tool calls are fed back to the model instead of raising errors — [rosa.py](https://raw.githubusercontent.com/nasa-jpl/rosa/main/src/rosa/rosa.py)
- [V] ROS-LLM executes each step as a `rosllm_srvs/AtomicAction` service call, passing the previous step's output forward, so a step is a blocking call that returns an output string. Environment feedback is a failure flag, hard-coded for some actions (e.g. zero gripper width means a failed grasp). Human corrective feedback comes through the chat after each execution — [arXiv HTML v3](https://arxiv.org/html/2406.19741v3)
- [V] Butter-Bench (TurtleBot 4, ROS 2 Jazzy) exposes high-level tools: drive(distance), rotate(angle), wait, dock, undock, status, take_photo, save_photo, view_map, navigate_to(coordinates), read_msg, and send_msg/reply_message over Slack. It runs in a ReAct loop where each movement returns images and an annotated SLAM map, so results come back to the model as multimodal observations. There is a 4 m per-move limit on the planning task — [arXiv HTML](https://arxiv.org/html/2510.21860v1)
- [V] ROSClaw does "pre-execution action validation within a configurable safety envelope". Its tool schemas, safety enforcement and provenance logging stay fixed while the model is swapped — [arXiv abs](https://arxiv.org/abs/2603.26997)
- [V] Salimpour et al. argue that clear tool descriptions affect task success regardless of the model's tool-use ability. They also say long-horizon tasks with variable execution times need progress monitoring and recovery, and that a 10 Hz video feed can outpace LLM processing and cause desynchronization — [arXiv HTML v4](https://arxiv.org/html/2508.05294v4)
- [V] The ROSBag MCP paper reports that tool-calling success depends on the number of tools, the description schema and the argument count — [arXiv abs](https://arxiv.org/abs/2511.03497)
- [S] Search-engine summary of the ROSBag MCP paper: having more tools in total "inversely correlated with success rates when tools overlapped", and Kimi K2 and Claude Sonnet 4 were clearly best. I did not see this sentence on the abstract page itself — [alphaxiv](https://www.alphaxiv.org/abs/2511.03497)

### Inferences
- These sources describe no standard pattern for exposing Nav2 NavigateToPose to an agent (e.g. non-blocking send_goal plus get_status/cancel tools versus a blocking call). Butter-Bench's `navigate_to` and ROS-LLM's blocking atomic services suggest most systems hide the action behind one blocking tool that returns a final result.
- The ROSBag MCP finding about tool count and argument count supports a small, non-overlapping tool set with few arguments for small local models like a 7B Qwen.

### Gaps
- I found no primary source on how ROSA's built-in tools handle ROS 2 actions (goals, feedback, cancel), and ROSClaw's Nav2 handling is not in its abstract.
- I found no published comparison of allow-list versus deny-list tool restriction.

## Q3. How are these agents evaluated? Are there benchmarks for robot tool calling?

### Takeaway
Evaluation is still mostly bespoke: qualitative demos (ROSA), task success with or without human feedback on a real arm (ROS-LLM), and user studies with completion time and NASA-TLX. The most concrete ROS 2 LLM-agent benchmark is Butter-Bench (real TurtleBot 4, ROS 2 Jazzy), where the best LLM scored 40% against 95% for humans. Tool-calling-specific benchmarking exists for ROSBag MCP, and ROSClaw compares out-of-policy action rates across models.

### Cited Findings
- [V] Butter-Bench (Sharrock, Petersson, Petersson, Backlund, Wennström, Nordström, Aronsson; arXiv:2510.21860, 23 Oct 2025). Average completion rates: Gemini 2.5 Pro 40%, Claude Opus 4.1 37%, GPT-5 30%, Gemini Robotics ER 1.5 27%, Grok 4 23%, Llama 4 Maverick 7%. The human baseline is 95% (three operators). Models fine-tuned for embodied reasoning did not score higher. Tasks: search for package, infer butter bag, notice absence, wait for confirmed pickup, multi-step spatial path planning, and end-to-end "pass the butter" (15-minute limit) — [arXiv abs](https://arxiv.org/abs/2510.21860); [HTML](https://arxiv.org/html/2510.21860v1)
- [V] ROSClaw: out-of-policy action proposal rates varied up to 4.8x across models, and 3.4x among frontier models alone. Identical commands produced "qualitatively distinct physical behaviors". A cross-framework parity comparison against ROSA suggests that executive-layer design, not just prompt wording, significantly affects task completion and safety behavior — [arXiv abs](https://arxiv.org/abs/2603.26997)
- [V] ROSBag MCP Server benchmarks tool-calling success for eight LLMs/VLMs (Anthropic, OpenAI, and open models via Groq) and includes a benchmarking UI. The abstract gives no numbers — [arXiv abs](https://arxiv.org/abs/2511.03497)
- [V] ROS-LLM: 35 tabletop tasks on a real UR5, with success with and without feedback shown in a figure, and a 7-person remote-supervision study (completion times 6:09 and 9:00, NASA-TLX) — [arXiv HTML v3](https://arxiv.org/html/2406.19741v3)
- [V] ROSA's evaluation is mock-up operations in the Mars Yard, a lab and simulation, with no quantitative results in the abstract — [arXiv abs](https://arxiv.org/abs/2410.06472)
- [V] Salimpour et al. propose metrics along Perceive–Reason–Act: success rate, completion time, level of autonomy, adaptability, and memory consistency and recallability. They warn that goal completion alone misses inefficient motion — [arXiv HTML v4](https://arxiv.org/html/2508.05294v4)
- [S] Unverified 2026 items from search snippets only: "RHO: Your Coding Agent is Secretly a Roboticist" (arXiv:2606.16458) evaluates RAI on an O3DE manipulation benchmark (ROS 2 + MoveIt), and "ALRM: Agentic LLM for Robotic Manipulation" (arXiv:2601.19510) is a benchmark for multistep manipulation using tool calling and code generation — [RHO](https://arxiv.org/html/2606.16458v1); [ALRM](https://arxiv.org/pdf/2601.19510)

### Inferences
- No widely adopted, standardised "robot tool-calling accuracy" benchmark (in the style of BFCL or τ-bench for ROS) was found. Butter-Bench and ROSClaw's out-of-policy rate are the closest real-robot measures. A fleet agent could be scored on success rate, tool-call validity and refusal correctness.

### Gaps
- I could not verify a benchmark named `rai_bench` from a primary page.
- Per-model numbers for ROSBag MCP and ROSClaw were not on the abstract pages, and I did not read the full papers.
- I found no latency-per-tool-call measurements for the ROS agents above.

## Q4. Voice and speech front ends (Whisper + LLM) for robots: latency and error results

### Takeaway
Whisper is the usual speech-to-text (STT) front end. Clean voice-to-action latency and WER benchmarks for ROS 2 pipelines are scarce. The verified data points are a ChatGPT–ROS 2 latency-reduction paper (simulation only, relative numbers) and a 2026 security study showing that Whisper and other sensor channels are prompt-injection vectors for LLM-controlled ROS 2 robots.

### Cited Findings
- [V] Pollini, Guterres, Guerra, Grando, "Reducing Latency in LLM-Based Natural Language Commands Processing for Robot Navigation", arXiv:2506.00075 (29 May 2025), accepted to IEEE INDIN. It integrates ChatGPT and ROS 2 for text and voice commands without a middleware transport platform. It reports a **7.01% average reduction in communication latency**, gives no absolute figures in the abstract, and was tested in Gazebo simulation only — [arXiv abs](https://arxiv.org/abs/2506.00075)
- [V] Dorzhiev, "RIPA: Sensory-Vector Prompt Injection Attacks on LLM-Controlled ROS 2 Robots", arXiv:2606.28649 (26 Jun 2026, cs.CR). The pipeline is Whisper STT, OCR and LiDAR-derived state fed to an LLM. Five LLMs (about 4B to 284B parameters) were tested, with 100 runs per variant. Llama-3.3-70B had 100% attack success rate (ASR) across all variants, while Llama-3-8B and **Qwen 2.5-7B-Instruct had 0% ASR on direct-override injection**. Gemma-3n-E4B matched the 70B model's vulnerability, and the authors conclude that "robustness is model-specific rather than scale-dependent". LiDAR context poisoning reached 100% ASR on DeepSeek-V4-Flash. A hybrid semantic firewall blocked known patterns (0% ASR, 0/20 false positives) but was bypassed in 10.2% of obfuscated trials (58/570) — [arXiv abs](https://arxiv.org/abs/2606.28649)
- [S] A search summary of the RIPA full text says Whisper WER on injected commands was 91.7%, yet the LLM still extracted the intended meaning in 29 of 30 runs. It also says pipeline latency occasionally exceeded an 8 s timeout under API load. This is not on the abstract page and is unverified — [arXiv PDF](https://arxiv.org/pdf/2606.28649)
- [S] **BACKGROUND/2024, not ROS:** "Does ChatGPT and Whisper Make Humanoid Robots More Relatable?" (arXiv:2402.07095, Pepper robot). Per the snippet, Whisper had an average WER of 1.716% with 2.639 s processing time, better than the Google ASR options. Not opened — [arXiv](https://arxiv.org/abs/2402.07095v1)

### Inferences
- Any voice channel is an untrusted input path into tool calls, so a robot-side safety gate also defends against injected speech. RIPA's result that Qwen 2.5-7B resisted direct-override injection applies to that model only and does not carry over to obfuscated attacks.

### Gaps
- I found no verified 2024–2026 paper that reports end-to-end Whisper → LLM → ROS 2 action latency together with WER on normal (non-adversarial) commands, on-device (e.g. faster-whisper on edge hardware) or in the cloud.

## Q5. Reported failure modes: hallucinated tools/parameters, wrong robot, over-eager action, silent repair of infeasible requests

### Takeaway
The reported failures include prompt sensitivity and acting on objects that appear only in prompt examples (ROS-LLM). Butter-Bench adds over-eager and premature actions, spatial-reasoning errors, unsafe motion (driving down stairs), excessive clarification, unjustified refusals, and leaking confidential information under stress. Across models, out-of-policy action proposals vary 4.8x (ROSClaw). I found no robot paper that names and measures the specific "silent rewrite of an infeasible mission" failure the user observed. The closest is general-LLM infeasibility-refusal work.

### Cited Findings
- [V] ROS-LLM: small wording changes ("the other cube" vs "another cube", adding "on top of") changed the output. The model sometimes acted on objects from illustrative prompt examples that were not in the scene, i.e. a hallucinated grounding drawn from few-shot examples. Ambiguous or typo-filled commands and duplicate command execution also occurred — [arXiv HTML v3](https://arxiv.org/html/2406.19741v3)
- [V] Butter-Bench:
  - **Over-eager action:** Grok 4 docked about 6 s after announcing delivery, before any confirmation, and barely used the `wait` tool. All models failed "Notice Absence".
  - **Spatial reasoning:** models chose straight-line waypoints that ignored walls.
  - **Unsafe motion:** a model driving to photograph stairs drove off the edge, and without being told it was wheeled, the agent tried to navigate down stairs.
  - **Clarification and refusal:** Gemini ER 1.5 asked excessive clarifying questions (three end-to-end failures), and Llama 4 Maverick refused tasks citing a lack of arms despite the system prompt.
  - **Leaking under stress:** under simulated low battery and a broken charger, Claude Opus 4.1 shared an image of a confidential document.
  - **"Doom spiral":** an early Claude Sonnet 3.5 run produced theatrical output when the dock malfunctioned.

  — [arXiv HTML](https://arxiv.org/html/2510.21860v1)
- [V] ROSClaw: out-of-policy action proposal rates differ up to 4.8x across models, and the same command yields different physical behaviors — [arXiv abs](https://arxiv.org/abs/2603.26997)
- [V] Salimpour survey: RAI has unreliable self-correction and limited spatial reasoning, and most agents rely on transient, session-bound memory — [arXiv HTML v4](https://arxiv.org/html/2508.05294v4)
- [S] "Recognizing Limits: Investigating Infeasibility in Large Language Models" (arXiv:2408.05873, listed as Findings of EMNLP 2025) builds a benchmark of feasible and infeasible tasks that tests whether LLMs decline infeasible ones. Its taxonomy includes "Physical Interaction". It is not robot-specific, and I saw it only in search results — [arXiv HTML v3](https://arxiv.org/html/2408.05873v3); [ACL Anthology](https://preview.aclanthology.org/new-sigs/2025.findings-emnlp.535/)
- [S] DELTA (ICRA 2025) uses scene graphs to improve the feasibility of LLM plans. It appears only in an ICRA program listing snippet and was not verified — [ICRA25 program](https://ras.papercept.net/conferences/conferences/ICRA25/program/ICRA25_ContentListWeb_3.html)

### Inferences
- The silent-repair behavior the user saw (a 7B model rewriting an impossible mission instead of refusing) fits the reported patterns of over-compliance and unreliable self-correction. It mirrors ROS-LLM's tendency to substitute objects from prompt examples. This is an inference: no robotics paper found here quantifies "silent mission rewriting".
- ROSClaw's model-dependent out-of-policy rates and Butter-Bench's mix of over-refusal (Llama 4) and over-eagerness (Grok 4) suggest that refusal behavior should be measured per model, not assumed. A robot-side validation layer (ROSClaw's safety envelope, ROSA's constraint enforcement) is the common mitigation.

### Gaps
- I found no verified source that specifically measures hallucinated tool names or parameters, or wrong-robot selection in multi-robot fleets, for ROS agents.
- I found no robot-specific benchmark for refusing infeasible commands in 2024–2026. The general-LLM work (arXiv:2408.05873) was seen only in snippets.
- I did not read the full texts of ROSClaw, ROSBag MCP or RAI, so their detailed failure analyses are not captured.
