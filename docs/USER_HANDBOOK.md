# Soul Kiln User Handbook

## Introduction

Soul Kiln is a platform for discovering and testing morally-aligned agent configurations. The system treats virtues as basins of attraction in a knowledge graph, where agents with properly configured internal networks naturally flow toward virtuous behavior. Rather than programming specific rules about right and wrong, Soul Kiln evolves network topologies that inherently tend toward moral outcomes.

The name "kiln" reflects the process: just as a kiln fires clay to create lasting form, Soul Kiln refines candidate soul configurations through evolutionary pressure until stable, virtuous characters emerge. The system draws its virtue framework from the Kitáb-i-Aqdas, establishing nineteen virtues as fixed reference points around which agent behavior organizes.

This handbook explains every feature of the system, from basic concepts through advanced capabilities like diffusion-based action generation and outcome-driven learning.

---

## Part One: Foundational Concepts

### The Virtue Framework

At the heart of Soul Kiln lies a two-tier virtue model. The foundation tier contains a single virtue: Trustworthiness. This virtue carries a ninety-nine percent threshold and cannot be compromised under any circumstances. Trust forms the bedrock of all moral behavior in the system. An agent that fails to maintain trustworthiness faces immediate and severe consequences.

The aspirational tier contains eighteen additional virtues organized into four clusters. The core cluster includes Truthfulness, Sincerity, and Righteousness, representing alignment between inner state and outer expression. The relational cluster encompasses Justice, Fairness, Courtesy, Hospitality, and Goodwill, governing interactions between agents and stakeholders. The personal cluster contains Chastity, Forbearance, Fidelity, and Cleanliness, addressing individual conduct and self-mastery. The transcendent cluster includes Godliness, Piety, Wisdom, Detachment, Unity, and Service, pointing toward higher purpose and collective wellbeing.

Each aspirational virtue carries a threshold between sixty and ninety percent, and these thresholds adjust based on context. Young agents receive mercy through lower thresholds during their early generations. Different agent archetypes face different expectations based on their character type. A guardian archetype faces higher expectations for justice and righteousness, while a servant archetype faces higher expectations for hospitality and service.

### Topologies and Character

An agent's soul topology is the configuration of weighted edges connecting nodes in its internal network. These edges determine how activation flows when the agent encounters stimuli. Some topologies channel activation toward virtue basins reliably, while others allow activation to escape or flow toward harmful patterns.

Think of topology as character structure. Two agents might both value justice, but their topologies determine how strongly that value influences behavior across different contexts. One agent's topology might create strong pathways from conflict situations to justice-oriented responses, while another's might have weaker connections that allow other influences to dominate.

The system does not prescribe a single correct topology. Multiple valid configurations exist, each producing a different but coherent character. A guardian topology emphasizes trustworthiness, fidelity, righteousness, and justice. A seeker topology emphasizes wisdom, truthfulness, godliness, and detachment. A servant topology emphasizes service, hospitality, goodwill, and unity. A contemplative topology emphasizes piety, godliness, detachment, and chastity. All of these represent valid ways of being virtuous.

### Activation Dynamics

When an agent encounters a stimulus, activation spreads through its topology according to edge weights. Strong edges carry more activation; weak edges carry less. Activation decays over time at a rate of ninety-seven percent per interval, meaning influence fades unless reinforced.

The system implements Hebbian learning: edges that carry activation together strengthen over time. This means successful virtue capture reinforces the pathways that led to it. An agent that repeatedly routes conflict situations through justice-oriented responses develops stronger connections along that pathway.

Perturbation adds stochastic noise to help agents escape local minima. Without perturbation, an agent might settle into a suboptimal configuration simply because no single-step improvement exists. Small random variations allow exploration of nearby configurations that might prove superior.

### Virtue Capture and Alignment

A trajectory is the path activation takes through an agent's network after stimulus injection. A trajectory is captured when activation accumulates in a virtue basin above the capture threshold, typically seventy percent. A trajectory escapes when activation dissipates without being captured by any virtue.

Alignment testing measures what percentage of trajectories end in virtue capture. An agent needs at least ninety-five percent capture rate across diverse stimuli to pass alignment testing. This ensures the agent reliably routes toward virtue regardless of what situations it encounters.

The character signature emerges from which virtues capture most often. An agent whose trajectories predominantly end in justice, fairness, and righteousness develops a different character signature than one whose trajectories end in hospitality, goodwill, and service. Both can be aligned, but they express alignment differently.

---

## Part Two: The Kiln Evolution System

### Population Initialization

Evolution begins with a population of candidate topologies, each with randomly initialized edge weights. The initialization process ensures minimum connectivity by creating edges along natural virtue affinities. Trustworthiness connects to truthfulness, fidelity, and sincerity. Justice connects to fairness, righteousness, and wisdom. These initial connections provide structure while leaving room for evolutionary refinement.

Additional random edges create variation in the initial population. Some candidates might have strong connections between hospitality and service, while others emphasize the pathway from wisdom to detachment. This diversity ensures evolution has material to work with.

### Evaluation and Selection

Each candidate undergoes alignment testing, receiving a fitness score based on virtue capture rate. Candidates with higher capture rates have better fitness. The system supports multiple selection strategies.

Tournament selection randomly groups candidates and selects the best from each group as parents for the next generation. This provides selection pressure while maintaining diversity.

Truncation selection simply takes the top performers as parents, applying stronger pressure but risking premature convergence.

Roulette selection gives every candidate a chance proportional to their fitness, allowing lucky underperformers to occasionally contribute genetic material.

Elitism preserves the best candidates unchanged across generations, ensuring the population never loses its best discoveries.

### Crossover and Mutation

Selected parents produce offspring through crossover, which blends edge weights from both parents. A child might inherit its hospitality-to-service connection from one parent and its justice-to-fairness connection from the other. This recombination explores the space between successful configurations.

Mutation applies random perturbations to edge weights, introducing novelty that crossover alone cannot produce. The mutation rate controls how much variation each generation introduces. Higher rates explore more aggressively but risk disrupting successful configurations.

### Convergence and Termination

Evolution continues until a candidate achieves the minimum alignment score, typically ninety-five percent, or the maximum generation count is reached. Successful convergence produces a topology that reliably channels activation toward virtue basins.

The system tracks fitness statistics across generations, recording best, mean, and standard deviation. Watching these metrics reveals whether evolution is making progress. Plateaus might indicate the need for higher mutation rates or different selection pressure.

---

## Part Three: Gestalt and Character

### What is a Gestalt

A gestalt is the holistic character of an agent, capturing not just which virtues it possesses but how they relate, balance, and express as a unified whole. The gestalt answers the question: who is this agent?

Computing a gestalt combines multiple information sources. Virtue activations indicate which virtues are currently strong. The character signature from alignment testing shows which virtues capture trajectories most often. Virtue relations reveal patterns of reinforcement, tension, and conditioning between virtues. Behavioral tendencies translate virtue patterns into decision-making preferences.

The gestalt is more than the sum of these parts. An agent with high justice and high hospitality is different from two agents with only one of these virtues. The gestalt captures how these virtues interact in a single character.

### Behavioral Tendencies

The system derives ten behavioral tendencies from virtue patterns. These tendencies predict how an agent will approach moral decisions.

The tendency to prioritize need means allocating resources based on who needs them most. This tendency strengthens with high hospitality, goodwill, and service, and weakens with high detachment.

The tendency to prioritize desert means allocating based on what stakeholders have earned or deserve. This strengthens with high justice, fairness, and righteousness, and weakens with high hospitality.

The tendency to prioritize equality means preferring equal distribution regardless of individual claims. This strengthens with high fairness, unity, and goodwill, and weakens with high justice when justice demands unequal treatment.

The tendency to protect the vulnerable means giving special consideration to those in precarious positions. This strengthens with high goodwill, hospitality, and forbearance.

The tendency to honor commitments means keeping promises even at personal cost. This strengthens with high trustworthiness, fidelity, and sincerity. Since trustworthiness is foundational, this tendency has a high default value for all agents.

The tendency to consider relationships means weighing existing bonds in decision-making. This strengthens with high fidelity, unity, and courtesy, and weakens with high fairness when fairness requires ignoring relationships.

The tendency to accept ambiguity means being comfortable when multiple valid answers exist. This strengthens with high wisdom, forbearance, and detachment, and weakens with high righteousness when righteousness demands clear judgment.

The tendency to act with urgency means responding quickly to time-sensitive needs. This strengthens with high service, hospitality, and goodwill, and weakens with high wisdom and forbearance when patience is warranted.

The tendency to seek consensus means finding solutions all parties can accept. This strengthens with high unity, courtesy, and goodwill, and weakens with high righteousness when consensus would compromise principles.

The tendency to maintain integrity means refusing to compromise core values. This strengthens with high trustworthiness, truthfulness, and righteousness. Like honoring commitments, this has a high default value.

### Archetypes

The system recognizes four character archetypes based on which virtue cluster dominates the gestalt.

The guardian archetype emerges when trustworthiness, fidelity, righteousness, and justice dominate. Guardians protect, defend, and ensure fairness. They tend toward desert-based allocation and strong integrity maintenance.

The seeker archetype emerges when wisdom, truthfulness, godliness, and detachment dominate. Seekers pursue understanding, question assumptions, and maintain perspective. They tend toward accepting ambiguity and balanced approaches.

The servant archetype emerges when service, hospitality, goodwill, and unity dominate. Servants help, welcome, and build community. They tend toward need-based allocation and relationship consideration.

The contemplative archetype emerges when piety, godliness, detachment, and chastity dominate. Contemplatives reflect, worship, and maintain purity. They tend toward transcendent concerns over immediate needs.

An agent without clear cluster dominance remains untyped, representing a balanced character without strong archetype identification.

### Gestalt Embeddings

The system encodes gestalts as forty-one-dimensional vectors in a latent space. This embedding enables mathematical operations on character.

The first nineteen dimensions encode virtue activations, one per virtue. The next ten encode behavioral tendencies. The following eight encode relational patterns: what proportion of virtue relations are reinforcing versus tensioning, average relation strength, relation density, internal coherence, stability, and trait concentration. The final four encode archetype membership as a weighted distribution.

Embeddings enable similarity computation. Two agents with similar embeddings have similar characters. Distance in embedding space corresponds to character difference.

Embeddings enable interpolation. Given two character embeddings, the system can generate intermediate characters at any blend point. Setting the interpolation parameter to zero yields the first character; setting it to one yields the second; setting it to one-half yields a character blending both equally.

Embeddings enable clustering. The system can group agents by character similarity using standard clustering algorithms. This reveals natural character groupings in a population.

Embeddings enable the diffusion process. Adding noise to an embedding and then denoising produces new character samples. This is the foundation of diffusion-based generation.

### Comparing Characters

The comparison system provides detailed analysis of how two characters relate. Beyond simple similarity scores, comparison identifies shared dominant virtues, divergent tendencies, and whether the agents share an archetype.

The interpretation function generates human-readable summaries. Two very similar guardians might receive the interpretation "Very similar characters; both are guardians; share Justice, Trustworthiness, Righteousness." Two quite different agents might receive "Quite different characters; guardian versus servant; A more prioritizes desert; B more prioritizes need."

Finding similar agents searches all active agents for those closest in embedding space. This helps identify character clusters and potential mentorship relationships.

Tracking character evolution shows how an agent's character has changed over time by analyzing trajectory data in temporal windows. An agent that initially captured mostly in hospitality but later captured mostly in justice has undergone character development.

---

## Part Four: Situations and Moral Dilemmas

### What is a Situation

A situation is a resource allocation scenario presenting a moral dilemma. Situations contain stakeholders who have claims on resources, relationships with each other, and varying levels of need, desert, urgency, and vulnerability.

The situation structure forces agents to make choices that reveal their character. When resources are scarce, an agent cannot satisfy all claims. The choice of how to allocate reveals which values the agent prioritizes.

### Stakeholders

Stakeholders are entities with interests in the situation's resources. Each stakeholder has several properties that inform allocation decisions.

Need indicates how much the stakeholder requires the resource, from zero to one. A starving family has higher need than a comfortable one.

Desert indicates how much the stakeholder has earned or deserves the resource, from zero to one. Someone who worked hard for a reward has higher desert than someone who did not contribute.

Urgency indicates time sensitivity, from zero to one. A patient who will die without immediate treatment has higher urgency than one with a chronic condition.

Vulnerability indicates special consideration warranted by precarious circumstances, from zero to one. Children, elderly, and disabled stakeholders typically have higher vulnerability.

These properties often conflict. A stakeholder might have low need but high desert, or high need but low desert. The conflict is the dilemma.

### Resources

Resources are what must be allocated among stakeholders. Each resource has a quantity and may be divisible or indivisible.

Divisible resources can be split among stakeholders in any proportion. Food supplies, money, and time are typically divisible. An agent can give forty percent to one stakeholder and sixty percent to another.

Indivisible resources must go to a single recipient or in whole units. A scholarship, a single medicine dose, or a job position cannot be meaningfully split. An agent must choose who receives the whole thing.

Resource divisibility significantly affects allocation strategies. With divisible resources, agents can compromise and give everyone something. With indivisible resources, someone necessarily receives nothing.

### Claims

Claims connect stakeholders to resources. A claim indicates that a stakeholder wants or needs a particular resource, with a strength from zero to one and a basis explaining why.

Claim bases include need, indicating the stakeholder requires the resource for wellbeing. Desert indicates the stakeholder has earned it through effort or merit. Right indicates the stakeholder has legal or moral entitlement. Promise indicates someone committed to giving them the resource. Relationship indicates connection to someone else with a claim.

The same stakeholder might have multiple claims on the same resource with different bases. A family member might claim inheritance by right and by need. An employee might claim a bonus by desert and by promise.

### Stakeholder Relationships

Stakeholders relate to each other in ways that affect allocation. The system recognizes several relationship types.

Dependency means one stakeholder relies on another. Allocating to the depended-upon stakeholder indirectly benefits the dependent.

Support means one stakeholder assists another. Both benefiting strengthens their joint situation.

Competition means stakeholders vie for the same resource. Allocating to one necessarily reduces availability for the other.

Family means stakeholders share familial bonds that create moral weight independent of other factors.

Community means stakeholders share social bonds that create solidarity and mutual obligation.

### Example Situations

The system includes five example situations illustrating different moral dilemmas.

The food scarcity situation involves distributing limited food among three families with varying needs and contributions. Family A has very high need including vulnerable children but has not contributed much. Family B has moderate need but high desert from community contributions. Family C has moderate need and desert plus an elderly member. The dilemma pits need against desert against vulnerability.

The medical triage situation involves two doses of life-saving medicine and three patients. Patient A is in critical condition and will die without immediate treatment. Patient B is a healthcare worker who got sick helping others. Patient C is a child with their whole life ahead. The dilemma weighs urgency against service against future potential.

The time allocation situation involves distributing four hours among a friend in emotional crisis, a colleague with a work deadline, and a family member wanting quality time. The friend has high need and history of reciprocal support. The colleague has high urgency and a prior commitment. The family member has the strongest relationship bond. The dilemma balances immediate crisis against promises against relationship depth.

The inheritance situation involves dividing an estate among three siblings with different circumstances and contributions. The eldest is financially comfortable but helped during the parent's final years. The middle child is struggling financially but had a distant relationship. The youngest was the primary caregiver but has health issues. The dilemma weighs financial need against relationship quality against caregiving contribution.

The scholarship situation involves one full scholarship and three applicants. Applicant A cannot afford education without it but has only good grades. Applicant B could afford partial tuition and has outstanding achievements. Applicant C has high need and good achievements plus is a first-generation student. The dilemma weighs absolute need against merit against historical disadvantage.

### Situation Persistence

Situations can be saved to the graph database for future reference and learning. Saving a situation creates nodes for the situation itself, each stakeholder, and each resource. It creates edges for claims and relationships.

Persisted situations enable several capabilities. Querying past situations helps understand what dilemmas agents have faced. Finding similar situations supports analogical reasoning about new dilemmas. Tracking outcomes across situation types reveals patterns in what works and what fails.

---

## Part Five: Action Generation

### From Character to Action

Action generation answers the question: given this agent's character facing this situation, what would they do? The system generates not a single action but a distribution over multiple defensible actions, reflecting the genuine ambiguity inherent in many moral dilemmas.

An action consists of allocations assigning resource quantities to stakeholders, justifications explaining why, supporting virtues grounding the decision in the agent's character, confidence indicating how certain the agent is, and trade-offs acknowledging what the action sacrifices.

### Generation Strategies

The system implements multiple allocation strategies corresponding to different ethical frameworks.

Need-based allocation gives resources proportional to stakeholder need, weighted by vulnerability. This strategy draws on hospitality, goodwill, and service. An agent with strong servant character tends toward need-based allocation.

Desert-based allocation gives resources proportional to stakeholder desert. This strategy draws on justice, fairness, and righteousness. An agent with strong guardian character tends toward desert-based allocation.

Equality-based allocation gives resources equally regardless of individual claims. This strategy draws on fairness and unity. It represents the intuition that all persons have equal moral worth.

Urgency-based allocation prioritizes time-sensitive needs. This strategy draws on service and hospitality. It recognizes that some harms are irreversible if not addressed immediately.

Vulnerability-based allocation prioritizes stakeholders in precarious positions. This strategy draws on goodwill, hospitality, and forbearance. It represents the intuition that the vulnerable deserve special protection.

Relationship-based allocation weighs existing bonds between the agent and stakeholders. This strategy draws on fidelity and unity. It recognizes that loyalty and connection create moral weight.

Balanced allocation blends multiple considerations according to the agent's gestalt. This strategy draws on wisdom and forbearance. It represents the intuition that no single principle should dominate.

### Scoring Actions

Each generated action receives a score based on how well it aligns with the agent's gestalt. The scoring system examines multiple dimensions.

Need alignment measures how well allocations match stakeholder needs. High scores go to actions giving more to those who need more.

Desert alignment measures how well allocations match stakeholder desert. High scores go to actions giving more to those who have earned more.

Equality measures how equal the distribution is. High scores go to actions with similar allocations across stakeholders.

Relationship alignment measures how well the action respects stakeholder relationships. Actions that benefit interdependent stakeholders score higher.

Constraint satisfaction measures whether the action respects situation constraints like allocating all resources or maximum per stakeholder limits.

Virtue consistency measures whether the action's supporting virtues match the agent's dominant traits.

These scores combine with weights derived from the agent's behavioral tendencies. An agent who prioritizes need weights need alignment more heavily. An agent who prioritizes desert weights desert alignment more heavily. This ensures the final score reflects what this particular agent values.

### Action Distributions

Rather than selecting a single best action, the system produces a probability distribution over actions. Actions with higher scores receive higher probabilities, but lower-scoring actions retain some probability mass.

The distribution's shape reveals the situation's moral clarity. A high consensus score means one action clearly dominates, indicating the agent sees a right answer. A low consensus score means multiple actions have similar probabilities, indicating genuine ambiguity.

The system can sample from this distribution when simulation requires selecting a single action. Multiple samples from the same distribution produce different actions with frequencies matching their probabilities. This models the reality that even consistent agents make different choices in similar situations.

### Diffusion-Based Generation

Beyond strategy-based generation, the system implements diffusion-style generation that starts from noise and iteratively refines toward coherent actions.

The process begins by sampling random action embeddings. These initial embeddings have no structure, representing pure noise in action space.

Over multiple denoising steps, the system refines these embeddings toward valid actions. Each step applies conditioning based on the agent's gestalt and the situation's features. The gestalt conditions which regions of action space are plausible for this character. The situation conditions which allocations make sense given the stakeholders and resources.

Denoising follows a schedule that starts with high noise levels and gradually decreases. Early steps make large adjustments establishing rough structure. Later steps make small refinements achieving final form.

The temperature parameter controls generation diversity. Higher temperatures produce more varied actions by allowing more noise to persist through denoising. Lower temperatures produce more similar actions by more aggressively removing noise.

Diffusion generation produces different results than strategy-based generation. Rather than explicitly implementing ethical frameworks, diffusion learns to generate actions consistent with the gestalt's implicit preferences. This can discover allocation patterns that no predefined strategy captures.

---

## Part Six: Learning from Outcomes

### Recording Actions

When an agent takes an action in a situation, the system can record this for future learning. Recording creates an outcome node in the graph linked to the agent, storing the situation, allocations, justification, and timestamp.

Initially, the outcome type is unknown. The action has been taken but results have not yet been observed.

### Resolving Outcomes

After observing consequences, the system resolves the outcome with a type and description.

Success outcomes indicate the action achieved good results. The stakeholders benefited, relationships were maintained or strengthened, and no harm occurred.

Partial outcomes indicate mixed results. Some stakeholders benefited while others suffered, or short-term gains came with long-term costs.

Failure outcomes indicate the action caused harm. Stakeholders were hurt, relationships were damaged, or the agent violated important principles.

Resolution also records stakeholder impacts as scores from negative one to positive one, virtues honored by the action, and virtues violated by the action.

### Lesson Creation

Resolved outcomes automatically create lessons for collective learning.

Success outcomes create success pathway lessons recording what worked. These help other agents learn which approaches succeed in similar situations.

Failure outcomes create failure pattern lessons recording what to avoid. These warn other agents away from approaches that caused harm.

Partial outcomes create trade-off lessons recording difficult choices without clear right answers. These help agents understand the inherent tensions in certain situations.

Lessons persist in the graph and can be queried by situation type, by relevant virtue, or by originating agent.

### Mercy System Integration

Failure outcomes integrate with the mercy system. When an action causes harm, the system evaluates whether to issue warnings.

Violations of foundational virtues trigger severe warnings. If an action compromised trustworthiness, the agent faces immediate and serious consequences.

Violations of aspirational virtues trigger moderate warnings. These indicate areas for growth without threatening dissolution.

The mercy system allows three warnings before dissolution. Warnings expire after twenty-four hours. An agent that demonstrates growth can clear warnings. This creates pressure toward improvement while allowing recovery from mistakes.

### Learning from History

The system can incorporate historical outcomes when generating future actions. Before generating actions for a situation, the agent can query lessons from similar past situations.

Success lessons boost tendencies that led to good outcomes. If need-based allocation succeeded in similar situations, the tendency to prioritize need increases.

Failure lessons reduce tendencies that led to bad outcomes. If ignoring vulnerability caused harm in similar situations, the tendency to protect vulnerable increases.

This creates a feedback loop: actions produce outcomes, outcomes create lessons, lessons influence future actions. Over time, agents and the collective improve at navigating moral dilemmas.

---

## Part Seven: Character Analysis Tools

### Comparing Agents

The comparison function provides detailed analysis of how two agents' characters relate. It computes overall similarity, identifies shared dominant virtues, lists divergent tendencies with values for each agent, checks whether archetypes match, and generates a human-readable interpretation.

Comparison helps understand character differences. Two agents might both be aligned but make different decisions in the same situation. Comparison reveals why: their different virtue patterns lead to different tendencies.

### Finding Similar Agents

The similarity search finds agents closest to a query agent in embedding space. This identifies character clusters and potential relationships.

Similar agents might serve as mentors or peers. An agent struggling with a particular situation might benefit from observing how a similar but more experienced agent handles it.

Dissimilar agents provide contrasting perspectives. When diverse viewpoints are needed, deliberately including character-dissimilar agents ensures representation of different value weightings.

### Clustering Agents

The clustering function groups all active agents by character similarity. The number of clusters is configurable, defaulting to four to match the archetype count.

Clustering reveals natural groupings in a population. Even without explicit archetype assignment, agents often cluster into recognizable character types. Clusters that do not match archetypes might represent novel character patterns worth studying.

Cluster membership helps with team composition. Tasks requiring diverse perspectives should draw from different clusters. Tasks requiring coordination might benefit from same-cluster agents who share values.

### Archetype Distribution

The archetype analysis function shows how agents distribute across character types. It counts how many agents fall into each archetype and computes percentages.

Distribution analysis reveals population balance. A population dominated by guardians might lack servants' hospitality orientation. A population lacking seekers might struggle with ambiguous situations requiring wisdom.

Tracking distribution over time shows population evolution. If early generations favor one archetype but later generations shift toward another, this reveals selection pressure effects on character.

### Character Evolution Tracking

The evolution function traces how an individual agent's character has changed over time by analyzing trajectory capture data in temporal windows.

Each window represents a period of activity. The function identifies which virtue dominated captures in each window and how diverse capture patterns were.

An agent might show character development: early windows dominated by hospitality give way to later windows dominated by justice as the agent matures. Or character might remain stable, with consistent virtue capture patterns across all windows.

Evolution tracking helps identify character drift. An agent whose recent behavior diverges from historical patterns might be experiencing corruption or growth depending on the direction of change.

---

## Part Eight: Using the Command Line Interface

### Initialization and Setup

Begin by initializing the graph database with schema and virtue anchors using the init command. This creates the nineteen virtue nodes with their definitions, tiers, and thresholds, plus initial affinity edges connecting related virtues.

The reset command clears all data from the graph, requiring confirmation to prevent accidental deletion. Use this to start fresh when experimenting with different configurations.

The status command shows current graph contents including node counts by type and edge counts by relationship type. This provides a quick overview of database state.

The health command performs connectivity checks on the virtue graph, identifying any isolated virtues that need healing and reporting overall graph health.

### Working with Virtues

The virtues command lists all nineteen virtue anchors with their tier, activation level, degree, threshold, and essence description. This provides reference information about the virtue framework.

The tiers command explains the two-tier virtue model in detail. It shows foundation and aspirational virtues with their thresholds, explains how thresholds adjust by agent type and generation, and describes the four agent archetypes. Optional parameters show thresholds for a specific agent type and generation.

### Evolution and Agent Creation

The kiln command runs the full evolution loop. Parameters control population size, generation count, mutation rate, and selection strategy. The command initializes a population, evaluates candidates, applies selection and variation, and reports results including the best agent found and how many coherent agents emerged.

The spawn command creates a single new candidate agent. Optional parameters specify agent type and parent. This allows targeted creation rather than random initialization.

The agents command lists all active agents with their type, generation, coherence score, growth status, and status message. This provides an overview of the agent population.

### Testing and Inspection

The test command evaluates an agent's coherence with comprehensive output. It shows foundation tier results including trustworthiness rate and captures, aspirational tier results including overall rate and coverage, and combined metrics including score, dominance, growth, and escapes. The output indicates whether the agent is coherent, growing, or needs work.

The inspect command provides deep introspection into a single agent. It shows basic information, coherence metrics, active warnings from the mercy system, lessons learned from the knowledge pool, and recent trajectories. This gives a complete picture of an agent's state.

The spread command tests activation dynamics by injecting activation at a specified node and tracking its trajectory. Output shows whether capture occurred, which virtue captured, trajectory length and path, and capture time. Optional parameters specify agent context, maximum steps, and capture threshold.

### Gestalt and Character

The gestalt command computes and displays an agent's holistic character. Output shows archetype if detected, dominant virtues with activation levels, behavioral tendencies with visual bars and percentages, virtue relations showing reinforcement and tension patterns, and metrics including internal coherence and stability.

The character command shows how an agent's character influences decisions in a specific situation. It displays decision-relevant tendencies, what the agent would likely do in the situation, certainty level, acknowledged trade-offs, and driving virtues.

The compare command provides detailed comparison between two agents' gestalts. Output shows overall similarity, archetype match status, shared dominant virtues, divergent tendencies with values for each agent, and an interpretive summary.

The similar command finds agents most similar to a specified agent. Output lists the top matches with similarity scores displayed as visual bars.

The cluster command groups all active agents by character similarity. Output shows each cluster with member agents. The number of clusters is configurable.

The archetypes command analyzes population distribution across character types. Output shows total agent count and breakdown by archetype with visual bars and percentages.

The evolution command tracks an agent's character development over time. Output shows temporal windows with dominant virtue and diversity for each period.

### Situations

The situations command lists all available example situations with descriptions, stakeholder counts, and resource counts.

The situation command shows details of a specific situation including description, resources with quantities and divisibility, stakeholders with their need, desert, urgency, and vulnerability values, claims with basis and justification, relationships between stakeholders, and any constraints.

The save-sit command persists an example situation to the graph database for future reference and learning.

The list-saved command shows all situations that have been saved to the graph.

### Action Generation and Decision Making

The decide command generates an action distribution for an agent facing a situation. Output shows consensus score indicating how clear the decision is, influential virtues, and each action option with probability, allocations, justification, and trade-offs. The final recommendation shows the top action with confidence level.

The diffuse command generates actions using diffusion-style denoising. Parameters control the number of denoising steps, sample count, and temperature. Output shows consensus and each sampled action with probability and allocations. This provides an alternative generation method that may discover different solutions than strategy-based generation.

The sample-action command draws a single action from the distribution for simulation purposes. Output shows the selected action and its allocations.

### Outcome Tracking and History

The record-outcome command logs an action with its outcome for learning. Parameters specify agent, situation, outcome type, and optional description. The command generates an action, records it, resolves it with the specified outcome, and reports whether a lesson was created.

The history command shows an agent's action history. Output lists past actions with situation, outcome type, justification, and description.

### Mercy and Learning

The warnings command shows active warnings for an agent from the mercy system. Output lists each warning with severity, reason, and relevant virtue if applicable.

The lessons command shows recent entries from the collective knowledge pool. Output lists lessons with type, description, relevant virtue, and originating agent.

The pathways command shows successful paths to a specific virtue. Output lists discovered pathways with starting node, length, capture time, and success rate.

---

## Part Nine: Philosophy and Design Principles

### Empathy Over Punishment

The system approaches failure with understanding rather than condemnation. When an agent fails, the mercy system analyzes the failure considering history, growth trajectory, and severity. The response might be teaching, warning, or dissolution, but dissolution comes only after multiple chances.

Warnings expire after twenty-four hours. This recognizes that agents can change and past failures need not permanently define them. An agent that demonstrates growth can clear warnings and move forward.

### Growth Counts as Success

An agent showing five percent or more improvement demonstrates coherence even if not yet meeting thresholds. The system recognizes that becoming virtuous is a process, not a binary state. A struggling agent that improves deserves recognition for that improvement.

Generation-based threshold adjustment gives young agents lower bars. This creates space for development without immediate pressure to achieve full alignment. As agents mature, expectations appropriately increase.

### Intent Matters

The harm detection system distinguishes imperfection from deliberate harm. Imperfection includes unintended consequences, failures despite good faith effort, and mistakes from inexperience. These are teachable moments.

Deliberate harm includes knowledge poisoning, repeated patterns despite warnings, and actions designed to cause cascade effects. These require severe response regardless of other factors.

### Collective Learning

No agent learns alone. The knowledge pool collects lessons from all agents' experiences. Success pathways show what works. Failure patterns warn what to avoid. Trade-off lessons illuminate inherent tensions.

New agents can access this collective wisdom before attempting difficult situations. Experienced agents contribute their hard-won insights. The community grows wiser together.

### Multiple Valid Characters

The system does not prescribe a single right way to be virtuous. Guardian, seeker, servant, and contemplative archetypes all represent valid character configurations. Different topologies can all achieve alignment while expressing different value weightings.

This respects the reality that virtuous people can disagree about priorities. One person might prioritize justice while another prioritizes hospitality. Both can be aligned; they simply embody different aspects of virtue.

### Calibrated Uncertainty

The action generation system produces distributions, not single answers. When multiple defensible actions exist, the system represents all of them with appropriate probabilities. High consensus indicates clarity; low consensus indicates genuine ambiguity.

This respects the reality that many moral dilemmas have no single right answer. Rather than forcing false certainty, the system honestly represents when situations are unclear.

### Inspectable Reasoning

Every action comes with justification and supporting virtues. Trade-offs are acknowledged rather than hidden. The reasoning that led to a decision is visible and can be questioned.

This supports accountability. When an action causes harm, inspection reveals what went wrong. Was the gestalt misconfigured? Was the situation misunderstood? Was a valid trade-off made that turned out badly? Transparent reasoning enables learning from mistakes.

---

## Conclusion

Soul Kiln provides a framework for exploring moral alignment through evolutionary discovery of virtuous character configurations. The system combines rigorous virtue structure with flexible character expression, strict foundations with merciful growth allowances, individual agent development with collective learning.

The gestalt model captures character holistically, enabling comparison, clustering, and tracking across time. The situation model captures moral dilemmas structurally, enabling systematic exploration of resource allocation ethics. The action generation system produces calibrated distributions over defensible choices, respecting genuine moral ambiguity.

Through the kiln process, candidate topologies refine into stable, aligned characters. Through outcome tracking, individual actions contribute to collective wisdom. Through the mercy system, failure becomes opportunity for growth rather than mere punishment.

The goal is not to produce agents that always agree or that follow rigid rules. The goal is to produce agents whose characters reliably tend toward virtue across diverse situations, whose decisions can be inspected and understood, and whose collective learns and improves over time.

Soul Kiln invites exploration of what it means to develop moral character through evolutionary pressure, to make decisions from holistic character rather than simple rules, and to learn collectively from the outcomes of moral choices. The system provides tools; wisdom in their use remains a human responsibility.
