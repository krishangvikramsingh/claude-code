"""Answer generators.

* ExtractiveGenerator: offline, no LLM. Selects the most question-relevant sentences from the retrieved
  passages and cites them. It cannot paraphrase or reason; it can only quote retrieved text.
* AnthropicGenerator / OllamaGenerator: LLM-backed, use the structured prompt. Require an API key / local server.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field

from .chunking import split_sentences
from .config import Settings
from .errors import GenerationError
from .prompt_templates import ABSTAIN_TEXT, BuiltPrompt, looks_like_injection
from .retrieval import Retrieved

_STOP = set("""a an the of to in on for and or is are was were be been being what which who whom whose when where why how do does
did can could should would will shall may might must it its this that these those with by from as at about into than then
so such there their they them you your i we our not no any each per via vs if""".split())


def _stem(w: str) -> str:
    for suf in ("ations", "ation", "ings", "ing", "ies", "ed", "es", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 4:
            return w[: -len(suf)] + ("y" if suf == "ies" else "")
    return w


def content_terms(text: str) -> set[str]:
    return {_stem(w) for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in _STOP and len(w) > 1}


@dataclass
class Generation:
    text: str
    abstained: bool
    cited: list[str]                         # labels, validated against retrieved set
    provider: str
    notes: dict = field(default_factory=dict)


def extract_citations(text: str, valid: set[str]) -> tuple[list[str], list[str]]:
    """Return (valid labels in order, invalid labels) found as [S#] in `text`."""
    found = re.findall(r"\[(S\d+)\]", text)
    ok, bad = [], []
    for f in found:
        (ok if f in valid else bad).append(f)
    return list(dict.fromkeys(ok)), list(dict.fromkeys(bad))


class ExtractiveGenerator:
    name = "extractive (no LLM)"

    def __init__(self, s: Settings):
        self.s = s

    def generate(self, question: str, built: BuiltPrompt) -> Generation:
        q_terms = content_terms(question)
        used = built.used
        if not used or used[0].score < self.s.min_score or not q_terms:
            return Generation(ABSTAIN_TEXT, True, [], self.name, {"reason": "low retrieval score"})
        cands, skipped_inj = [], 0
        for r in used:
            for sent in split_sentences(r.chunk.text):
                if len(sent.split()) < 5 or not re.search(r"[.!?]$", sent):  # heading fragments are not answers
                    continue
                if looks_like_injection(sent):
                    skipped_inj += 1
                    continue
                cov = len(q_terms & content_terms(sent)) / len(q_terms)
                cands.append((cov + 0.25 * r.score, cov, r.rank, sent, r.label))
        if not cands:
            return Generation(ABSTAIN_TEXT, True, [], self.name, {"reason": "no usable sentences", "injection_sentences_skipped": skipped_inj})
        cands.sort(key=lambda x: -x[0])
        best_cov = max(c[1] for c in cands)
        if best_cov < self.s.min_coverage:
            return Generation(ABSTAIN_TEXT, True, [], self.name,
                              {"reason": "insufficient question-term coverage", "best_coverage": round(best_cov, 2),
                               "injection_sentences_skipped": skipped_inj})
        picked, seen = [], set()
        for sc, cov, rank, sent, label in cands:
            if cov < self.s.min_coverage * 0.5 or sent in seen:
                continue
            picked.append((rank, sent, label))
            seen.add(sent)
            if len(picked) == 3:
                break
        picked.sort(key=lambda x: x[0])
        text = " ".join(f"{sent} [{label}]" for _, sent, label in picked)
        return Generation(text, False, list(dict.fromkeys(l for _, _, l in picked)), self.name,
                          {"best_coverage": round(best_cov, 2), "injection_sentences_skipped": skipped_inj})


class AnthropicGenerator:
    def __init__(self, s: Settings):
        self.s, self.name = s, f"anthropic:{s.anthropic_model}"

    def generate(self, question: str, built: BuiltPrompt) -> Generation:
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise GenerationError("ANTHROPIC_API_KEY is not set. Set it in the environment or use the extractive provider.")
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=key)
            msg = client.messages.create(model=self.s.anthropic_model, max_tokens=500, temperature=0.0,
                                         system=built.system, messages=[{"role": "user", "content": built.user}])
            text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()
        except Exception as e:  # never echo the key or a stack trace
            raise GenerationError(f"The LLM request failed ({type(e).__name__}).") from e
        return _finish(text, built, self.name)


class OllamaGenerator:
    def __init__(self, s: Settings):
        self.s, self.name = s, f"ollama:{s.ollama_model}"

    def generate(self, question: str, built: BuiltPrompt) -> Generation:
        body = json.dumps({"model": self.s.ollama_model, "stream": False, "options": {"temperature": 0},
                           "messages": [{"role": "system", "content": built.system},
                                        {"role": "user", "content": built.user}]}).encode()
        req = urllib.request.Request(self.s.ollama_url.rstrip("/") + "/api/chat", data=body,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                text = json.loads(r.read())["message"]["content"].strip()
        except (urllib.error.URLError, KeyError, ValueError, TimeoutError) as e:
            raise GenerationError(f"Could not reach the local Ollama server ({type(e).__name__}).") from e
        return _finish(text, built, self.name)


def _finish(text: str, built: BuiltPrompt, name: str) -> Generation:
    valid = {r.label for r in built.used}
    ok, bad = extract_citations(text, valid)
    abstained = text.strip().strip('"') == ABSTAIN_TEXT
    for b in bad:  # remove citations to non-existent passages
        text = text.replace(f"[{b}]", "")
    return Generation(text, abstained, ok, name, {"invalid_citations_removed": bad})


def make_generator(s: Settings):
    if s.llm_provider == "extractive":
        return ExtractiveGenerator(s)
    if s.llm_provider == "anthropic":
        return AnthropicGenerator(s)
    if s.llm_provider == "ollama":
        return OllamaGenerator(s)
    raise GenerationError(f"Unknown LLM provider '{s.llm_provider}' (extractive, anthropic, ollama)")
