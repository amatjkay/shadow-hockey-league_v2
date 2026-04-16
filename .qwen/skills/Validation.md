# Validation Skill

When to use: input validation, business rule checks, or data integrity.

Core instructions:
- Validate client-side and server-side.
- Use schema validation (e.g., Pydantic, Joi) where possible.
- Return clear error messages with HTTP status codes.
- Ensure idempotency for safe retries.

Template:
1. Input schema.
2. Error mapping (code/message).
3. Edge cases (null, dup, range).