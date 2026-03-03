"""LLM Service - Handles OpenAI GPT, Google Gemini, and Groq API calls."""

import json
import re
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

        # Groq client (OpenAI-compatible, free tier)
        self.groq_client = None
        if settings.GROQ_API_KEY:
            self.groq_client = AsyncOpenAI(
                api_key=settings.GROQ_API_KEY,
                base_url="https://api.groq.com/openai/v1"
            )

    async def generate_response(
        self,
        prompt: str,
        context: str = "",
        model: str = "gpt-4",
        system_prompt: str = "",
        chat_history: list = None
    ) -> dict:
        """Generate a response using the specified LLM, with cascading fallback."""
        # Build the fallback chain based on selected model
        fallback_chain = []

        if model.startswith("gpt"):
            fallback_chain = ["openai", "groq", "gemini", "offline"]
        elif model == "gemini":
            fallback_chain = ["gemini", "groq", "openai", "offline"]
        elif model == "groq":
            fallback_chain = ["groq", "gemini", "openai", "offline"]
        else:
            fallback_chain = ["groq", "gemini", "openai", "offline"]

        last_error = None
        for provider in fallback_chain:
            try:
                if provider == "openai" and self.openai_client:
                    return await self._call_openai(prompt, context, model, system_prompt, chat_history)
                elif provider == "gemini" and settings.GEMINI_API_KEY:
                    result = await self._call_gemini(prompt, context, system_prompt, chat_history)
                    if provider != fallback_chain[0]:
                        result["model_used"] += " (fallback)"
                    return result
                elif provider == "groq" and self.groq_client:
                    result = await self._call_groq(prompt, context, system_prompt, chat_history)
                    if provider != fallback_chain[0]:
                        result["model_used"] += " (fallback)"
                    return result
                elif provider == "offline":
                    return self._offline_response(prompt, context)
            except Exception as e:
                print(f"⚠️ {provider} failed ({type(e).__name__}: {str(e)[:100]}), trying next...")
                last_error = e

        # Should never reach here because offline never fails
        return self._offline_response(prompt, context)

    async def _call_openai(
        self, prompt: str, context: str, model: str, system_prompt: str, chat_history: list
    ) -> dict:
        """Call OpenAI GPT API with timeout."""
        if not self.openai_client:
            raise ValueError("OpenAI API key not configured")

        import asyncio
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

        response = await asyncio.wait_for(
            self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            ),
            timeout=30
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

        model = genai.GenerativeModel("gemini-2.0-flash")

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
            "model_used": "Gemini 2.0 Flash"
        }

    async def _call_groq(
        self, prompt: str, context: str, system_prompt: str, chat_history: list
    ) -> dict:
        """Call Groq API (OpenAI-compatible, free tier with Llama 3.3 70B)."""
        if not self.groq_client:
            raise ValueError("Groq API key not configured")

        import asyncio
        messages = []

        sys_msg = system_prompt or "You are DocuMind AI, an intelligent document assistant. You help users understand their documents, answer questions, and provide insights. Always be accurate and cite sources when available."
        if context:
            sys_msg += f"\n\nRelevant document context:\n{context}\n\nUse this context to answer the user's question. If the context doesn't contain relevant information, say so honestly."
        messages.append({"role": "system", "content": sys_msg})

        if chat_history:
            for msg in chat_history[-10:]:
                messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": prompt})

        response = await asyncio.wait_for(
            self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            ),
            timeout=30
        )

        return {
            "reply": response.choices[0].message.content,
            "tokens_used": response.usage.total_tokens if response.usage else None,
            "model_used": "Llama 3.3 70B (Groq)"
        }

    def _offline_response(self, prompt: str, context: str) -> dict:
        """Generate a basic extractive response when all APIs fail. No API key needed."""
        if not context:
            return {
                "reply": "⚠️ **All AI providers are unavailable** (API quotas exhausted).\n\nTo fix this, you need at least one working API key:\n\n1. **Groq (FREE, recommended)**: Get a key at [console.groq.com/keys](https://console.groq.com/keys)\n2. **Gemini**: Get a key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)\n3. **OpenAI**: Get a key at [platform.openai.com/api-keys](https://platform.openai.com/api-keys)\n\nAdd the key to `server/.env` and restart the server.",
                "tokens_used": None,
                "model_used": "Offline (no API)"
            }

        # Extract relevant sentences from context
        query_words = set(prompt.lower().split())
        sentences = re.split(r'(?<=[.!?])\s+', context)
        scored = []
        for sent in sentences:
            sent = sent.strip()
            if len(sent) < 20:
                continue
            score = sum(1 for w in query_words if w.lower() in sent.lower())
            scored.append((score, sent))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = [s for _, s in scored[:5] if _ > 0]

        if top:
            reply = "📄 **Extracted from your documents** (AI unavailable — showing relevant excerpts):\n\n"
            for i, sent in enumerate(top, 1):
                reply += f"> {sent}\n\n"
            reply += "\n---\n*⚠️ This is a text extraction, not an AI answer. Add a free Groq API key in `server/.env` for full AI responses.*"
        else:
            reply = f"📄 **Document excerpt** (AI unavailable):\n\n> {context[:500]}...\n\n---\n*⚠️ Add a free Groq API key in `server/.env` for AI-powered answers.*"

        return {
            "reply": reply,
            "tokens_used": None,
            "model_used": "Offline (extractive)"
        }

    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using Gemini (primary) or OpenAI (fallback)."""
        # Try Gemini embeddings first (since OpenAI may be unreachable)
        if settings.GEMINI_API_KEY:
            try:
                return await self._gemini_embeddings(texts)
            except Exception as e:
                print(f"⚠️ Gemini embeddings failed: {e}")

        # Fallback to OpenAI
        if self.openai_client:
            try:
                import asyncio
                response = await asyncio.wait_for(
                    self.openai_client.embeddings.create(
                        model="text-embedding-3-small",
                        input=texts
                    ),
                    timeout=15
                )
                return [item.embedding for item in response.data]
            except Exception as e:
                print(f"⚠️ OpenAI embeddings failed: {e}")

        raise ValueError("No embedding provider available. Check your API keys.")

    async def _gemini_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using Gemini embedding model."""
        import asyncio
        results = []
        for text in texts:
            result = await asyncio.to_thread(
                genai.embed_content,
                model="models/gemini-embedding-001",
                content=text,
                task_type="retrieval_document"
            )
            results.append(result['embedding'])
        return results

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

        try:
            result = await self.generate_response(prompt, model=model, system_prompt=system_prompt)
        except Exception:
            result = self._offline_response(prompt, context)

        # Check if offline mode returned non-JSON
        if result.get("model_used", "").startswith("Offline"):
            return self._generate_offline_quiz(context, num_questions)

        try:
            reply = result["reply"].strip()
            if reply.startswith("```"):
                reply = reply.split("\n", 1)[1].rsplit("```", 1)[0]
            quiz_data = json.loads(reply)
            return quiz_data
        except json.JSONDecodeError:
            return self._generate_offline_quiz(context, num_questions)

    def _generate_offline_quiz(self, context: str, num_questions: int) -> dict:
        """Generate basic quiz from text without AI."""
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', context) if len(s.strip()) > 30]
        questions = []
        for i, sent in enumerate(sentences[:num_questions]):
            # Find a key phrase to blank out
            words = sent.split()
            if len(words) > 4:
                key_idx = len(words) // 2
                answer = words[key_idx]
                blanked = " ".join(words[:key_idx] + ["_____"] + words[key_idx+1:])
                options = [answer, words[0], words[-1], "None of the above"]
                questions.append({
                    "question": f"Fill in the blank: {blanked}",
                    "options": options,
                    "correct": 0,
                    "explanation": f"The original text states: '{sent[:100]}...'"
                })
        return {"questions": questions if questions else [{"question": "No quiz could be generated (AI unavailable). Add a Groq API key to server/.env", "options": ["OK"], "correct": 0, "explanation": "Get a free key at console.groq.com/keys"}]}

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

        try:
            result = await self.generate_response(prompt, model=model, system_prompt=system_prompt)
        except Exception:
            result = self._offline_response(prompt, context)

        if result.get("model_used", "").startswith("Offline"):
            return self._generate_offline_flashcards(context, num_cards)

        try:
            reply = result["reply"].strip()
            if reply.startswith("```"):
                reply = reply.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(reply)
        except json.JSONDecodeError:
            return self._generate_offline_flashcards(context, num_cards)

    def _generate_offline_flashcards(self, context: str, num_cards: int) -> dict:
        """Generate basic flashcards from text without AI."""
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', context) if len(s.strip()) > 20]
        cards = []
        for i, sent in enumerate(sentences[:num_cards]):
            cards.append({
                "front": f"Key fact #{i+1} from your document:",
                "back": sent[:200]
            })
        return {"cards": cards if cards else [{"front": "AI unavailable", "back": "Add a free Groq API key to server/.env (console.groq.com/keys)"}]}

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

        try:
            result = await self.generate_response(prompt, model=model, system_prompt=system_prompt)
        except Exception:
            result = self._offline_response(prompt, context)

        if result.get("model_used", "").startswith("Offline"):
            return self._generate_offline_summary(context)

        try:
            reply = result["reply"].strip()
            if reply.startswith("```"):
                reply = reply.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(reply)
        except json.JSONDecodeError:
            return {"summary": result["reply"], "key_points": []}

    def _generate_offline_summary(self, context: str) -> dict:
        """Generate a basic summary from text without AI."""
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', context) if len(s.strip()) > 20]
        # Take first few sentences as summary, rest as key points
        summary = " ".join(sentences[:3]) if sentences else context[:500]
        key_points = sentences[3:8] if len(sentences) > 3 else sentences[:3]
        return {
            "summary": f"(Auto-extracted, AI unavailable) {summary}",
            "key_points": key_points if key_points else ["Add a free Groq API key to server/.env for AI summaries"]
        }


llm_service = LLMService()
