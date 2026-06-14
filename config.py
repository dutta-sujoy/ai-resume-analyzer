import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configurable Gemini Model
# We default to a modern, supported model (gemini-2.5-flash) but allow overrides
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Configurable scoring weights
WEIGHT_KEYWORD_ALIGNMENT = float(os.getenv("WEIGHT_KEYWORD_ALIGNMENT", "0.40"))
WEIGHT_EXPERIENCE_RELEVANCE = float(os.getenv("WEIGHT_EXPERIENCE_RELEVANCE", "0.35"))
WEIGHT_FORMATTING_HEALTH = float(os.getenv("WEIGHT_FORMATTING_HEALTH", "0.25"))

# Normalize weights if they do not sum to 1.0
total_weight = WEIGHT_KEYWORD_ALIGNMENT + WEIGHT_EXPERIENCE_RELEVANCE + WEIGHT_FORMATTING_HEALTH
if total_weight > 0 and not (0.99 <= total_weight <= 1.01):
    WEIGHT_KEYWORD_ALIGNMENT /= total_weight
    WEIGHT_EXPERIENCE_RELEVANCE /= total_weight
    WEIGHT_FORMATTING_HEALTH /= total_weight
