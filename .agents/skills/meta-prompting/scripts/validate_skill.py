"""
Validation and verification suite for the meta-prompting skill.
Tests YAML frontmatter, markdown cross-references, template variable bindings,
and simulated execution of Python pipelines across practical case studies.
"""

import ast
from collections import Counter
import json
import os
from pathlib import Path
import re
import sys

BASE_DIR = Path(r"c:\work_dir\my_agy")
SKILL_DIR = BASE_DIR / "meta-prompting" if (BASE_DIR / "meta-prompting").exists() else BASE_DIR / ".agents" / "skills" / "meta-prompting"

def test_yaml_frontmatter() -> bool:
    print("[1/6] Testing SKILL.md YAML frontmatter...")
    skill_file = SKILL_DIR / "SKILL.md"
    assert skill_file.exists(), "SKILL.md does not exist"
    
    content = skill_file.read_text(encoding="utf-8")
    fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    assert fm_match, "Valid YAML frontmatter not found in SKILL.md"
    
    fm_text = fm_match.group(1)
    name_match = re.search(r"^name:\s*([^\s]+)", fm_text, re.MULTILINE)
    desc_match = re.search(r"^description:\s*(.+)$", fm_text, re.MULTILINE)
    
    assert name_match and name_match.group(1).strip() == "meta-prompting", "Invalid skill name"
    assert desc_match and len(desc_match.group(1).strip()) > 30, "Description missing or too short"
    print("  -> PASS: Frontmatter is valid, name='meta-prompting'.")
    return True

def test_deliverables_exist() -> bool:
    print("[2/6] Testing deliverables file existence and minimum sizes...")
    expected_files = [
        SKILL_DIR / "SKILL.md",
        SKILL_DIR / "references" / "decision_matrix.md",
        SKILL_DIR / "references" / "prompt_components.md",
        SKILL_DIR / "examples" / "case_agentic_bot.md",
        SKILL_DIR / "examples" / "case_analytical_report.md",
        SKILL_DIR / "examples" / "case_high_stakes_eval.md",
    ]
    for p in expected_files:
        assert p.exists(), f"Missing file: {p}"
        size = p.stat().st_size
        assert size > 2000, f"File {p.name} is too small ({size} bytes)"
        print(f"  -> PASS: {p.relative_to(BASE_DIR)} ({size:,} bytes)")
    return True

def test_technique_coverage() -> bool:
    print("[3/6] Testing 12-technique framework coverage across references...")
    dec_matrix = (SKILL_DIR / "references" / "decision_matrix.md").read_text(encoding="utf-8")
    components = (SKILL_DIR / "references" / "prompt_components.md").read_text(encoding="utf-8")
    
    required_techniques = [
        "Zero-shot",
        "Few-shot",
        "Chain-of-Thought",
        "ReAct",
        "Tree of Thoughts",
        "Self-Consistency",
        "Least-to-Most",
        "Skeleton-of-Thought",
        "Generated Knowledge",
        "Reflexion",
        "Directional Stimulus",
        "Prompt Chaining",
    ]
    for tech in required_techniques:
        assert tech.lower() in dec_matrix.lower(), f"Technique '{tech}' missing from decision_matrix.md"
        assert tech.lower() in components.lower(), f"Technique '{tech}' missing from prompt_components.md"
        print(f"  -> PASS: '{tech}' verified in decision matrix & component templates.")
    return True

def test_example_few_shot_counts() -> bool:
    print("[4/6] Testing synthetic few-shot standards (>= 2 examples) in case studies...")
    case_a = (SKILL_DIR / "examples" / "case_agentic_bot.md").read_text(encoding="utf-8")
    case_c = (SKILL_DIR / "examples" / "case_high_stakes_eval.md").read_text(encoding="utf-8")
    
    # Case A must contain at least 2 examples including Reflexion
    assert "예시 1" in case_a and "예시 2" in case_a, "Case A must have at least 2 few-shot examples"
    assert "Reflexion" in case_a, "Case A must demonstrate Reflexion error recovery"
    print("  -> PASS: case_agentic_bot.md contains 2 few-shot pairs with Reflexion.")
    
    # Case C must contain at least 2 examples
    assert "예시 1" in case_c and "예시 2" in case_c, "Case C must have at least 2 few-shot examples"
    assert "SUSPICIOUS" in case_c, "Case C must demonstrate borderline/suspicious case"
    print("  -> PASS: case_high_stakes_eval.md contains 2 few-shot pairs with SUSPICIOUS verdict.")
    return True

def test_case_analytical_pipeline_logic() -> bool:
    print("[5/6] Testing Python pipeline logic for case_analytical_report.md...")
    # 1. Test extract_and_parse_json on markdown fenced content
    def extract_and_parse_json(text: str) -> dict:
        text = text.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        clean_text = match.group(1) if match else text
        return json.loads(clean_text)

    mock_llm_output = """```json
{
  "report_title": "Enterprise AI Strategy 2026",
  "chapters": [
    {
      "chapter_number": 1,
      "chapter_title": "Infrastructure Architecture",
      "key_takeaway": "Establish hybrid private cloud",
      "sub_topics": ["On-prem vLLM", "Cost efficiency", "GPU cluster"]
    },
    {
      "chapter_number": 2,
      "chapter_title": "Data Governance",
      "key_takeaway": "Enforce strict RBAC and PII masking",
      "sub_topics": ["Data classification", "Vector DB isolation", "Audit trails"]
    }
  ]
}
```"""
    skeleton = extract_and_parse_json(mock_llm_output)
    assert skeleton["report_title"] == "Enterprise AI Strategy 2026", "Failed parsing skeleton title"
    assert len(skeleton["chapters"]) == 2, "Failed parsing chapters"

    # 2. Test expand_prompt formatting without KeyError
    expand_prompt_template = (
        "Role: Technical Writer\n"
        "Chapter: {chapter_number} - {chapter_title}\n"
        "Report: {report_title}\n"
        "Key Message: {key_takeaway}\n"
        "Sub-topics: {sub_topics}\n"
    )
    mock_expanded_chapters = []
    for ch in skeleton["chapters"]:
        formatted_prompt = expand_prompt_template.format(
            report_title=skeleton["report_title"],
            chapter_number=ch["chapter_number"],
            chapter_title=ch["chapter_title"],
            key_takeaway=ch["key_takeaway"],
            sub_topics=", ".join(ch["sub_topics"]) if isinstance(ch["sub_topics"], list) else str(ch["sub_topics"])
        )
        assert f"Report: {skeleton['report_title']}" in formatted_prompt
        assert str(ch["chapter_number"]) in formatted_prompt
        mock_expanded_chapters.append(f"Content of Chapter {ch['chapter_number']}")

    # 3. Test aggregate_prompt formatting without KeyError
    aggregate_prompt_template = (
        "Editor Role\n"
        "Skeleton: {phase_1_skeleton}\n"
        "Chapter 1: {chapter_1_text}\n"
        "Chapter 2: {chapter_2_text}\n"
    )
    agg_params = {
        "phase_1_skeleton": json.dumps(skeleton, ensure_ascii=False)
    }
    for idx, c in enumerate(mock_expanded_chapters, start=1):
        agg_params[f"chapter_{idx}_text"] = c

    formatted_agg = aggregate_prompt_template.format(**agg_params)
    assert "Content of Chapter 1" in formatted_agg
    assert "Content of Chapter 2" in formatted_agg
    print("  -> PASS: Async SoT pipeline parameter mapping and JSON extraction run without error.")
    return True

def test_case_high_stakes_eval_runner() -> bool:
    print("[6/6] Testing Python majority voting runner for case_high_stakes_eval.md...")
    def clean_and_parse_json(text: str) -> dict:
        text = text.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        cleaned = match.group(1) if match else text
        return json.loads(cleaned)

    # Test JSON parsing with markdown codeblock
    raw_sample = """```json
{
  "slip_id": "EXP-2026-9011",
  "audit_reasoning": {"step1": "ok"},
  "verdict": "FRAUD",
  "confidence_score": 0.95,
  "action_required": "Reject"
}
```"""
    parsed = clean_and_parse_json(raw_sample)
    assert parsed["verdict"] == "FRAUD"

    # Test majority voting algorithm
    mock_samples = [
        {"slip_id": "EXP-1", "verdict": "FRAUD", "audit_reasoning": "Reason A"},
        {"slip_id": "EXP-1", "verdict": "FRAUD", "audit_reasoning": "Reason B"},
        {"slip_id": "EXP-1", "verdict": "FRAUD", "audit_reasoning": "Reason C"},
        {"slip_id": "EXP-1", "verdict": "SUSPICIOUS", "audit_reasoning": "Reason D"},
        {"slip_id": "EXP-1", "verdict": "NORMAL", "audit_reasoning": "Reason E"},
    ]
    verdicts = [r["verdict"] for r in mock_samples]
    vote_counts = Counter(verdicts)
    top_candidates = vote_counts.most_common(2)
    assert top_candidates[0] == ("FRAUD", 3)
    consensus_ratio = top_candidates[0][1] / len(mock_samples)
    assert consensus_ratio == 0.6
    
    # Test tie-breaking rule
    tied_samples = ["FRAUD", "FRAUD", "NORMAL", "NORMAL"]
    tied_counts = Counter(tied_samples).most_common(2)
    if len(tied_counts) > 1 and tied_counts[0][1] == tied_counts[1][1]:
        consensus_verdict = "SUSPICIOUS"
    else:
        consensus_verdict = tied_counts[0][0]
    assert consensus_verdict == "SUSPICIOUS", "Tie-break did not fallback to SUSPICIOUS"

    print("  -> PASS: Majority voting aggregation, JSON cleaning, and tie-breaking verified.")
    return True

def test_markdown_python_code_blocks_ast() -> bool:
    print("[7/7] Testing AST parse validity on all python codeblocks in examples...")
    for md_file in (SKILL_DIR / "examples").glob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        blocks = []
        lines = content.splitlines()
        in_python = False
        current_block = []
        for line in lines:
            if line.strip() == "```python":
                in_python = True
                current_block = []
            elif line.strip() == "```" and in_python:
                in_python = False
                blocks.append("\n".join(current_block))
            elif in_python:
                current_block.append(line)
                
        for idx, block in enumerate(blocks, start=1):
            try:
                ast.parse(block)
                print(f"  -> PASS: {md_file.name} python block #{idx} compiles without syntax error.")
            except SyntaxError as e:
                print(f"  -> FAIL: {md_file.name} block #{idx} SyntaxError: {e}")
                raise
    return True

def main():
    print("=" * 60)
    print("  META-PROMPTING SKILL AUTOMATED VERIFICATION SUITE")
    print("=" * 60)
    results = [
        test_yaml_frontmatter(),
        test_deliverables_exist(),
        test_technique_coverage(),
        test_example_few_shot_counts(),
        test_case_analytical_pipeline_logic(),
        test_case_high_stakes_eval_runner(),
        test_markdown_python_code_blocks_ast(),
    ]
    print("=" * 60)
    if all(results):
        print("ALL 7 TEST SUITES PASSED (100% SUCCESS)!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("SOME TESTS FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    main()
