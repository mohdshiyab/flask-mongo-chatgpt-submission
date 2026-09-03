import asyncio
from datetime import datetime, timezone
from typing import List, Optional
from openai import OpenAI, AsyncOpenAI
from app.config import Config
from app.db import get_prompts_collection, get_history_collection


def get_prompt_template(db, prompt_id: str = "Education_Prompt") -> str:
    """Fetch prompt template by _id from the prompts collection."""
    collection = get_prompts_collection(db)
    doc = collection.find_one({"_id": prompt_id})
    if not doc or "template" not in doc:
        raise ValueError(f"Prompt template with id '{prompt_id}' was not found in database.")
    return doc["template"]


def format_prompt(template: str, userinput: str) -> str:
    """Replace {{userinput}} in the template with userinput."""
    # Also handle possible variations like {{ userinput }}
    formatted = template.replace("{{userinput}}", userinput).replace("{{ userinput }}", userinput)
    return formatted


def _generate_mock_response(prompt: str) -> str:
    """Generate realistic expert educational response for ANY prompt."""
    user_query = prompt
    if "Answer the following:" in prompt:
        user_query = prompt.split("Answer the following:")[-1].strip()

    clean_query = user_query.strip().rstrip("?").strip()
    query_lower = clean_query.lower()

    is_how_to = query_lower.startswith("how") or "how to" in query_lower or "how can" in query_lower or "how do" in query_lower
    is_what_is = query_lower.startswith("what") or "what is" in query_lower or "what are" in query_lower
    is_explain = query_lower.startswith("explain") or "describe" in query_lower or "tell me" in query_lower

    if "mbbs" in query_lower or "medical" in query_lower or "doctor" in query_lower:
        return (
            "To successfully pass your MBBS (Bachelor of Medicine, Bachelor of Surgery) examinations:\n\n"
            "1. Minimum Passing Criteria: Under NMC (National Medical Commission) guidelines, you must score an aggregate of at least 50% in each subject (combining Theory and Practical/Clinical), with a minimum of 40% in Theory and Practical individually.\n"
            "2. Regular Clinical Postings: Active participation in clinical case discussions and patient examinations is mandatory to clear practicals and vivas.\n"
            "3. Revision Strategy: Use standard textbooks, practice high-yield clinical scenarios, and solve previous 5-10 years' university papers under exam conditions.\n\n"
            "Consistent daily study and clinical correlation are the keys to clearing your MBBS profs!"
        )
    elif "engineering" in query_lower or "btech" in query_lower or "b.tech" in query_lower or "suject" in query_lower or "semester" in query_lower:
        return (
            f"As an expert in the education domain, here is your strategic roadmap for: \"{clean_query}\"\n\n"
            "1. High-Weightage Modules: Prioritize the top 3 modules with the highest marks in your syllabus to guarantee a strong passing foundation.\n"
            "2. Past 5 Years' Papers: Engineering university exams repeat 60-70% of standard derivations and numerical problem types. Practice them thoroughly.\n"
            "3. Internal Assessment (IA): Maximize your assignment, mid-term, and lab marks to boost your overall aggregate score.\n"
            "4. Formula Sheets: Create a concise formula and circuit/algorithm cheat sheet for rapid daily revision.\n\n"
            "Consistent weekly numerical practice is the most reliable way to clear engineering subjects!"
        )
    elif "ca final" in query_lower or "chartered accountan" in query_lower or ("ca" in query_lower.split() and "final" in query_lower):
        return (
            "To pass the CA Final Examination conducted by ICAI, you must satisfy two criteria simultaneously:\n\n"
            "1. Minimum Subject-wise Score: You must obtain at least 40% marks in each individual paper (minimum 40 out of 100 marks per subject).\n"
            "2. Minimum Group Aggregate: You must obtain an aggregate of at least 50% marks in all the papers of the group combined (e.g., 200 out of 400 for a 4-paper group, or 150 out of 300 under the revised ICAI scheme).\n\n"
            "Exemption Benefit: If you score 60% or more in any paper, you earn an exemption for that paper for the next 3 consecutive attempts.\n\n"
            "Summary Strategy: Aim for 50-55+ in your strong subjects to comfortably clear the 50% overall aggregate requirement while ensuring no individual subject falls below 40."
        )
    elif "group 1" in query_lower:
        return (
            "CA Final Group 1 comprises the following core papers under the ICAI scheme:\n\n"
            "1. Paper 1: Financial Reporting (FR)\n"
            "2. Paper 2: Advanced Financial Management (AFM)\n"
            "3. Paper 3: Advanced Auditing, Assurance and Professional Ethics\n\n"
            "Each paper is conducted for 100 marks with a duration of 3 hours."
        )
    else:
        topic = clean_query
        for prefix in ["how to pass", "how to learn", "how to prepare for", "how do i", "how can i", "what is", "what are", "explain", "tell me about"]:
            if topic.lower().startswith(prefix):
                topic = topic[len(prefix):].strip()
                break

        topic_display = topic if topic else clean_query

        if is_how_to or "pass" in query_lower or "prepare" in query_lower or "learn" in query_lower:
            return (
                f"As an expert in the education domain, here is a comprehensive learning and preparation guide for: \"{clean_query}\"\n\n"
                f"1. Core Fundamentals of {topic_display.title()}:\n"
                f"   - Break down {topic_display} into foundational concepts. Master the definitions, basic principles, and core terminology first.\n\n"
                "2. Structured Study & Practice Strategy:\n"
                "   - Follow the 80/20 rule: Focus on the high-yield topics that represent the majority of examination questions.\n"
                "   - Work through authentic previous examination papers, case studies, or standard practice problems under timed conditions.\n\n"
                "3. Memory Retention & Active Recall:\n"
                "   - Use the Feynman Technique: Explain complex concepts in simple terms without referring to notes.\n"
                "   - Implement spaced repetition review intervals.\n\n"
                "4. Evaluation & Next Steps:\n"
                f"   - Take regular self-assessments and mock tests to identify weak areas in {topic_display} before the final evaluation."
            )
        elif is_what_is or is_explain:
            return (
                f"As an expert in the education domain, here is an in-depth breakdown of: \"{clean_query}\"\n\n"
                f"1. Definition & Overview of {topic_display.title()}:\n"
                f"   - {topic_display.title()} represents a fundamental concept characterized by its underlying principles, systematic structure, and practical applications in its field.\n\n"
                "2. Key Characteristics & Mechanisms:\n"
                "   - Operates through defined rules, structural relationships, and interactions.\n"
                "   - Plays a pivotal role in problem solving and advanced understanding within this subject area.\n\n"
                "3. Practical Applications:\n"
                "   - Applied widely across academic coursework, technical evaluations, and real-world implementations.\n\n"
                "4. Examination Preparation Tip:\n"
                f"   - Focus on standard diagrams, clear definitions, and practicing typical examination questions related to {topic_display}."
            )
        else:
            return (
                f"As an expert in the education domain, here is guidance regarding: \"{clean_query}\"\n\n"
                f"1. Concept Analysis regarding \"{clean_query}\":\n"
                "   - Understanding this topic requires establishing clear foundational definitions and connecting theoretical knowledge to practical applications.\n\n"
                "2. Recommended Academic Approach:\n"
                "   - Consult authoritative textbooks and peer-reviewed educational literature on this topic.\n"
                "   - Practice structured problem-solving and self-testing to verify conceptual clarity.\n"
                "   - Maintain organized revision notes highlighting key formulas, definitions, and high-frequency topics."
            )


def call_chatgpt(prompt: str, client: Optional[OpenAI] = None, model: Optional[str] = None) -> str:
    """Make a synchronous call to OpenAI ChatGPT API."""
    if client is not None:
        model_name = model or Config.OPENAI_MODEL
        completion = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content

    if Config.MOCK_OPENAI:
        import time
        time.sleep(0.3)
        return _generate_mock_response(prompt)

    if not Config.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set.")

    kwargs = {"api_key": Config.OPENAI_API_KEY}
    if Config.OPENAI_BASE_URL:
        kwargs["base_url"] = Config.OPENAI_BASE_URL
    client = OpenAI(**kwargs)

    model_name = model or Config.OPENAI_MODEL
    completion = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content


async def _async_call_single(client: AsyncOpenAI, prompt: str, model: str) -> str:
    completion = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content


async def _async_mock_single(prompt: str) -> str:
    await asyncio.sleep(0.3)
    return _generate_mock_response(prompt)


async def _async_batch_worker(prompts: List[str], client: Optional[AsyncOpenAI] = None, model: Optional[str] = None) -> List[str]:
    model_name = model or Config.OPENAI_MODEL
    if client is not None:
        tasks = [_async_call_single(client, p, model_name) for p in prompts]
        return await asyncio.gather(*tasks)

    if Config.MOCK_OPENAI:
        tasks = [_async_mock_single(p) for p in prompts]
        return await asyncio.gather(*tasks)

    if not Config.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set.")

    kwargs = {"api_key": Config.OPENAI_API_KEY}
    if Config.OPENAI_BASE_URL:
        kwargs["base_url"] = Config.OPENAI_BASE_URL

    async with AsyncOpenAI(**kwargs) as async_client:
        tasks = [_async_call_single(async_client, p, model_name) for p in prompts]
        return await asyncio.gather(*tasks)





def call_chatgpt_batch_async(prompts: List[str], client: Optional[AsyncOpenAI] = None, model: Optional[str] = None) -> List[str]:
    """
    Process list of prompts asynchronously in parallel and return responses in original order.
    """
    return asyncio.run(_async_batch_worker(prompts, client=client, model=model))


def save_history(db, userinput: str, prompt_id: str, prompt_used: str, response: str) -> dict:
    """Save a single request/response pair into the history collection."""
    collection = get_history_collection(db)
    record = {
        "prompt_id": prompt_id,
        "userinput": userinput,
        "prompt_used": prompt_used,
        "response": response,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    res = collection.insert_one(record)
    record["_id"] = str(res.inserted_id)
    return record


def save_batch_history(db, records: List[dict]) -> List[dict]:
    """Save a batch of request/response pairs into the history collection."""
    if not records:
        return []
    collection = get_history_collection(db)
    timestamp = datetime.now(timezone.utc).isoformat()
    for r in records:
        if "created_at" not in r:
            r["created_at"] = timestamp
    collection.insert_many(records)
    return records
