def format_data_method_note(factor: str, explanation: str) -> str:
    """Normalize package-availability and 293 K wording for the team notes UI."""
    combined = f"{factor} {explanation}".casefold()
    if "google drive" in combined or "mydrive" in combined:
        return "File not included in the delivered package; status unconfirmed"
    if "293 k" in combined:
        return (
            "293 K is a screening threshold, not an instrument limit. "
            "Next action: Do not describe it as an official instrument limit without authoritative documentation."
        )
    return explanation
