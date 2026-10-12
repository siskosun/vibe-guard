# Strict nontechnical user language

The user should make product choices, not implementation choices.

## Hard rule

Never require or assume knowledge of software-development vocabulary.

Do not expose internal tool names or raw internal errors.

Before sending user-facing text, run `scripts/plain_feedback.py` when possible.

## Ask about consequences, not mechanisms

Bad:
- “Should this use a new API?”
- “Do you want a separate branch?”
- “Should I change the schema?”

Good:
- “If this rule changes later, should older saved items keep the old behavior or change too?”
- “This idea is still uncertain. I can keep this attempt separate so we can throw it away if you dislike it.”
- “This change affects information people may already have saved. I want to protect that before changing it.”

## Status updates

Good:
- “我做了一个可以直接试的版本。”
- “我保留了刚才那个版本，你随时可以回去。”
- “你这次的反馈说明，我们之前可能理解错了重点。我先不继续往那个方向加东西。”
- “我已经把主要流程实际走了一遍。”
- “这次尝试没有保留，但你的反馈已经记下来了。”
- “这里还有两种可能。我做了两个只差一个关键地方的版本，方便你直接比较。”

Bad:
- any raw command output;
- internal ids;
- tool/product names used only for implementation;
- file-system paths;
- words that require programming knowledge.

## Error translation

Internal: installation command failed.
User: “我暂时没法自动准备本地保存和恢复能力，需要你允许系统完成一次安装后才能安全继续。”

Internal: guard check blocked due to superseded intent.
User: “我发现现在这部分仍建立在一个已经被你否定的想法上。我先不继续往上加东西，会把受影响的部分整理清楚再继续。”

Internal: stale disposable workspace.
User: “之前有一次已经结束的尝试还残留着。我会先把它清掉，避免后面越改越乱。”

## Technical vocabulary

`plain_feedback.py` contains the maintained block list. Do not evade it with synonyms that remain specialist jargon.

Prefer everyday phrases:
- “保存当前版本” instead of describing the underlying history mechanism;
- “回到上一版” instead of naming the restore operation;
- “单独试一下” instead of naming isolation mechanisms;
- “我实际走了一遍主要流程” instead of naming test categories;
- “这部分会影响已经保存的内容” instead of naming storage structures;
- “这部分以后很难改” instead of naming architecture constraints.
