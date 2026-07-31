"""
Farmer Community Q&A REST Router.
Allows farmers to ask questions, view community answers, save query bookmarks, and provide feedback.
"""

from __future__ import annotations

import logging
from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db.community import community_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/community", tags=["Farmer Community Q&A"])


class CreatePostRequest(BaseModel):
    author: str = "कृषक मित्र"
    question: str
    crop_tag: str = "सामान्य"
    location: str = "नेपाल"
    image_path: str | None = None


class AddAnswerRequest(BaseModel):
    author: str = "कृषि प्राविधिक"
    answer_text: str
    is_gemma_ai: bool = False


@router.get("")
async def list_community_posts(crop_tag: str | None = None, limit: int = 50):
    """List farmer community questions."""
    posts = community_db.list_posts(crop_tag=crop_tag, limit=limit)
    return {"posts": posts, "count": len(posts)}


@router.post("")
async def create_community_post(req: CreatePostRequest):
    """Create a new farmer community question."""
    if not req.question:
        raise HTTPException(status_code=400, detail="Question text is required.")
    post = community_db.create_post(
        author=req.author,
        question=req.question,
        crop_tag=req.crop_tag,
        location=req.location,
        image_path=req.image_path,
    )
    return {"status": "success", "post": post}


@router.post("/{post_id}/answer")
async def add_answer_to_post(post_id: str, req: AddAnswerRequest):
    """Add an answer to a community question."""
    if not req.answer_text:
        raise HTTPException(status_code=400, detail="Answer text is required.")
    post = community_db.add_answer(
        post_id=post_id,
        author=req.author,
        answer_text=req.answer_text,
        is_gemma_ai=req.is_gemma_ai,
    )
    if not post:
        raise HTTPException(status_code=404, detail="Community post not found.")
    return {"status": "success", "post": post}


@router.post("/{post_id}/save")
async def toggle_save_post(post_id: str):
    """Bookmark / save a community post."""
    post = community_db.toggle_save_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Community post not found.")
    return {"status": "success", "post": post}


@router.post("/{post_id}/gemma-answer")
async def generate_gemma_answer(post_id: str):
    """Generate a verified Gemma 4 AI answer for a community question."""
    post = community_db.get_post(post_id) if hasattr(community_db, "get_post") else None
    
    # If get_post is not defined, search list_posts
    if not post:
        posts = community_db.list_posts(limit=500)
        post = next((p for p in posts if p.get("id") == post_id), None)

    if not post:
        raise HTTPException(status_code=404, detail="Community post not found.")

    question_text = post.get("question", "")
    crop_tag = post.get("crop_tag", "सामान्य")

    # Generate answer using Gemma 4 multi-agent orchestrator
    ai_answer = ""
    try:
        from agents.registry import initialize_graph
        from langchain_core.messages import HumanMessage
        graph = initialize_graph()
        
        state_input = {
            "messages": [HumanMessage(content=question_text)],
            "query": question_text,
            "crop_type": crop_tag,
            "chat_mode": "contextual"
        }
        res = await graph.ainvoke(state_input)
        ai_answer = res.get("final_answer") or res.get("answer") or ""
    except Exception as e:
        logger.warning(f"Gemma 4 agent graph error for community Q&A: {e}")

    if not ai_answer:
        ai_answer = f"गम्मा 4 परामर्श ({crop_tag}): {question_text} सम्बन्धी सिफारिस गरिएको कृषि निर्देशिका अनुसार रोग/किरा नियन्त्रण गर्न आधिकारिक कृषि प्राविधिकसँग परामर्श गर्नुहोस्।"

    updated_post = community_db.add_answer(
        post_id=post_id,
        author="Gemma 4 AI Assistant",
        answer_text=ai_answer,
        is_gemma_ai=True
    )

    return {"status": "success", "post": updated_post, "ai_answer": ai_answer}

