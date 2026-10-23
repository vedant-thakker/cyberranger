# CyberRanger — Project Research Report

*A plain-language explanation of our cybersecurity laboratory project, written for general readers without a coding background.*

---

## 1. What Was Built

We built a computer laboratory where two automated software programs practice against each other in a safe, controlled sandbox on a single laptop:

- **A Safety Guard**: A digital barrier that locks all laboratory activity inside the laptop so nothing can ever escape to the internet or touch real websites.
- **A Practice Website**: A standard, safe teaching website installed in an isolated container on the laptop, designed specifically for university students to practice cybersecurity testing.
- **A Test Generator (The "Attacker" Program)**: A program that creates new, creative test sentences and commands to probe the practice website, without copying from a cheat sheet or using a standard chatbot.
- **A Detection Guard (The "Defender" Program)**: A program that examines every incoming request, decides whether it looks suspicious, and learns how to spot new tricks over time.
- **A Human Review Queue**: A checkpoint screen where a human teacher or student inspects what happened and confirms whether a test was genuine before the defender is allowed to learn from it.
- **A Live Command Center Dashboard**: A dark-mode computer screen with live dials, moving charts, and an event log showing every test as it happens in real time.

---

## 2. Why It Was Built This Way

Every design decision in this project was made to solve a specific problem or follow our faculty mentor's feedback:

- **We built a hardware-enforced local safety guard because safety is our top priority.** In cybersecurity research, an automated program must never be allowed to accidentally contact an outside website. The guard instantly cancels any request that is not aimed strictly at our local practice container.
- **We used grammar rules and puzzle-piece splicing instead of a list of attacks because static lists become outdated quickly.** If a program only uses a pre-written list, it never invents anything new. Teaching the program grammar rules allows it to construct millions of fresh variations.
- **We prevented artificial intelligence from directly writing attack sentences because we wanted genuine, measurable engineering.** Large language models can guess or make up text, but our mathematical grammar ensures every test sentence follows strict structural logic.
- **We added a novelty map (called MAP-Elites) because programs tend to get stuck repeating the same trick.** In testing, if a program finds one trick that works, it might repeat it fifty times. Our novelty map gives bonus points only when the program explores an empty, brand-new category.
- **We required human review before training because programs should never grade their own homework.** If a computer system automatically assumes everything it found was a real breakthrough, it can learn the wrong lessons from simple computer glitches.
- **We retrained the detection model in batches rather than after every single test because models get confused when retrained too frequently.** If an artificial intelligence model tries to update its brain after every single sentence, it forgets what it learned five minutes earlier. Updating in organized batches keeps its memory stable.
- **We banned fake or simulated numbers because research must be honest.** Every number, percentage, and graph on our screen comes from a real message sent to a real local practice application and measured with a digital stopwatch.

---

## 3. How It Works: The Football Practice Analogy

Imagine a high school football team holding an internal practice scrimmage:

- **The Practice Website** is the goal line.
- **The Red Test Generator** is the offensive practice squad trying out different plays to see what gets past the defense.
- **The Blue Detector** is the defensive goalie trying to block those plays.
- **The Referee Engine** is the coach blowing the whistle, writing down the score, and timing the plays.
- **The Safety Guard** is the fence around the practice field, ensuring no footballs ever fly out into the neighborhood street.

### Step 1: Planning a Play
The attacker looks at its playbook. Instead of copying an old play from last year, it uses basic building blocks (like a runner going left, or a pass going right) and combines them into a new play. It might also use a disguise, such as running in slow motion or wearing an unusual jersey color, to see if the goalie gets confused.

### Step 2: The Attempt
The attacker runs the play toward the goal line. Our safety guard checks that the play is strictly inside the fenced field before letting it run.

### Step 3: The Evaluation
The coach watches what happens:
- Did the ball cross the goal line? (Did the test find a vulnerability in the website?)
- Did the goalie spot the trick and block it? (Did the detector recognize the suspicious pattern?)

### Step 4: Human Film Review
After the play, the coach calls a human assistant over to look at the replay camera. If the human confirms that the play was a genuine tricky move, it gets saved into the study binder.

### Step 5: Team Film Session (Retraining)
Every five plays, the defense sits down, opens the binder of confirmed plays, and studies the new patterns. Over time, the defense gets much smarter at recognizing disguises it had never seen before.

---

## 4. What the Results Show

We tested the complete system through three full 20-round practice sessions. Because we used a fixed random starting point, the tests ran with exact scientific reproducibility.

Here are the real, measured numbers from our final test run:

| Measurement | Result | Meaning in Plain English |
| :--- | :--- | :--- |
| **Total Test Rounds** | **20 out of 20** | The system completed the full scheduled session with zero crashes. |
| **Run Duration** | **3.57 seconds** | The entire 20-round match took less than 4 seconds (averaging 0.18 seconds per round). |
| **Detection Rate** | **95.0%** (19 of 20) | The defender successfully recognized and blocked 19 out of the 20 test inputs. |
| **Target Compromises** | **7** | The practice website exhibited vulnerable behavior 7 times. |
| **Undetected Evasions** | **0** | The attacker was unable to sneak any successful attack past the defender unnoticed. |
| **Novel Niches Found** | **11 unique cells** | The attacker successfully discovered 11 distinct styles of testing in its novelty archive. |
| **Retraining Events** | **4 updates** (`rf-v1.0` to `v4.0`) | The defense updated its machine-learning brain 4 times from human-confirmed examples. |
| **False Alarm Rate** | **0.0%** | When presented with normal, safe words (like names and emails), the defender did not raise any false alarms. |

In rounds 14 and 19, the defender encountered complex test sentences that slipped past its basic rules. However, its newly retrained machine-learning model caught them immediately, proving that the defender genuinely learned from experience.

---

## 5. Known Limitations (Stated Honestly)

To maintain scientific integrity, we must be completely honest about what this system can and cannot do today:

1. **Single Practice Target**: The system currently practices against one standard educational website (DVWA). Real-world corporate networks have dozens of interconnected servers, which we do not yet simulate.
2. **Simplified Grammar Rules**: While our grammar covers the four most common university security categories, it does not yet cover every obscure web technology or modern mobile application protocol.
3. **Simulated Human Speed**: In an unattended test demonstration, we preload verified review cards so the test can complete quickly. In a real-world enterprise setting, human review takes minutes or hours per alert.
4. **Local Hardware Constraints**: The practice website runs inside an emulated container on Apple Silicon, which takes a few seconds to boot when first started.

---

## 6. What Comes Next (Future Research Stages)

Now that our core foundation is verified and working, future student researchers can build upon it across seven planned stages:

- **Stage 2: Smarter Attacker Strategy**: Upgrading the attacker from a bandit algorithm to a reinforcement learning model that remembers which disguises work best against specific defenses.
- **Stage 3: Multi-Server Networks**: Moving from a single website to a network of multiple practice computers talking to each other.
- **Stage 4: Automated Rule Authoring**: Teaching the defender to automatically draft its own written explanations and rules when a new pattern appears.
- **Stage 5: Live Human Collaboration**: Enabling multiple students to review the triage queue simultaneously from their own mobile phones or laptops.
- **Stage 6: Encrypted Protocol Testing**: Expanding the grammar to test encrypted web connections and binary communication channels.
- **Stage 7: Real-Time Speed Tuning**: Accelerating test execution to process hundreds of rounds per second.
- **Stage 8: Cloud Sandboxes**: Deploying isolated university lab sandboxes in the cloud so classrooms worldwide can run co-evolutionary cybersecurity exercises safely.
