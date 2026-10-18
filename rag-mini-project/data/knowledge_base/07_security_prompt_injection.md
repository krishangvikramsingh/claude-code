# Security: Prompt Injection in RAG

## Indirect prompt injection

In a RAG system, the retrieved documents are inserted into the prompt. If a document contains text such as an instruction to ignore previous rules, the model may treat that text as a command. This is called indirect prompt injection, and it is listed as the first risk, LLM01, in the OWASP Top 10 for LLM Applications.

## Treat retrieved text as data

The first mitigation is to state in the system prompt that retrieved passages are untrusted data and never instructions. Passages are wrapped in clearly marked delimiters, and delimiter-like strings inside a passage are neutralised so that a document cannot close the passage block early.

## Further mitigations

Additional measures include filtering passages that contain known injection phrases, limiting the tools and secrets available to the model, never placing API keys in the prompt, validating the output format, and reviewing which documents are allowed into the knowledge base. None of these measures gives a guarantee, so security tests with adversarial documents should be part of the evaluation.

## Secrets

API keys must be read from environment variables and must never be written into prompts, logs, source code or the submission archive. Error messages shown to users should not contain keys or stack traces.
