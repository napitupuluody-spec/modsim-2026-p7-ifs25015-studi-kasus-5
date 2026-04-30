import os
import requests


class LLMService:
    """Service untuk berkomunikasi dengan custom LLM API."""

    def __init__(self):
        self.base_url = os.getenv("LLM_BASE_URL", "").rstrip("/")
        self.token = os.getenv("LLM_TOKEN", "")
        
        if not self.base_url or not self.token:
            raise ValueError(
                "LLM_BASE_URL dan LLM_TOKEN harus di-set di file .env"
            )

    def generate(self, prompt: str, system_prompt: str = "", max_tokens: int = 2048) -> str:
        """
        Mengirim prompt ke LLM dan mengembalikan teks respons.

        Args:
            prompt: Pesan utama untuk LLM.
            system_prompt: Instruksi sistem opsional.
            max_tokens: Maksimum token yang dihasilkan.

        Returns:
            String teks respons dari LLM.
        """
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # Build messages array for API
        messages = prompt
        if system_prompt:
            messages = system_prompt
        
        payload = {
            "token": self.token,
            "chat": messages,
        }

        try:
            # Try main endpoint first
            response = requests.post(
                f"{self.base_url}/llm/chat",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            # If 404, try alternative endpoint
            if response.status_code == 404:
                response = requests.post(
                    f"{self.base_url}/complete",
                    json=payload,
                    headers=headers,
                    timeout=30
                )
            
            response.raise_for_status()
            data = response.json()
            
            # Handle different response formats
            if "response" in data:
                return data["response"]
            elif "text" in data:
                return data["text"]
            elif "choices" in data and len(data["choices"]) > 0:
                choice = data["choices"][0]
                if isinstance(choice, dict):
                    return choice.get("text", choice.get("message", {}).get("content", ""))
                return str(choice)
            else:
                # Return first string value found
                for val in data.values():
                    if isinstance(val, str):
                        return val
                return str(data)
                
        except requests.exceptions.RequestException as e:
            raise ValueError(f"LLM API error: {str(e)}")
