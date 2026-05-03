from enum import Enum
from langchain_ollama import OllamaLLM
from config import QWEN_LIGHT, QWEN_MEDIUM, QWEN_HEAVY

class ModelTier(Enum):
    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"

def get_llm(tier: ModelTier, reasoning: bool = False) -> OllamaLLM:
    """Factory to get the Ollama client based on tier.

    Sampling overrides:
      - temperature=0.3 → riproducibilità per task di
        template-completion. Il modelfile default di qwen3.5 è
        temperature=1.0 (ottimo per chat creativa, pessimo per
        seguire un template fisso).
      - repeat_penalty=1.0 → disattiva la penalizzazione di
        ripetizione. Il default Ollama è 1.1; con presence_penalty=1.5
        nel modelfile, il modello sotto-pesa la ripetizione strutturale
        del template (saltava sezioni in writer_report).
      - reasoning=False (default): template-completion, fast path,
        used by all writers / planner / structurer / linguist / etc.
      - reasoning=True: multi-step verification, used ONLY by the
        critic. Expect 30–60 s wall-clock per critic invocation.
    """
    if tier == ModelTier.LIGHT:
        model_name = QWEN_LIGHT
    elif tier == ModelTier.MEDIUM:
        model_name = QWEN_MEDIUM
    elif tier == ModelTier.HEAVY:
        model_name = QWEN_HEAVY
    else:
        raise ValueError(f"Unknown model tier: {tier}")

    return OllamaLLM(
        model=model_name,
        temperature=0.3,
        repeat_penalty=1.0,
        reasoning=reasoning,
    )
