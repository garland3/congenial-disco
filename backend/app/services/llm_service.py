import requests
import json
from typing import Dict, Any, Optional
from ..config import settings

class LLMService:
    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.base_url = settings.openrouter_base_url.rstrip('/')
        self.model = settings.model_name
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    async def generate_questions_from_goals(self, goals: str) -> Dict[str, Any]:
        prompt = f"""
        Based on the following interview goals, generate a structured JSON schema for interview questions.
        Each field should have a "prompt" (the question to ask) and a "type" (string, story, or yes/no).
        
        Goals: {goals}
        
        Generate 3-5 relevant questions that would help gather information about these goals.
        Return only valid JSON in this format:
        {{
            "field_name": {{"prompt": "Question text?", "type": "string|story|yes/no"}}
        }}
        """
        
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that generates structured interview questions. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            return json.loads(content)
        
        except Exception as e:
            return self._fallback_schema(goals)
    
    async def extract_data_from_conversation(self, conversation_history: list, questions_schema: dict) -> dict:
        """Extract structured data from conversation history based on schema"""
        conversation_text = "\n".join([f"{msg['sender']}: {msg['text']}" for msg in conversation_history])
        
        schema_description = ""
        for field_name, field_info in questions_schema.items():
            schema_description += f"- {field_name}: {field_info['prompt']} (type: {field_info['type']})\n"
        
        prompt = f"""
        Based on the following conversation, extract information for these fields:
        {schema_description}
        
        Conversation:
        {conversation_text}
        
        Return a JSON object with the field names as keys and extracted information as values. 
        If information for a field is not available or unclear, use null.
        Only return valid JSON.
        """
        
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a data extraction assistant. Extract structured information from conversations and return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 1000
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            return json.loads(content)
            
        except Exception as e:
            return {}

    async def judge_completeness(self, extracted_data: dict, questions_schema: dict) -> tuple[dict, bool, str]:
        """Judge how well each field is filled and overall completeness"""
        schema_description = ""
        for field_name, field_info in questions_schema.items():
            schema_description += f"- {field_name}: {field_info['prompt']} (type: {field_info['type']})\n"
        
        extracted_summary = ""
        for field_name, value in extracted_data.items():
            extracted_summary += f"- {field_name}: {value}\n"
        
        prompt = f"""
        Evaluate the completeness and quality of extracted data for an interview.
        
        Required fields:
        {schema_description}
        
        Extracted data:
        {extracted_summary}
        
        For each field, rate the completeness on a scale of 0-10:
        - 0-3: Missing or very insufficient
        - 4-6: Partially filled but needs more detail
        - 7-8: Good but could use minor improvements
        - 9-10: Complete and detailed
        
        Return a JSON object with:
        - "field_scores": object with field names as keys and scores (0-10) as values
        - "overall_complete": boolean indicating if interview is ready to conclude (all fields >= 7)
        - "suggestions": string with specific suggestions for what information is still needed
        
        Only return valid JSON.
        """
        
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are an interview quality judge. Evaluate data completeness objectively and return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 500
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            judgment = json.loads(content)
            
            return judgment.get("field_scores", {}), judgment.get("overall_complete", False), judgment.get("suggestions", "")
            
        except Exception as e:
            # Fallback scoring
            field_scores = {}
            for field_name in questions_schema.keys():
                field_scores[field_name] = 5 if extracted_data.get(field_name) else 0
            return field_scores, False, "Unable to evaluate completeness. Please continue the conversation."

    async def generate_next_question(self, conversation_history: list, questions_schema: dict, extracted_data: dict, field_scores: dict, suggestions: str) -> str:
        """Generate the next question based on conversation and missing information"""
        conversation_text = "\n".join([f"{msg['sender']}: {msg['text']}" for msg in conversation_history[-6:]])  # Last 6 messages for context
        
        schema_description = ""
        for field_name, field_info in questions_schema.items():
            score = field_scores.get(field_name, 0)
            schema_description += f"- {field_name}: {field_info['prompt']} (score: {score}/10)\n"
        
        prompt = f"""
        You are conducting an interview. Based on the conversation and current data quality, ask the next most appropriate question.
        
        Interview fields and current scores:
        {schema_description}
        
        Areas needing improvement: {suggestions}
        
        Recent conversation:
        {conversation_text}
        
        Generate a natural, conversational question that will help gather the most needed information. 
        Be specific and engaging. Don't ask about fields that are already well-covered (score >= 7).
        Return only the question text, no additional formatting.
        """
        
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a skilled interviewer. Ask natural, engaging questions that gather specific information efficiently."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 200
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
            
        except Exception as e:
            return "Could you tell me more about your experience?"

    async def evaluate_response(self, question: str, answer: str, field_type: str) -> tuple[bool, Optional[str]]:
        prompt = f"""
        Evaluate if the following answer is sufficient for the question asked.
        
        Question: {question}
        Answer: {answer}
        Expected type: {field_type}
        
        Return "SUFFICIENT" if the answer adequately addresses the question, or "INSUFFICIENT: reason" if not.
        Be helpful and encouraging. Only mark as insufficient if the answer is clearly inadequate.
        """
        
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are evaluating interview responses. Be fair and encouraging."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 200
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
            result_data = response.json()
            result = result_data["choices"][0]["message"]["content"].strip()
            
            if result.startswith("SUFFICIENT"):
                return True, None
            elif result.startswith("INSUFFICIENT"):
                reason = result.split(":", 1)[1].strip() if ":" in result else "Please provide more detail."
                return False, reason
            else:
                return True, None
                
        except Exception as e:
            return self._fallback_evaluation(answer, field_type)
    
    def _fallback_schema(self, goals: str) -> Dict[str, Any]:
        words = goals.lower().split()
        
        if any(word in words for word in ['bug', 'fix', 'software', 'error']):
            return {
                "issue_description": {"prompt": "Please describe the issue you encountered.", "type": "story"},
                "steps_taken": {"prompt": "What steps did you take to resolve it?", "type": "story"},
                "outcome": {"prompt": "What was the final outcome?", "type": "string"}
            }
        elif any(word in words for word in ['document', 'guide', 'process']):
            return {
                "topic": {"prompt": "What is the main topic you want to document?", "type": "string"},
                "key_points": {"prompt": "What are the key points to cover?", "type": "story"},
                "audience": {"prompt": "Who is the intended audience?", "type": "string"}
            }
        else:
            return {
                "main_topic": {"prompt": f"Can you tell me more about {goals}?", "type": "story"},
                "key_details": {"prompt": "What are the most important details?", "type": "story"}
            }
    
    def _fallback_evaluation(self, answer: str, field_type: str) -> tuple[bool, Optional[str]]:
        if field_type == "yes/no":
            return answer.lower() in ["yes", "no"], "Please answer with 'yes' or 'no'."
        elif len(answer.strip()) < 10:
            return False, "Please provide a more detailed response."
        else:
            return True, None

llm_service = LLMService()