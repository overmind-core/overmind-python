# Available Policy Templates

Currently, Overmind supports 5 basic policy templates:

- **`anonymize_pii`**: Anonymizes PII (Personally Identifiable Information)
- **`reject_pii`**: Rejects requests containing PII
- **`reject_prompt_injection`**: Rejects responses that appear to be prompt injection attempts
- **`reject_irrelevant_answer`**: Rejects responses that don't answer the original question
- **`reject_llm_judge_with_criteria`**: Rejects responses that don't meet specified criteria

### Policy Template Details

#### AnonymizePii & RejectPii
Both policies accept an optional `pii_types` parameter, which must be one or more from:
- `"DEMOGRAPHIC_DATA"`
- `"FINANCIAL_ID"`
- `"GEOGRAPHIC_DATA"`
- `"GOVERNMENT_ID"`
- `"MEDICAL_DATA"`
- `"SECURITY_DATA"`
- `"TECHNICAL_ID"`
- `"PERSON_NAME"`
- `"PHONE"`
- `"EMAIL"`

#### RejectLlmJudgeWithCriteria
Requires a `criteria` parameter which is a list of statements. Each statement should evaluate to true or false. The policy will reject if at least one of these statements evaluates to false.

