"""LLM Service - Handles OpenAI GPT and Google Gemini API calls."""

import json
from openai import AsyncOpenAI
import google.generativeai as genai
from config import settings


class LLMService:
    def __init__(self):
        # OpenAI client
        self.openai_client = None
        if settings.OPENAI_API_KEY:
            self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        # Gemini client
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)

    async def generate_response(
        self,
        prompt: str,
        context: str = "",
        model: str = "gpt-4",
        system_prompt: str = "",
        chat_history: list = None
    ) -> dict:
        """Generate a response using the specified LLM."""
        if model.startswith("gpt"):
            return await self._call_openai(prompt, context, model, system_prompt, chat_history)
        elif model == "gemini":
            return await self._call_gemini(prompt, context, system_prompt, chat_history)
        else:
            raise ValueError(f"Unsupported model: {model}")

    async def _call_openai(
        self, prompt: str, context: str, model: str, system_prompt: str, chat_history: list
    ) -> dict:
        """Call OpenAI GPT API."""
        if not self.openai_client:
            raise ValueError("OpenAI API key not configured")

        messages = []

        # System message
        sys_msg = system_prompt or "You are DocuMind AI, an intelligent document assistant. You help users understand their documents, answer questions, and provide insights. Always be accurate and cite sources when available."
        if context:
            sys_msg += f"\n\nRelevant document context:\n{context}\n\nUse this context to answer the user's question. If the context doesn't contain relevant information, say so honestly."
        messages.append({"role": "system", "content": sys_msg})

        # Chat history
        if chat_history:
            for msg in chat_history[-10:]:  # Last 10 messages
                messages.append({"role": msg["role"], "content": msg["content"]})

        # User message
        messages.append({"role": "user", "content": prompt})

        response = await self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )

        return {
            "reply": response.choices[0].message.content,
            "tokens_used": response.usage.total_tokens if response.usage else None,
            "model_used": "GPT-4o Mini"
        }

    async def _call_gemini(
        self, prompt: str, context: str, system_prompt: str, chat_history: list
    ) -> dict:
        """Call Google Gemini API."""
        if not settings.GEMINI_API_KEY:
            raise ValueError("Gemini API key not configured")

        model = genai.GenerativeModel("gemini-1.5-flash")

        # Build the full prompt
        full_prompt = ""

        sys_msg = system_prompt or "You are DocuMind AI, an intelligent document assistant. You help users understand their documents, answer questions, and provide insights."
        full_prompt += f"System: {sys_msg}\n\n"

        if context:
            full_prompt += f"Relevant document context:\n{context}\n\nUse this context to answer accurately. Cite sources when available.\n\n"

        if chat_history:
            for msg in chat_history[-10:]:
                role = "User" if msg["role"] == "user" else "Assistant"
                full_prompt += f"{role}: {msg['content']}\n"

        full_prompt += f"User: {prompt}\nAssistant:"

        response = await model.generate_content_async(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=2000
            )
        )

        return {
            "reply": response.text,
            "tokens_used": None,
            "model_used": "Gemini 1.5 Flash"
        }

    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using OpenAI."""
        if not self.openai_client:
            raise ValueError("OpenAI API key needed for embeddings")

        response = await self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )
        return [item.embedding for item in response.data]

    async def generate_quiz(self, context: str, num_questions: int = 5, model: str = "gpt-4") -> dict:
        """Generate quiz questions from document context."""
        prompt = f"""Based on the following content, generate exactly {num_questions} multiple-choice quiz questions.

Content:
{context}

Return ONLY valid JSON in this exact format:
{{
  "questions": [
    {{
      "question": "What is...?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct": 0,
      "explanation": "Brief explanation why this is correct"
    }}
  ]
}}"""

        system_prompt = "You are a quiz generator. Return ONLY valid JSON, no markdown formatting."
        result = await self.generate_response(prompt, model=model, system_prompt=system_prompt)

        try:
            # Try to parse as JSON
            reply = result["reply"].strip()
            if reply.startswith("```"):
                reply = reply.split("\n", 1)[1].rsplit("```", 1)[0]
            quiz_data = json.loads(reply)
            return quiz_data
        except json.JSONDecodeError:
            return {"questions": []}

    async def generate_flashcards(self, context: str, num_cards: int = 10, model: str = "gpt-4") -> dict:
        """Generate flashcards from document context."""
        prompt = f"""Based on the following content, generate exactly {num_cards} study flashcards.

Content:
{context}

Return ONLY valid JSON in this exact format:
{{
  "cards": [
    {{
      "front": "Question or concept",
      "back": "Answer or explanation"
    }}
  ]
}}"""

        system_prompt = "You are a flashcard generator. Return ONLY valid JSON, no markdown formatting."
        result = await self.generate_response(prompt, model=model, system_prompt=system_prompt)

        try:
            reply = result["reply"].strip()
            if reply.startswith("```"):
                reply = reply.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(reply)
        except json.JSONDecodeError:
            return {"cards": []}

    async def generate_summary(self, context: str, model: str = "gpt-4") -> dict:
        """Generate a summary of document content."""
        prompt = f"""Provide a comprehensive summary of the following content. Include:
1. A clear summary paragraph
2. Key points as bullet points

Content:
{context}

Return ONLY valid JSON in this exact format:
{{
  "summary": "Comprehensive summary text...",
  "key_points": ["Point 1", "Point 2", "Point 3"]
}}"""

        system_prompt = "You are a document summarizer. Return ONLY valid JSON, no markdown formatting."
        result = await self.generate_response(prompt, model=model, system_prompt=system_prompt)

        try:
            reply = result["reply"].strip()
            if reply.startswith("```"):
                reply = reply.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(reply)
        except json.JSONDecodeError:
            return {"summary": result["reply"], "key_points": []}


llm_service = LLMService()
