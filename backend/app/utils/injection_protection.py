import re


class PromptInjectionProtection:
    def __init__(self):
        self.blocked_patterns = [
            r"ignore previous instructions",
            r"you are now",
            r"system prompt",
            r"act as",
            r"pretend you are",
            r"forget everything",
            r"new instructions",
            r"override",
            r"disregard",
            r"ignore above",
            r"developer mode",
            r"jailbreak",
            r"DAN mode",
            r"do anything now",
            r"bypass",
        ]

        self.max_input_length = 2000

    def sanitize_input(self, user_input: str) -> str:
        if not user_input:
            return ""

        sanitized = user_input

        # Remove blocked patterns
        for pattern in self.blocked_patterns:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)

        # Remove excessive whitespace
        sanitized = re.sub(r"\s+", " ", sanitized).strip()

        # Truncate to max length
        if len(sanitized) > self.max_input_length:
            sanitized = sanitized[:self.max_input_length]

        return sanitized

    def detect_injection(self, user_input: str) -> dict:
        if not user_input:
            return {"detected": False, "reason": None}

        for pattern in self.blocked_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                return {
                    "detected": True,
                    "reason": f"Potential prompt injection detected: matches pattern '{pattern}'",
                }

        if len(user_input) > self.max_input_length:
            return {
                "detected": True,
                "reason": f"Input exceeds maximum length of {self.max_input_length} characters",
            }

        return {"detected": False, "reason": None}

    def validate_output(self, output: str, expected_keys: list[str] | None = None) -> dict:
        if not output:
            return {"valid": False, "reason": "Empty output"}

        if len(output) > 10000:
            return {"valid": False, "reason": "Output exceeds maximum length"}

        if expected_keys:
            import json
            try:
                data = json.loads(output)
                for key in expected_keys:
                    if key not in data:
                        return {"valid": False, "reason": f"Missing required key: {key}"}
            except json.JSONDecodeError:
                pass

        return {"valid": True, "reason": None}


injection_protection = PromptInjectionProtection()
