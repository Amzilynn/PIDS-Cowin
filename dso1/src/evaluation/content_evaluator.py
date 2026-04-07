import json
from groq import Groq
from dso1.src.nlp import prompts

class ContentEvaluator:
    """
    Evaluates the sales content of a transcript using an LLM.
    Part of the two-part evaluation system.
    """
    def __init__(self):
        self.client = Groq()

    def evaluate(self, conversation_history):
        if not conversation_history:
            return {
                "content_grade": "N/A",
                "feedback": "No conversation recorded to evaluate content."
            }

        transcript = "\n".join([f"{m['role']}: {m['text']}" for m in conversation_history])
        
        eval_prompt = f"""
        You are a Sales Performance Auditor for a pharmaceutical company.
        Analyze the following transcript of a session where a Medical Delegate practiced with a doctor avatar.
        
        TRANSCRIPT:
        {transcript}
        
        EVALUATE BASED ON:
        1. Product Knowledge Accuracy (did they mention correct facts?)
        2. Objection Handling (how well did they respond to doctor concerns?)
        3. Professional Tone & Scientific Language.
        
        Provide a JSON response with:
        - "score": (0-100)
        - "grade": (A, B, C, D, or F)
        - "strengths": [list]
        - "weaknesses": [list]
        - "summary_feedback": "string"
        """
        
        try:
            completion = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": eval_prompt}],
                response_format={"type": "json_object"}
            )
            result = json.loads(completion.choices[0].message.content)
            return result
        except Exception as e:
            print(f"[ERROR] Content Evaluation failed: {e}")
            return {"error": str(e)}
