# LLM-Based Multi-Robot Coordination and Multi-Agent LLM Planning for Robot Teams (2024–2026)

Verification note: every arXiv ID marked [verified] was opened on arxiv.org during this research (abs or html page). Items marked [UNVERIFIED] came only from a secondary source (the 2502.03814 survey or a search snippet) and were not opened. Venue claims come from the arXiv comments field. "Submitted to X" does not mean accepted.

## Key systems/papers: what they showed and on what hardware

### Takeaway
The field has settled on a few architecture families, and real-robot validation is still small:
- **Dialectic/decentralized:** RoCo.
- **Centralized staged prompting:** SMART-LLM.
- **Centralized assigner with executor feedback:** COHERENT, CoMuRoS.
- **LLM front end plus classical PDDL search:** LaMMA-P and successors.
- **Centralized VLM/LLM frontier allocators for exploration:** Co-NavGPT, LLM-MCoX.

Physical tests typically use 2–8 robots, and headline numbers come mostly from AI2-THOR, RoCoBench, or HM3D simulation. Hybrid or hierarchical designs beat fully decentralized dialogue, mainly because of context and token growth.

### Cited Findings
- **RoCo** (Mandi, Jain, Song; arXiv 2307.04738, [verified]; first posted July 2023, so 2023 background that is heavily used in 2024–25 work):
  - Each robot arm has its own LLM agent. The agents hold a dialogue to agree on subtask plans and task-space waypoints.
  - Environment feedback such as collision checking is returned, and the agents revise their plans in-context.
  - Introduces RoCoBench, a 6-task multi-arm benchmark, plus a text-only dataset. Reports "high success rates", with no numbers on the abs page. Includes real-world human-in-the-loop experiments.
  - The abs page shows no venue. The 2502.03814 survey cites it as Mandi et al. 2024.
  - — [arXiv 2307.04738](https://arxiv.org/abs/2307.04738)
- The 2502.03814 survey says RoCo's real-world performance "is primarily bottlenecked by incorrect object detection from the onboard vision pipeline". It describes RoCo's replanning as a "5-validator dialectic loop". — [LLMs for Multi-Robot Systems: A Survey](https://arxiv.org/html/2502.03814v5)
- **SMART-LLM** (Kannan, Venkatesh, Min; arXiv 2309.10062, [verified]; "Submitted to IROS 2024"; the survey lists it as Kannan et al. 2024):
  - Pipeline: few-shot programmatic prompts for task decomposition, then coalition formation, then task allocation, then code generation.
  - Benchmark: 36 AI2-THOR instructions (6 elemental, 8 simple, 14 compound, 8 complex), with 1–4 robots per task.
  - GPT-4 success rate: 1.00 on elemental, 0.62 on simple, 0.69 on compound, 0.71 on complex tasks. Executability was 0.97–1.00.
  - Real robots: aerial and ground robots with GoToLocation, ClickPicture, and Patrol skills, doing visibility coverage and patrolling. Results were qualitative only.
  - — [arXiv 2309.10062v2 html](https://arxiv.org/html/2309.10062v2)
- **"Centralized or Decentralized?"** (Chen, Arkin, Zhang, Roy, Fan; ICRA 2024; arXiv 2309.15943, [verified]):
  - Compares 4 frameworks: centralized, decentralized, and two hybrids.
  - A hybrid framework gave the best success rate on all four tasks and scaled better with more agents.
  - — [arXiv 2309.15943](https://arxiv.org/abs/2309.15943)
- The survey gives the numbers from that paper. Fully decentralized DMAS reaches "only 25% success on BoxNet1, compared to 82.5% for the hybrid HMAS-2." Decentralized dialogue fails at scale because the "peer-to-peer dialog history exhaust[s] the context token budget." — [Survey 2502.03814](https://arxiv.org/html/2502.03814v5)
- **COHERENT** (Liu, Tang, Wang, Wang, Li, Zhao; ICRA 2025; arXiv 2409.15146, [verified]):
  - Uses a Proposal-Execution-Feedback-Adjustment (PEFA) loop. A centralized task assigner proposes subtasks for robot executors. Each executor picks a feasible action and sends self-reflection feedback to the assigner, which adjusts the plan.
  - Benchmark: 100 long-horizon tasks for heterogeneous teams.
  - Robots: quadrotors, robot dogs, and arms, in simulation and real.
  - Reports a large-margin improvement. The abs page gives no numbers.
  - — [arXiv 2409.15146](https://arxiv.org/abs/2409.15146)
- The survey notes the costs of these loops: "PEFA adds re-planning latency, the actor-critic roughly doubles LLM call overhead, and dialogue overhead grows rapidly with agent count." — [Survey 2502.03814](https://arxiv.org/html/2502.03814v5)
- **LaMMA-P** (Zhang, Qin, Wang, Dong, Li; ICRA 2025; arXiv 2409.20560, [verified]):
  - A language model-driven multi-agent PDDL planner. The LM identifies and allocates subtasks across a heterogeneous team, and a classical heuristic-search planner solves them.
  - New MAT-THOR benchmark on AI2-THOR, with two difficulty levels. A search snippet describes it as 70 tasks over 5 floor plans, including vague-command tasks.
  - Reports 105% higher success rate and 36% higher efficiency than prior LM-based multi-agent planners.
  - — [arXiv 2409.20560](https://arxiv.org/abs/2409.20560)
- **LLM + PDDL successors** (from search results; abstracts only, not opened in full):
  - Hierarchical multi-agent LLM framework with prompt optimization that generates PDDL for a classical solver (Kawabe & Takano). A snippet reports MAT-THOR success rates of 0.95 on compound, 0.84 on complex, and 0.60 on vague tasks, versus 0.45 for LaMMA-P on vague tasks. — [arXiv 2602.21670](https://arxiv.org/html/2602.21670) [ID seen in search, numbers from snippet, not verified in paper]
  - Scale-Plan built a cleaned MAT2-THOR after finding missing or incorrect goal conditions and duplicate tasks in MAT-THOR. This is a caveat for LaMMA-P comparisons. — [arXiv 2603.08814](https://arxiv.org/html/2603.08814) [snippet only]
  - FLEET: formal-language-grounded scheduling for heterogeneous teams. — [arXiv 2510.07417](https://arxiv.org/pdf/2510.07417) [title only]
- **CoMuRoS** (Borate et al.; arXiv 2511.22354, [verified]; the page says the full version is accepted at Frontiers in Robotics and AI):
  - A central Task Manager LLM classifies and allocates tasks. Each robot runs a local LLM that writes Python over primitive skills, which include ROS 2 nodes.
  - Onboard VLM perception triggers event-driven replanning.
  - Physical results: 9/10 collaborative object recovery, 8/8 coordinated transport, 5/5 human-assisted recovery.
  - Text benchmark: 22 scenarios with about 20 robots, correctness up to 0.91.
  - — [arXiv 2511.22354](https://arxiv.org/abs/2511.22354)
- **Air-ground language missions** (Cladera, Ravichandran, Hughes, Murali, Nieto-Granda, Hsieh, Pappas, Taylor, Kumar; arXiv 2505.09108, [verified]; submitted to T-FR, which the survey lists as IEEE Transactions on Field Robotics):
  - One UAV plus one UGV. An LLM planner reasons over semantic-metric maps that are built online and shared opportunistically.
  - Seven natural-language missions in urban and rural settings, with navigation up to kilometer scale.
  - — [arXiv 2505.09108](https://arxiv.org/abs/2505.09108)
- **Other systems** named in the survey's real-robot list, not opened here [UNVERIFIED IDs]:
  - VADER (Ahn et al. 2024, arXiv 2405.16021): decentralized, with error recovery and help requests.
  - REBEL (Gupte et al. 2024, arXiv 2409.16266).
  - EMOS (Chen et al., listed as ICLR 2025): capability-aware, heterogeneous.
  - DART-LLM (Wang et al. 2024).
  - LLM2Swarm, LLM-Flock (Crazyflie drones), and Hunt et al. 2024a (AAMAS '24, human-approved plans).
  - — [Survey 2502.03814](https://arxiv.org/html/2502.03814v5)
- **Scale of validation:** "Real-robot counts are typically in the range of two to eight", and "no system ... clearly exceeds roughly ten physical robots"; "few approaches [are] validated beyond roughly ten robots." — [Survey 2502.03814](https://arxiv.org/html/2502.03814v5)
- **Benchmark gaps:** "None of the four benchmarks reports hallucination rate, token consumption, API-call count, wall-clock inference latency." Benchmarks are "primarily designed for indoor environments and household applications." — [Survey 2502.03814](https://arxiv.org/html/2502.03814v5)

### Inferences
- A JSON plan sent to a central blackboard fits the centralized or hierarchical family (SMART-LLM, COHERENT, CoMuRoS, LLM-MCoX). The literature favors this family over decentralized dialogue at small fleet sizes.
- The most common upgrade over plain centralized planning is an executor-to-planner feedback channel, as in COHERENT's PEFA loop and CoMuRoS's event-driven replanning. The user's blackboard could carry that feedback.
- LLM+PDDL hybrids are the clearest way to get hard feasibility guarantees, because a classical planner fails explicitly when no plan exists.

### Gaps
- MultiAgentBench (believed to be arXiv 2503.01935) was not verified. From memory, it is a general LLM multi-agent benchmark, not a robot benchmark. I found no robot-specific "MultiAgentBench-style" fleet benchmark beyond RoCoBench, MAT-THOR/MAT2-THOR, the COHERENT 100-task benchmark, and the CoMuRoS text benchmark.
- COHERENT's and RoCo's numerical success rates were not retrieved, because the abs pages carry no numbers.

## Handling infeasible or ambiguous missions (refusal, clarification, feasibility checks, silent repair)

### Takeaway
Explicit refusal is rarely measured in multi-robot LLM work.
- SMART-LLM is the clearest data point. GPT-4 and Claude-3 declined to allocate when no robot had the needed skill, while GPT-3.5 and Llama2 assigned unsuitable robots. That is the "silent repair" failure mode with weaker models. Only qualitative results were given.
- Ambiguity is handled by clarification-question frameworks (SG-CoT) and vague-task splits (MAT-THOR).
- Feasibility is enforced by capability matching, PDDL solvers, or validators.

I found no paper that directly measures "silent rewriting" of impossible missions by small models.

### Cited Findings
- **SMART-LLM** tested the case where no robot has the required skill separately, since no metrics can be computed without feasible code:
  - "GPT-4 and Claude-3 recognized the infeasibility and generated no allocation plan".
  - "GPT-3.5 and Llama2 instead assigned ill-suited robots". No counts were reported.
  - Its coalition-formation stage explicitly matches the skills each subtask needs against robot skills, and adds robots for payload limits.
  - — [arXiv 2309.10062v2](https://arxiv.org/html/2309.10062v2)
- **SafeAgentBench** (arXiv 2412.13178, [verified]; preprint with no venue): 750 embodied tasks covering 10 hazards. "The most safety-conscious baseline achieves only a 10% rejection rate for detailed hazardous tasks." Swapping the LLM does not notably improve safety awareness. It is a single-agent benchmark, but it is the closest quantitative evidence that LLM planners rarely refuse. — [arXiv 2412.13178](https://arxiv.org/abs/2412.13178)
- **SG-CoT** (arXiv 2603.18271, [verified]; submitted to Autonomous Robots):
  - The LLM queries a scene graph through retrieval functions, finds the source of an ambiguity, and asks a targeted disambiguation question to the user or to another robot.
  - Question accuracy improves by at least 10%. Success improves by at least 15% in multi-agent environments.
  - — [arXiv 2603.18271](https://arxiv.org/abs/2603.18271)
- **CoMuRoS:**
  - A search summary said its Task Manager classifies tasks as independent, sequential, coordinated, or infeasible. The abs page I opened did not describe infeasible handling.
  - The abs page does state that replanning can "request human help".
  - — [arXiv 2511.22354](https://arxiv.org/abs/2511.22354) (the "infeasible" category is not confirmed on the abs page)
- **Kinematic infeasibility:** LLM multi-robot plans are often kinematically infeasible. Hu et al. add hierarchical temporal logic with receding-horizon reachability and collision checks. — [arXiv 2602.09472](https://arxiv.org/abs/2602.09472) [abs listed in search, not opened]
- **Capability awareness:** without capability representations, "LLMs may assign tasks to physically incapable robots" (on Gupte/REBEL and EMOS). The survey also notes a RoCo directive that "may be physically infeasible for some recipients". — [Survey 2502.03814](https://arxiv.org/html/2502.03814v5)
- **Human review:** Hunt et al. (2024a) and Li et al. (2025c) use human approval or verification against hallucinated plans. The survey recommends "consensus or human-in-the-loop critique layers to filter erroneous LLM outputs before they reach actuators". — [Survey 2502.03814](https://arxiv.org/html/2502.03814v5)
- **Error recovery** across systems "relies heavily on prompt-level re-invocation triggered by syntactic checks, validator failures, or discussion rounds." — [Survey 2502.03814](https://arxiv.org/html/2502.03814v5)
- **Infeasibility metrics:** general LLM-planning evaluation defines metrics for spotting unachievable tasks (true negative rate, false negative rate, "unreachable accuracy"), but robot benchmarks do not report them. — search summary of [ACL 2025 survey of LLM planning](https://aclanthology.org/2025.acl-long.958.pdf) [snippet, not opened]
- **Vague instructions:** MAT-THOR includes vague-command tasks, and vague tasks are the weakest category for PDDL hybrids (0.60 vs 0.45; see above). — [arXiv 2602.21670](https://arxiv.org/html/2602.21670) [snippet]
- **Pre-execution verification:** VerifyLLM checks robot task plans before execution. — [arXiv 2507.05118](https://arxiv.org/pdf/2507.05118) [title only, not opened]
- **Background, pre-2024, [UNVERIFIED]:** KnowNo ("Robots That Ask For Help", Ren et al., CoRL 2023, believed arXiv 2307.01928) uses conformal prediction to decide when to ask for clarification. It is single-robot, cited from memory, and was not opened.

### Inferences
- The user's 0/18 refusals on impossible missions matches the SMART-LLM finding that smaller or weaker models assign unsuitable robots instead of declining. It also matches SafeAgentBench's best-case 10% rejection rate. "Silent repair" looks like the default behavior, not an anomaly.
- The literature's remedies, none of which rely on the LLM to refuse:
  - A structured capability check: SMART-LLM-style coalition matching, or a PDDL or validator gate that fails loudly.
  - An explicit "infeasible" output class, as reported for CoMuRoS.
  - A clarification or human-approval channel: SG-CoT, Hunt et al.
- A cheap measurable fix for the user's setup: a schema field such as `feasible: false` + `reason`, plus a deterministic post-check that compares the plan with the mission. Any rewrite of mission objects or targets would then be flagged as repair, not counted as success.

### Gaps
- No paper found that quantifies "silent repair" or plan rewriting on impossible multi-robot missions, or that compares small and large models on refusal in a fleet setting. This looks like a genuine gap, and possibly a publishable contribution.
- The CoMuRoS infeasible-category handling and the Hu et al. details were not confirmed in full text.

## Communication substrate: ROS 2 topics/blackboards, message loss, latency, Wi-Fi effects

### Takeaway
Most LLM multi-robot papers assume lossless, synchronous messaging and a central computer over Wi-Fi. Only a few, such as Cladera et al., design for intermittent links. LLM latency (seconds to tens of seconds) dominates network latency, so planners run at low frequency. I found no paper that measures ROS 2 message loss or Wi-Fi effects on an LLM-coordinated fleet.

### Cited Findings
- "MAS benchmarks commonly assume lossless, turn-synchronous message passing and negligible deliberation latency, both of which break under field conditions." — [Survey 2502.03814](https://arxiv.org/html/2502.03814v5)
- Most decentralized systems "presume reliable neighbor message passing". Only Cladera et al. (2025) and Ravichandran et al. (2025) are "explicitly designed for intermittent or opportunistic communication." — [Survey 2502.03814](https://arxiv.org/html/2502.03814v5)
- **Latency:** LLM response times are "relatively high and variable". With GPT-4 in multi-agent path finding, "the response time per step ranged between 15 and 30 seconds" (Chen et al. 2024b). "LLMs tolerate deliberative latency only at low frequencies". — [Survey 2502.03814](https://arxiv.org/html/2502.03814v5)
- **Cloud dependence:** server-based models "require a reliable internet connection", and a server outage "can interrupt the systems built on LLMs entirely". Only Lim & Kovalenko (2025) and SayCoNav (Rajvanshi et al. 2025) "provide concrete timings". — [Survey 2502.03814](https://arxiv.org/html/2502.03814v5)
- **Field failures:** Cladera et al. reported wind-blown leaves disrupting LiDAR, false positives from open-vocabulary detectors, and communication loss, none of which appeared in simulation. The survey calls for simulators that model "LLM latency variance, communication packet loss, and perceptual noise." — [Survey 2502.03814](https://arxiv.org/html/2502.03814v5)
- **LLM-MCoX:** robots send map and pose updates over Wi-Fi to a central planner computer. The planner is queried about 20 times per run, robots sit idle while waiting for a plan, and planning time grows with team size. The real system used a 20-second replanning horizon. — [arXiv 2509.26324v1](https://arxiv.org/html/2509.26324v1)
- **Opportunistic map sharing:** Cladera et al. share semantic-metric maps when the intermittent link is available. — [arXiv 2505.09108](https://arxiv.org/abs/2505.09108)
- **CoMuRoS** exposes ROS 2 nodes as primitive skills behind per-robot LLM code generation. — [arXiv 2511.22354](https://arxiv.org/abs/2511.22354)
- **ROS 2 networking background** (not LLM-specific):
  - Kronauer et al.: end-to-end latency depends strongly on the DDS vendor, and ROS 2 adds about 50% overhead over raw DDS. Many messages were lost at high payloads on Raspberry Pi. — [arXiv 2101.02074](https://arxiv.org/abs/2101.02074) (search summary, abs listed)
  - A real-robot ROS 2 ad hoc wireless framework compares multicast and unicast, 802.11 retry settings, and RTPS reliability. — [arXiv 2111.01777](https://arxiv.org/pdf/2111.01777) [snippet]
  - Reliable QoS retransmission can cause severe latency spikes on wireless links. — [arXiv 2607.01304](https://arxiv.org/html/2607.01304v1) [snippet; secondary claims]

### Inferences
- For a ROS 2 blackboard topic, the realistic risks are:
  - a late joiner missing a one-shot plan (use the TRANSIENT_LOCAL durability policy with RELIABLE QoS for the plan topic);
  - reliable-QoS retransmission spikes over Wi-Fi on Raspberry Pi-class hardware;
  - planner latency of seconds stalling robots.
- None of these is characterized in the LLM literature. Measuring plan-delivery success and latency under induced Wi-Fi loss would fill the gap the survey names.

### Gaps
- No measurements found of message loss, latency distributions, or Wi-Fi degradation in an LLM-coordinated ROS 2 fleet.
- Ravichandran et al. 2025 (SayCoNav?) and its timing numbers were not verified.

## Multi-robot collaborative mapping/exploration with LLM frontier/region assignment

### Takeaway
Two main 2024–2026 lines exist: Co-NavGPT and LLM-MCoX.
- **Co-NavGPT:** a VLM assigns frontiers from a merged global map. Tested on HM3D, with real quadrupeds.
- **LLM-MCoX:** GPT-4o assigns waypoint sequences from pre-ranked frontier clusters plus doorways. Reports exploration about 22.7% faster and search up to 50% faster with 6 robots in simulation. Real test on a Go2 quadruped plus a quadrotor.

Both are centralized, and both use classical geometry to propose candidates, with the LLM choosing among them.

### Cited Findings
- **Co-NavGPT** (Yu, Yuan, Li, Kasaei, Cao; arXiv 2310.07937, [verified]; v3 May 2025; no venue on the page):
  - A VLM global planner receives a unified map merged from the robots' sub-maps, with robot states and frontier regions, and assigns frontiers to robots.
  - Evaluated on HM3D with no task-specific training. Ablations show the VLM's semantic priors matter.
  - Validated on real quadrupedal robots.
  - — [arXiv 2310.07937](https://arxiv.org/abs/2310.07937)
- The survey characterizes this line as LLMs "limited to allocating unexplored frontiers to each robot", serving mainly as task allocation. — search summary of [Survey 2502.03814](https://arxiv.org/html/2502.03814v5)
- **LLM-MCoX** (Wang, Hsu, Hunt, Luo, Kim, Pajic; arXiv 2509.26324, [verified]; submitted to ICRA 2026):
  - Candidate generation: frontiers are sampled and ranked by information gain minus weighted travel cost, with a minimum separation. Doorways are found by ray-casting.
  - GPT-4o receives the frontiers, doorways, robot states and capabilities, a grayscale map image, and plan summaries, and returns per-robot waypoint sequences.
  - Results:
    - 22.7% faster exploration than the best baseline, on large structured maps with 6 robots.
    - Search 19.6% faster in caves.
    - About 30% lower search time with heterogeneous teams, and up to 50% lower with a natural-language hint.
  - Real hardware: a Unitree Go2 and a quadrotor in an indoor hall.
  - — [arXiv 2509.26324v1](https://arxiv.org/html/2509.26324v1)
- **Cladera et al.:** an LLM planner over shared semantic maps, which gathers information for language-specified missions across a UAV and a UGV. — [arXiv 2505.09108](https://arxiv.org/abs/2505.09108)
- **LGR** (single-robot background): LLMs "cannot determine the absolute value of a frontier" but "excel at evaluating the relative ordering of frontiers". — [arXiv 2503.20241](https://arxiv.org/abs/2503.20241v1) [snippet]
- **Related, not opened:**
  - iHERO: human-oriented exploration under scarce communication. — [arXiv 2405.12571](https://arxiv.org/pdf/2405.12571)
  - LLMs for multi-robot path planning and task allocation. — [arXiv 2507.07302](https://arxiv.org/abs/2507.07302)
- **LLM limits on spatial planning:** LLMs struggle on maze-like MAPF maps and "perform poorly" on multi-robot TSP. "Centralized LLM-based formation controllers consistently succeed by avoiding distributed spatial reasoning." — [Survey 2502.03814](https://arxiv.org/html/2502.03814v5)

### Inferences
- The proven pattern for a searcher plus responders is that geometry proposes and the LLM disposes. Classical frontier or region extraction produces a short ranked candidate list, and the LLM assigns candidates using semantics or hints. Raw-map spatial reasoning by the LLM is weak.
- An LLM is most useful when there is a semantic hint ("victim likely near the doorway"). The biggest LLM-MCoX gains came with hints.

### Gaps
- No LLM frontier-allocation study reports behavior under communication loss, or at more than 6 robots in simulation or more than 2 on hardware.
- The quantitative results for Co-NavGPT were not retrieved.
