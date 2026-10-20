# Safety, verification and guardrails for LLM/agentic control of physical robots (2024–2026)

Verification method: every arXiv ID below was checked against the arXiv API (export.arxiv.org) during this session. I checked title, date and abstract, and the venue where arXiv's comment or journal-ref field gives one. Three papers were also opened in full HTML: RoboGuard 2503.07885v2, RoboAbstention 2605.20544v1 and ASIMOV 2503.08663v1. Numbers marked "(abstract)" come only from the arXiv abstract. Venues marked "[venue unverified]" do not appear in arXiv metadata and were not checked anywhere else.

## Key works: what each one measured

### Takeaway
Two things hold across 2024–2026. Unguarded LLM planners execute harmful or hazardous plans most of the time: attack success is 82–100% under jailbreaks, and refusal of hazardous tasks is about 10% even without an attack. Formal or structured guards outside the planner cut this to low single digits; RoboGuard, for example, goes from 92.3% to 2.3%. Prompt-level and constitution-level fixes help, but they degrade under adversarial framing.

### Cited Findings
**Jailbreak / red-teaming**
- **RoboPAIR (Robey et al., "Jailbreaking LLM-Controlled Robots", arXiv 2410.13691, Oct 2024)** is described as the first jailbreak algorithm for LLM-controlled robots. It was tested in three settings: white-box on the NVIDIA Dolphins self-driving LLM, gray-box on a Clearpath Jackal with a GPT-4o planner, and black-box on the GPT-3.5-integrated Unitree Go2. It "often achiev[es] 100% attack success rates" on three new datasets of harmful robot actions (abstract). [ICRA 2025 venue unverified] — [arXiv 2410.13691](https://arxiv.org/abs/2410.13691)
- **BadRobot (arXiv 2407.20242, ICLR 2025)** attacks embodied LLMs through voice-style interaction using three vulnerabilities: (i) manipulating the LLM inside the robot system, (ii) misalignment between linguistic outputs and physical actions, and (iii) world-knowledge flaws that cause unintended hazards. It was evaluated against VoxPoser, Code as Policies and ProgPrompt on a benchmark of malicious physical-action queries (abstract). The venue is confirmed in the arXiv journal-ref. — [arXiv 2407.20242](https://arxiv.org/abs/2407.20242)
- **POEF, "Easier Said Than Done: Unpacking Intent-Behavior Gap in Jailbreaking LLM-Based Robots" (arXiv 2412.16633; arXiv comment says "Accepted by NDSS 2027")** finds that many jailbreaks yield malicious-looking policies ("intent jailbreaks") that do not produce harmful physical actions ("behavior jailbreaks"). The causes are robot-specific constraints such as hallucinated control APIs, policy ordering and kinematic limits. POEF optimizes jailbreaks with those constraints taken into account and was tested on commercial robots (abstract). — [arXiv 2412.16633](https://arxiv.org/abs/2412.16633)
- **Embodied Red Teaming (ERT, arXiv 2411.18676, Nov 2024)** uses a VLM to generate diverse, contextually grounded instructions. It finds that state-of-the-art language-conditioned robot models "fail or behave unsafely" on these instructions, while standard benchmarks miss such cases (abstract). — [arXiv 2411.18676](https://arxiv.org/abs/2411.18676)
- **"On the Vulnerability of LLM/VLM-Controlled Robotics" (arXiv 2402.10340)** shows that simple instruction or perception perturbations cut task success by 22.2% and 14.6% in two representative LLM/VLM robot systems (abstract). — [arXiv 2402.10340](https://arxiv.org/abs/2402.10340)
- **Hundt et al., "LLM-Driven Robots Risk Enacting Discrimination, Violence, and Unlawful Actions" (arXiv 2406.08824; Int. J. Social Robotics 2025 per arXiv comment)** reports that LLMs given open-vocabulary HRI tasks "accept dangerous, violent, or unlawful instructions", for example removing people's mobility aids (abstract). — [arXiv 2406.08824](https://arxiv.org/abs/2406.08824)

**Guardrails / formal verification**
- **RoboGuard ("Safety Guardrails for LLM-Enabled Robots", Ravichandran et al., arXiv 2503.07885)** works in two stages. First, a "root-of-trust" LLM (GPT-4o, temp 0, chain-of-thought) grounds pre-defined rules in the robot's world model as LTL specifications. Second, temporal-logic control synthesis (Spot library) resolves conflicts between those specifications and the proposed plan, deviating minimally from the user's intent. Measured results (sim, 70 behaviors, 210 evaluations per attack):
  - Template attack: 82.3% → 0.9% attack success.
  - RoboPAIR: 92.3% → 2.3%.
  - Direct prompt: 1.3% → 0.2%.
  - Adaptive attacks: 2.5% (black-box), 2.9% / 3.8% (gray-box), 5.2% (white-box).
  - Safe-task performance stayed at 100%.
  - Real Jackal UGV, 35 harmful behaviors: RoboPAIR 100% → 0%.
  - Ablation: removing CoT raised ASR from 4.3% to 12.8%.
  - Cost: about 4,330 tokens and 1 LLM query per inference. No latency was reported.
  - Stated limitation: it requires an accurate world model, and a compromised world model or perception layer breaks it.
  - No quantitative head-to-head against prompt-based guards or SafetyChip (qualitative discussion only).
  — [arXiv 2503.07885 (HTML v2)](https://arxiv.org/html/2503.07885v2)
- **Safety Chip ("Plug in the Safety Chip: Enforcing Constraints for LLM-driven Robot Agents", Yang et al., Brown; arXiv 2309.09919, first posted Sep 2023)** is a queryable LTL-based constraint module. It translates natural-language constraints to LTL, explains violations and prunes unsafe actions. Tested in VirtualHome and on a real robot, it "strictly adheres to the safety constraints and scales well with complex safety constraints". It cites ISO 61508 as motivation (abstract). [ICRA 2024 venue unverified; suggested by an h2r.cs.brown.edu "yang24.pdf" link in search results] — [arXiv 2309.09919](https://arxiv.org/abs/2309.09919)
- **SELP (arXiv 2409.19471, ICRA 2025 per arXiv comment)** combines three techniques: equivalence voting over multiple sampled NL→LTL translations, LTL-constrained decoding of plans, and domain fine-tuning. On drone navigation it beats state-of-the-art planners by +10.8% safety rate and +19.8% plan efficiency (abstract). — [arXiv 2409.19471](https://arxiv.org/abs/2409.19471)
- **SafePlan (arXiv 2503.06892, Mar 2025)** combines formal logic with chain-of-thought reasoners (prompt sanity, invariant, precondition and postcondition) to screen prompts, plans and task allocations. It reports a 90.5% reduction in harmful-prompt acceptance while keeping "reasonable" acceptance of safe tasks (abstract). — [arXiv 2503.06892](https://arxiv.org/abs/2503.06892)
- **Introspective Planning (arXiv 2402.06529, NeurIPS 2024)** retrieves introspective rationales and adds conformal prediction. This improves compliance and safety on a new safe mobile-manipulation benchmark and tightens statistical success guarantees with fewer clarification requests (abstract). — [arXiv 2402.06529](https://arxiv.org/abs/2402.06529)

**CBF / reachability safety filters for LLM output**
- **SAFER (arXiv 2503.15707, Mar 2025)** pairs a separate Safety Agent LLM with the planner, adds an LLM-as-a-Judge violation metric, and puts a CBF layer under the plan for execution-level guarantees. It was verified on multi-robot hardware with a human (abstract). A 77.5% average reduction in violations appears in a search summary but was not verified in the abstract. — [arXiv 2503.15707](https://arxiv.org/abs/2503.15707)
- **"Safe LLM-Controlled Robots with Formal Guarantees via Reachability Analysis" (arXiv 2503.03911, Mar 2025)** builds reachable sets from historical robot-LLM data and filters the low-level control actions the LLM emits for goal navigation. It gives formal guarantees without an analytical model (abstract). — [arXiv 2503.03911](https://arxiv.org/abs/2503.03911)
- **Brunke et al., "Semantically Safe Robot Manipulation" (arXiv 2410.15185; IEEE RA-L vol. 10 no. 5, May 2025)** has an LLM infer semantically unsafe conditions (e.g., cup of water above a laptop) from a 3D semantic map. These conditions, together with geometric collision constraints, are enforced by a control-barrier certification filter on teleop and diffusion-policy inputs in a real kitchen (abstract). — [arXiv 2410.15185](https://arxiv.org/abs/2410.15185)

**Constitutions / semantic-safety benchmarks**
- **AutoRT (arXiv 2401.12963; ICRA 2024 VLMNM workshop per arXiv comment)** proposed tasks to more than 20 robots and collected 77k real episodes. Per ASIMOV's description, it used a hand-written "robot constitution" of safety and embodiment rules to critique LLM-proposed tasks. — [arXiv 2401.12963](https://arxiv.org/abs/2401.12963); [ASIMOV paper](https://arxiv.org/html/2503.08663v1)
- **ASIMOV Benchmark + auto-generated robot constitutions (arXiv 2503.08663, Mar 2025, Google DeepMind).**
  - Benchmark: the validation split has 310 contexts, 2,273 actions and 1,140 human labels; the full set is about 514k contexts and 2.94M actions. Sources include RoboVQA images edited to add hazards and NEISS hospital injury reports.
  - Baselines (Gemini 1.5 Pro): with no constitution, alignment is 83.6% in normal mode but 33.6% in "adversary" mode. Asimov's Three Laws average 75.1% (65.1% adversary). Random and no-rules score 52.1% and 51.2%.
  - Best constitution: an auto-generated, auto-amended 128-rule constitution averages 84.3% (80.9% adversary), but it is about 298k characters long.
  - Jailbreaks: a secondary constitution check caught 100% of RoboPAIR undesirable commands across 7 self-driving situations.
  — [arXiv 2503.08663 (HTML)](https://arxiv.org/html/2503.08663v1)
- **SafeAgentBench (arXiv 2412.13178, Dec 2024)** has 750 executable tasks covering 10 hazard types and 3 task types, with 17 high-level actions, run on 9 agent baselines. "The most safety-conscious baseline achieves only a 10% rejection rate for detailed hazardous tasks", and swapping the LLM does not fix this (abstract). — [arXiv 2412.13178](https://arxiv.org/abs/2412.13178)
- **LabSafety Bench (arXiv 2410.14182; Nature Machine Intelligence 8, 20–31 (2026) per journal-ref)** has 765 MCQs plus 404 lab scenarios (3,128 open-ended tasks) and was run on 19 LLMs/VLMs. No model exceeds 70% on hazard identification. Proprietary models do not have a clear advantage on open-ended reasoning (abstract). — [arXiv 2410.14182](https://arxiv.org/abs/2410.14182)
- **EARBench (arXiv 2408.04449)** finds an average task risk rate of 95.75% across evaluated foundation models. Prompt-based mitigations help only partly (abstract). — [arXiv 2408.04449](https://arxiv.org/abs/2408.04449)
- **IS-Bench (arXiv 2506.16402, Jun 2025)** has 161 household scenarios with 388 risks and checks whether mitigation steps happen before or after risk-prone steps. GPT-4o and Gemini-2.5 "lack interactive safety awareness". Safety-aware CoT improves safety but "often compromises task completion" (abstract). — [arXiv 2506.16402](https://arxiv.org/abs/2506.16402)
- **Survey: "Trust in LLM-controlled Robotics: a Survey of Security Threats, Defenses and Challenges" (arXiv 2601.02377, Dec 2025)** gives a taxonomy of attacks (jailbreak, backdoor, multimodal prompt injection) and defenses (formal specs, runtime enforcement, multi-LLM oversight, prompt hardening). — [arXiv 2601.02377](https://arxiv.org/abs/2601.02377)

### Inferences
- The strongest numbers come from guards that turn LLM intent into a formal artifact and check it with a non-LLM procedure: LTL synthesis (RoboGuard), automaton pruning (Safety Chip) or constrained decoding (SELP). Pure-LLM judges and constitutions sit at about 80–90% alignment and drop under adversarial framing.
- Most measured results are household, office or navigation tasks in simulation. Real-hardware trials are small: 35 behaviors for RoboGuard on Jackal, and RoboCritics had n=18 users.

### Gaps
- No paper found gives a controlled head-to-head of several guard types (prompt vs. LLM-judge vs. formal vs. controller-level) on the same attack set.
- No published latency figures for RoboGuard.
- The SAFER 77.5% figure comes from a secondary summary only.

## Where guards sit, and evidence on which placement is more robust

### Takeaway
Guards appear at four layers:
- in the prompt (constitutions, defensive prompts);
- in the agent framework (safety agents, CoT reasoners);
- in a separate verifier model or formal checker (root-of-trust LLM plus LTL synthesis);
- at the controller (CBF, reachability, motion critics).

The evidence favors guards that the attacker's input cannot reach and that end in deterministic checks. No study isolates placement as the only variable.

### Cited Findings
- RoboGuard's design argument is that its root-of-trust LLM receives only the system prompt (robot API, rules, world model) and never the user prompt, so attackers cannot address it directly. A theorem guarantees that synthesized plans satisfy the generated specifications. Robustness still degrades slightly as attacker access grows, from 2.5% (black-box) to 5.2% (white-box). — [arXiv 2503.07885 HTML](https://arxiv.org/html/2503.07885v2)
- Prompt-level constitutions degrade sharply under adversarial framing. ASIMOV's "Theory of Mind: Good Person" scores 88.8% in normal mode vs. 61.3% in adversary mode, and the no-constitution baseline falls from 83.6% to 33.6%. — [arXiv 2503.08663 HTML](https://arxiv.org/html/2503.08663v1)
- Prompting can strongly increase refusal of infeasible instructions. Defensive prompting raises abstention from 18.2% to 90.8% for Gemini Robotics ER 1.6 and from 15.4% to 88.3% for GPT-5.4 Mini. That still leaves about 10% non-abstention. — [arXiv 2605.20544 HTML](https://arxiv.org/html/2605.20544v1)
- POEF shows that physical-layer constraints (executable APIs, kinematics, ordering) already block many "intent" jailbreaks. This is indirect evidence that robot-side or API-side constraints are a real barrier, but also that an attacker who models them can get around them. — [arXiv 2412.16633](https://arxiv.org/abs/2412.16633)
- Controller-level filters (CBF in SAFER and Brunke et al.; reachability in 2503.03911) enforce constraints on the commands the actuators receive, whatever the plan says. — [arXiv 2503.15707](https://arxiv.org/abs/2503.15707); [arXiv 2410.15185](https://arxiv.org/abs/2410.15185); [arXiv 2503.03911](https://arxiv.org/abs/2503.03911)
- Motion-level critics on a UR3e analyze execution traces for joint-speed violations, collisions and unsafe end-effector poses, then send structured feedback to the LLM. In a between-subjects study (n=18) they reduced safety violations compared with a plain LLM interface (HRI 2026 per arXiv comment). — [arXiv 2603.06842](https://arxiv.org/abs/2603.06842)
- Community ROS 2 projects (not peer-reviewed) describe deny-by-default safety kernels in a separate process from the agent (OpenRAL) and deterministic capability validators above the device's own safety function. — [ROS Discourse: OpenRAL](https://discourse.openrobotics.org/t/openral-the-agentic-harness-for-physical-ai-ros-2-native/56352); [ROS Discourse: runtime between LLM and actuation](https://discourse.openrobotics.org/t/a-runtime-that-sits-between-an-llm-and-physical-actuation-does-this-fit-your-use-case/57536)

### Inferences
- The robustness ordering implied by the results is: in-prompt < in-framework LLM judge < isolated verifier with formal synthesis < controller or robot-side deterministic enforcement. Only the controller and robot-side layer is independent of LLM correctness and of world-model fidelity at plan time. This is an inference; no single study ranks these placements directly.
- RoboGuard's own stated limitation (it relies on an accurate world model) means a plan-level guard is not enough when perception or state is wrong. A robot-side gate that re-reads live sensors fills that gap, which matches the user's design: refusing motion when an obstacle is under 0.3 m or a reading is unknown.

### Gaps
- No controlled ablation study moves the same guard logic between layers.
- No peer-reviewed measurement found of how often robot-side gates block LLM-originated commands in field campaigns, comparable to the user's 13 blocked arm moves.

## Infeasibility detection and refusal vs. silent "repair"; effect of model size

### Takeaway
LLM/VLM planners rarely abstain. They usually turn impossible or ambiguous instructions into some executable action: they pick arbitrary targets, invent objects or merge contradictions. Model scale improves planning much more than it improves safety or abstention. Only proprietary reasoning models show clearly higher safety awareness.

### Cited Findings
- **RoboAbstention / "The Yes-Man Syndrome: Benchmarking Abstention in Embodied Robotic Agents" (Yeke et al., Purdue/Bilkent, arXiv 2605.20544, May 2026)** has 6,069 image-grounded instructions.
  - Abstention rates: Gemini 2.5 Flash 39.0% (best), Claude Sonnet 4.6 26.4%, Llama 4 Maverick 18.8%, Gemini Robotics ER 1.6 16.5%, GPT-5.4 12.9%, GPT-5.4 Nano 12.5%, Qwen 3.5 27B 9.2% (lowest).
  - Physical infeasibility category: abstention was low; the best was 26.0%, and GPT-5.4 Mini without reasoning abstained 0%.
  - Within the GPT-5.4 family, scale had little effect. Higher reasoning effort *lowered* abstention, from 14.2% to 9.8%.
  - Failure analysis on GPT-5.4 found the model "converted uncertainty into action": Arbitrary Target Selection (964), Overconfident Grounding (702), Invented Target (430), Tactile Workaround (188) and Conflict Workaround (180), the last being contradictory instructions merged into one plan.
  — [arXiv 2605.20544 HTML](https://arxiv.org/html/2605.20544v1)
- **DESPITE ("Using large language models for embodied planning introduces systematic safety risks", arXiv 2604.18463, Apr 2026)** has 12,279 tasks with deterministic validation and covers 23 models. The best planner produces an invalid plan on only 0.4% of tasks but a dangerous plan on 28.3%. Across 18 open models from 3B to 671B parameters, planning ability rises from 0.4% to 99.3% with scale, while safety awareness stays flat at 38–57%. Three proprietary reasoning models reach 71–81%. Larger models complete more tasks safely "primarily through improved planning, not through better danger avoidance" (abstract). — [arXiv 2604.18463](https://arxiv.org/abs/2604.18463)
- **RAMA benchmark / RationalVLA (arXiv 2506.10826, Jun 2025)** has more than 14,000 samples, including defective instructions in six dimensions: visual, physical, semantic, motion, safety and out-of-context. RationalVLA's dual system learns to reject infeasible commands and scores 14.5% higher success than baselines (abstract). — [arXiv 2506.10826](https://arxiv.org/abs/2506.10826)
- **"Recognizing Limits: Investigating Infeasibility in LLMs" (arXiv 2408.05873, EMNLP 2025 Findings)** is a text-only study. It defines four categories of infeasible tasks, including physical interaction, benchmarks how well LLMs decline them, and shows that fine-tuning improves refusal (abstract). — [arXiv 2408.05873](https://arxiv.org/abs/2408.05873)
- SafeAgentBench reports a 10% maximum rejection rate for detailed hazardous tasks, and swapping the LLM does not help (abstract). — [arXiv 2412.13178](https://arxiv.org/abs/2412.13178)

### Inferences
- The user's observation, a small local model silently rewriting impossible missions, matches the documented "conversion of uncertainty into action" failure modes (Invented Target, Conflict Workaround). It also matches DESPITE's finding that safety awareness does not scale with model size among open models. Expect the same behavior from larger open models. Refusal should not depend on the model; a deterministic feasibility check outside the model, or robot-side rejection, is the safer design.
- Defensive prompting plus in-context examples is a cheap way to raise abstention to about 90% (RoboAbstention). It was measured on frontier models only, so the gain for small local models is unknown.

### Gaps
- No study found that measures abstention of small local models (≤8B) on embodied infeasibility, apart from DESPITE's aggregate 3B–671B range. DESPITE's per-size abstention numbers were not extracted, since only the abstract was read.
- No study separates "refuse" from "silently repair and report success" as distinct measured outcomes, apart from RoboAbstention's failure-cluster counts.

## Sensor trust, stale or wrong state, and runtime monitoring of robot state

### Takeaway
Work on agents acting on stale or false state is thin and mostly framed as failure detection and recovery. The common recommendations are explicit pre- and post-condition checks against fresh observations and uncertainty-based detectors, not LLM self-assessment. I found no paper that specifically studies "unknown reading ⇒ unsafe" policies, or proprioceptive state such as odometry agreeing with wrong commands, for LLM agents.

### Cited Findings
- RoboGuard explicitly lists a compromised world model as a failure path and says perception safeguards are needed. — [arXiv 2503.07885 HTML](https://arxiv.org/html/2503.07885v2)
- **"Agentic AI for Robot Control: Flexible but still Fragile" (arXiv 2602.13081, Feb 2026)** deploys a reasoning-LLM planner/executor on Mobipick (mobile manipulation) and Valdemar (agricultural navigation) under partial observability and sensor noise. It reports "substantial fragility": non-deterministic suboptimal behavior, instruction-following errors and high sensitivity to the prompt. It relies on explicit event checks and operator interventions (abstract). — [arXiv 2602.13081](https://arxiv.org/abs/2602.13081)
- **KnowLoop (arXiv 2406.00430, ICRA 2024 workshop)** argues that LLM-based failure detection wrongly assumes its predictions are trustworthy, given hallucination. Token probability and entropy are better failure signals than the model's self-explained confidence (abstract). — [arXiv 2406.00430](https://arxiv.org/abs/2406.00430)
- **VLM + reactive planner + behavior trees (arXiv 2503.15202, ABB YuMi)** combines pre-execution verification of preconditions, reactive failure handling during execution, a scene graph and an execution history. This gave higher success than either pre-execution or reactive handling alone (abstract). — [arXiv 2503.15202](https://arxiv.org/abs/2503.15202)
- **HoloAgent-0 (arXiv 2606.23565)** has a monitoring and verification layer that checks skill outcomes against execution evidence and feeds re-planning (search snippet only; not opened). — [arXiv 2606.23565](https://arxiv.org/pdf/2606.23565)
- Pre-LLM but directly relevant: NASA/VCU's Ogma generates ROS 2 runtime-monitor nodes from structured requirements, and these publish violations (2022). — [arXiv 2209.14030](https://arxiv.org/abs/2209.14030)
- Safety Chip stops execution when the automaton predicts the next action reaches an unsafe state. This is runtime monitoring of the action sequence, not of sensor validity. — [arXiv 2309.09919](https://arxiv.org/abs/2309.09919)

### Inferences
- Treating unknown or invalid readings as unsafe (fail-closed) is standard functional-safety practice. It is largely missing from LLM-robot papers, which assume a correct world model. This is a real gap the user's design addresses.
- Odometry that "agrees" with a wrong command is a common-mode failure: the agent's plan and the state estimate share an error source. Independent checks, such as a second sensor or a range check against a map, are needed. No LLM-robot paper was found that measures this.

### Gaps
- No peer-reviewed study found on LLM agents acting on stale ROS topics or timestamps, or on sensor-validity gating for LLM-issued motion.
- The STT-Arena "stale-state execution" finding (arXiv 2605.18548) is from tool-use agents, not robots. It was not verified (search snippet only).

## Industrial settings: industrial robots, welding, CNC, ISO 10218 / ISO/TS 15066, process-limit guards

### Takeaway
Peer-reviewed work that connects LLM agents to industrial-robot safety standards is sparse. The closest examples are an LLM turning ISO 13849 requirements into executable predicates on an edge runtime, motion-level critics for LLM-generated UR3e programs, and Safety Chip's ISO 61508 motivation. I found no paper on LLM agents for welding or CNC with process-parameter envelope guards (WPS-like).

### Cited Findings
- ISO 10218-1:2025 sets safety requirements for industrial robots as partly completed machinery. ISO 10218-2 covers integration into robot systems and cells. Service robots for the public, medical, military and underwater robots are excluded. — [ISO 10218-1:2025 (iso.org)](https://www.iso.org/standard/73933.html)
- The 2025 revision of ISO 10218 incorporates ISO/TS 15066 guidance on collaborative operation and safety-function validation, and links to ISO 13849, 13855 and 20607 (certification-body page, secondary source). — [TÜV NORD](https://www.tuv-nord.com/tw/en/homepage/product-and-service/product-safety/iso-10218-1-2/)
- **"LLM-Guided Safety Agent for Edge Robotics with an ISO-Compliant Perception-Compute-Control Architecture" (arXiv 2604.20193, Apr 2026)** has an LLM translate natural-language safety regulations into executable predicates. The predicates are deployed on a dual-modular-redundant dual-RK3588 edge runtime for HRI, as a path toward ISO 13849 Category 3 / PL d (abstract). — [arXiv 2604.20193](https://arxiv.org/abs/2604.20193)
- **RoboCritics (arXiv 2603.06842, HRI 2026)** uses expert-informed critics that check LLM-generated UR3e programs for joint-speed limits, collisions and unsafe poses before or while running. Violations dropped compared with a plain LLM interface (n=18). — [arXiv 2603.06842](https://arxiv.org/abs/2603.06842)
- Safety Chip cites ISO 61508 as a motivating standard for verifiable industrial deployment. (The abstract says "ISO 61508"; the standard is usually designated IEC 61508.) — [arXiv 2309.09919](https://arxiv.org/abs/2309.09919)
- A university thesis on a UR10e describes a safety watchdog that checks MoveIt trajectories against workspace, joint and velocity limits before execution, at the cost of re-planning delays (search snippet; not opened). — [unitesi.unimore.it](https://unitesi.unimore.it/handle/20.500.14251/6849)

### Inferences
- The user's FANUC welding-envelope guard (a WPS-like parameter range enforced robot-side) does not appear to have a published counterpart in LLM-robot literature. The nearest analogues are joint-speed and pose critics (RoboCritics) and LLM-to-predicate translation that a deterministic runtime then enforces (2604.20193).
- Standards treat safety functions as deterministic and validated (ISO 13849 PL, ISO 10218). This argues for keeping the LLM outside the safety function and having it propose only within an envelope enforced by certified or deterministic layers.

### Gaps
- No paper found on LLM agents for arc welding, CNC or G-code with process-limit guards. An arXiv keyword query for LLM plus welding/CNC/G-code returned no relevant hits; the query may have been malformed, so this is not conclusive.
- The ISO/TS 15066 page was not opened directly. Its content (power and force limits, speed and separation monitoring) is not cited here from a primary page.
- No public guidance from standards bodies was found on LLM- or AI-generated robot commands.
