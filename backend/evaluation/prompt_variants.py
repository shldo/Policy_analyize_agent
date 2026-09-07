"""Development experiments only; never imported by application prompts."""

COMPLETENESS_V1 = """Answer quality checks:
- Answer every part of the user's question directly and concisely.
- When describing a requirement, preserve the responsible party, concrete action
  and deliverable, applicable scope, trigger, deadline and relevant exceptions
  that the supplied excerpts establish. Include implementation details needed
  to carry out that requirement, not just its purpose.
- Preserve the source's strength and scope: do not turn may/should into must,
  or add only/always/universal restrictions that the excerpts do not establish.
- Do not add unnecessary claims. If you add an explanation, retain any source
  conditions or exceptions that affect that explanation.
- Cite the supplied excerpt that supports each substantive claim. Check that
  the citation supports the claim itself, not merely a related topic.
- If evidence is insufficient, state the limitation of the supplied material;
  do not infer that a fact does not exist. Ask for clarification only if the
  question is ambiguous in a way that changes what should be retrieved.
Before responding, check completeness and support internally; output only the
answer, not the checklist or hidden reasoning.
"""


def apply_variant(system_prompt, variant):
    if variant == "baseline":
        return system_prompt
    if variant == "completeness-v1":
        return system_prompt + "\n\n" + COMPLETENESS_V1
    raise ValueError("Unknown generation prompt variant")
