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
    """Generate realistic expert response for testing/demo when OpenAI quota is exhausted."""
    prompt_lower = prompt.lower()
    user_query = prompt
    if "Answer the following:" in prompt:
        user_query = prompt.split("Answer the following:")[-1].strip()

    if "mbbs" in prompt_lower or "medical" in prompt_lower:
        return (
            "To successfully pass your MBBS (Bachelor of Medicine, Bachelor of Surgery) examinations:\n\n"
            "1. Minimum Passing Criteria: Under NMC (National Medical Commission) guidelines, you must score an aggregate of at least 50% in each subject (combining Theory and Practical/Clinical), with a minimum of 40% in Theory and Practical individually.\n"
            "2. Regular Clinical Postings: Active participation in clinical case discussions and patient examinations is mandatory to clear practicals and vivas.\n"
            "3. Revision Strategy: Use standard textbooks, practice high-yield clinical scenarios, and solve previous 5-10 years' university papers under exam conditions.\n\n"
            "Consistent daily study and clinical correlation are the keys to clearing your MBBS profs!"
        )
    elif "group 1" in prompt_lower:
        return (
            "CA Final Group 1 comprises the following core papers under the ICAI scheme:\n\n"
            "1. Paper 1: Financial Reporting (FR)\n"
            "2. Paper 2: Advanced Financial Management (AFM)\n"
            "3. Paper 3: Advanced Auditing, Assurance and Professional Ethics\n\n"
            "Each paper is conducted for 100 marks with a duration of 3 hours."
        )
    elif "aggregate" in prompt_lower and "ca" in prompt_lower:
        return (
            "The CA Exam Aggregate Rule requires candidates to score an overall average of at least 50% across all papers in the group (e.g., 150/300 or 200/400), in addition to scoring at least 40% in each individual subject."
        )
    elif "ca final" in prompt_lower or ("ca" in prompt_lower and ("score" in prompt_lower or "pass" in prompt_lower)):
        return (
            "To pass the CA Final Examination conducted by ICAI, you must satisfy two criteria simultaneously:\n\n"
            "1. Minimum Subject-wise Score: You must obtain at least 40% marks in each individual paper (minimum 40 out of 100 marks per subject).\n"
            "2. Minimum Group Aggregate: You must obtain an aggregate of at least 50% marks in all the papers of the group combined (e.g., 200 out of 400 for a 4-paper group, or 150 out of 300 under the revised ICAI scheme).\n\n"
            "Exemption Benefit: If you score 60% or more in any paper, you earn an exemption for that paper for the next 3 consecutive attempts.\n\n"
            "Summary Strategy: Aim for 50-55+ in your strong subjects to comfortably clear the 50% overall aggregate requirement while ensuring no individual subject falls below 40."
        )
    else:
        return (
            f"As an expert in the education domain, here is guidance regarding your inquiry:\n\n"
            f"Regarding: \"{user_query}\"\n\n"
            "Key recommendations for academic success:\n"
            "1. Master the core syllabus and focus on high-weightage topics first.\n"
            "2. Practice past 5 years' university/board question papers under timed exam conditions.\n"
            "3. Maintain scheduled revision intervals using spaced repetition.\n"
            "4. Seek regular clarification from mentors and evaluate your performance through mock assessments."
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
    client = OpenAI(api_key=Config.OPENAI_API_KEY)

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
        # Simulate true concurrent async API processing with asyncio.gather
        tasks = [_async_mock_single(p) for p in prompts]
        return await asyncio.gather(*tasks)

    if not Config.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set.")

    async with AsyncOpenAI(api_key=Config.OPENAI_API_KEY) as async_client:
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
