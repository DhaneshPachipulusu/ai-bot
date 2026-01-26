"""
Conversational Interview Routes
===============================
API endpoints for the conversational interview system.
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime

from app.models.interview_context import (
    StartInterviewRequest,
    StartInterviewResponse,
    RespondRequest,
    RespondResponse,
    EndInterviewRequest,
    EndInterviewResponse,
    InterviewMessage,
    InterviewStateResponse,
    InterviewSummary,
    PerformanceHint,
    ResponseType,
    InterviewStage,
)
from app.services.interview_state import (
    create_interview_context,
    load_context,
    save_context,
    add_interviewer_turn,
    add_candidate_turn,
    update_topics,
    update_performance,
    mark_project_probed,
    complete_interview,
    should_transition_stage,
    transition_to_next_stage,
    get_progress_percent,
    get_time_remaining,
    get_time_elapsed,
)
from app.services.interview_ai import (
    generate_interviewer_response,
    generate_greeting,
    generate_closing_message,
    build_interview_message,
    analyze_answer,
)
from app import database as db


router = APIRouter(prefix="/interview", tags=["Conversational Interview"])


# ======================
# START INTERVIEW
# ======================

@router.post("/start", response_model=StartInterviewResponse)
async def start_interview(request: StartInterviewRequest):
    """
    Start a new conversational interview.
    
    - For resume mode: Pass parsed_resume
    - For career mode: Pass target_role and experience_level
    """
    
    # Create interview context
    context = create_interview_context(
        user_id=request.user_id,
        mode=request.mode,
        parsed_resume=request.parsed_resume,
        target_role=request.target_role,
        experience_level=request.experience_level,
        difficulty=request.difficulty,
        max_questions=request.max_questions,
        max_duration_mins=request.max_duration_mins,
    )
    
    # Generate greeting message
    greeting = generate_greeting(context)
    
    # Add to conversation history
    context = add_interviewer_turn(
        context=context,
        text=greeting.text,
        response_type=ResponseType.GREETING,
        topic=None,
    )
    
    # Save to database for reports
    # Using existing db function signature: save_interview(user_id, interview_id, questions)
    try:
        db.save_interview(
            request.user_id,
            context.interview_id,
            []  # Conversational mode doesn't have pre-set questions
        )
    except Exception as e:
        print(f"Database save warning: {e}")
        # Continue even if db save fails - we have file-based backup
    
    # Build state response
    state_response = InterviewStateResponse(
        stage=context.state.current_stage,
        progress_percent=get_progress_percent(context),
        topics_covered=context.state.topics_covered,
        current_topic=context.state.current_topic,
        questions_asked=context.state.questions_asked,
        questions_remaining=context.state.max_questions - context.state.questions_asked,
        time_elapsed_mins=get_time_elapsed(context),
        time_remaining_mins=get_time_remaining(context),
    )
    
    return StartInterviewResponse(
        interview_id=context.interview_id,
        message=greeting,
        state=state_response,
    )


# ======================
# RESPOND (Main Conversation Loop)
# ======================

@router.post("/respond", response_model=RespondResponse)
async def respond_to_answer(request: RespondRequest):
    """
    Process candidate's answer and generate AI response.
    
    This is the main conversation loop endpoint.
    """
    
    # Load interview context
    context = load_context(request.interview_id)
    if not context:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # Verify user
    if context.user_id != request.user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Check if interview is completed
    if context.state.is_completed:
        raise HTTPException(status_code=400, detail="Interview already completed")
    
    # Get the last interviewer question for context
    last_question = ""
    for turn in reversed(context.conversation):
        if turn.role == "interviewer":
            last_question = turn.text
            break
    
    # Analyze the candidate's answer
    analysis = analyze_answer(
        question=last_question,
        answer=request.answer,
        stage=context.state.current_stage,
        topic=context.state.current_topic,
    )
    
    # Add candidate's turn to conversation
    context = add_candidate_turn(
        context=context,
        text=request.answer,
        duration_seconds=request.answer_duration_seconds,
        analysis=analysis,
    )
    
    # Update performance tracking
    answer_quality = analysis.get("quality", "adequate")
    context = update_performance(
        context=context,
        answer_quality=answer_quality,
        strong_area=analysis.get("strong_topic"),
        weak_area=analysis.get("weak_topic") if answer_quality in ["weak", "incomplete"] else None,
    )
    
    # Update topics if covered
    if analysis.get("topic_covered") and context.state.current_topic:
        context = update_topics(
            context=context,
            topics_covered=[context.state.current_topic],
            skills_probed=[context.state.current_topic] if context.state.current_topic in context.probe_areas.skills else None,
        )
    
    # Check if we should transition stages
    if should_transition_stage(context):
        context = transition_to_next_stage(context)
    
    # Check if interview should end (time or questions)
    should_end = (
        context.state.questions_asked >= context.state.max_questions or
        get_time_remaining(context) <= 0 or
        context.state.current_stage == InterviewStage.COMPLETED
    )
    
    if should_end and context.state.current_stage != InterviewStage.CLOSING:
        # Force transition to closing
        context.state.current_stage = InterviewStage.CLOSING
        save_context(context)
    
    # Generate AI response
    ai_response = generate_interviewer_response(context, request.answer)
    
    # Build interview message
    message = build_interview_message(
        ai_response=ai_response,
        stage=context.state.current_stage,
        topic=ai_response.get("internal_analysis", {}).get("suggested_next_topic"),
    )
    
    # Update current topic
    new_topic = ai_response.get("internal_analysis", {}).get("suggested_next_topic")
    if new_topic:
        context.state.current_topic = new_topic
    
    # Add interviewer's turn
    context = add_interviewer_turn(
        context=context,
        text=message.text,
        response_type=message.type,
        topic=new_topic,
    )
    
    # Check if this is the final closing message
    is_complete = (
        context.state.current_stage == InterviewStage.CLOSING and
        ai_response.get("internal_analysis", {}).get("interview_complete", False)
    )
    
    if is_complete:
        context = complete_interview(context)
        
        # Update database
        try:
            db.complete_interview(context.interview_id)
        except Exception as e:
            print(f"Database complete warning: {e}")
    
    # Save conversation to database for report
    try:
        db.update_interview_answers(context.interview_id, last_question, request.answer)
    except Exception as e:
        print(f"Database update warning: {e}")
    
    # Build state response
    state_response = InterviewStateResponse(
        stage=context.state.current_stage,
        progress_percent=get_progress_percent(context),
        topics_covered=context.state.topics_covered,
        current_topic=context.state.current_topic,
        questions_asked=context.state.questions_asked,
        questions_remaining=max(0, context.state.max_questions - context.state.questions_asked),
        time_elapsed_mins=get_time_elapsed(context),
        time_remaining_mins=get_time_remaining(context),
    )
    
    # Build performance hint
    performance_hint = None
    if answer_quality in ["weak", "incomplete"]:
        suggestion = analysis.get("suggested_follow_up") or "Try to provide more specific examples"
        performance_hint = PerformanceHint(
            answer_quality=answer_quality,
            suggestion=suggestion,
        )
    
    return RespondResponse(
        message=message,
        state=state_response,
        performance_hint=performance_hint,
        is_complete=is_complete,
    )


# ======================
# END INTERVIEW
# ======================

@router.post("/end", response_model=EndInterviewResponse)
async def end_interview(request: EndInterviewRequest):
    """
    End the interview (either by user or system).
    """
    
    # Load context
    context = load_context(request.interview_id)
    if not context:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # Verify user
    if context.user_id != request.user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Generate closing message
    closing = generate_closing_message(context)
    
    # Complete the interview
    context = complete_interview(context)
    
    # Update database
    try:
        db.complete_interview(context.interview_id)
    except Exception as e:
        print(f"Database complete warning: {e}")
    
    # Build summary
    duration = get_time_elapsed(context)
    questions_answered = len([t for t in context.conversation if t.role == "candidate"])
    
    # Determine overall performance
    good_answers = len([
        q for q in context.performance.answers_quality 
        if q.get("quality") in ["excellent", "good"]
    ])
    total_answers = len(context.performance.answers_quality)
    
    if total_answers > 0:
        good_ratio = good_answers / total_answers
        if good_ratio >= 0.7:
            overall = "Strong performance"
        elif good_ratio >= 0.4:
            overall = "Moderate performance"
        else:
            overall = "Needs improvement"
    else:
        overall = "Interview ended early"
    
    summary = InterviewSummary(
        duration_mins=duration,
        questions_answered=questions_answered,
        strong_areas=context.performance.strong_areas[:5],
        areas_to_improve=context.performance.weak_areas[:5],
        overall_performance=overall,
    )
    
    return EndInterviewResponse(
        message=closing,
        summary=summary,
        report_id=context.interview_id,  # Same as interview_id for now
    )


# ======================
# GET INTERVIEW STATUS
# ======================

@router.get("/{interview_id}/status")
async def get_interview_status(interview_id: str, user_id: int):
    """
    Get current interview status.
    """
    
    context = load_context(interview_id)
    if not context:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    if context.user_id != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    return {
        "interview_id": interview_id,
        "stage": context.state.current_stage,
        "is_completed": context.state.is_completed,
        "is_paused": context.state.is_paused,
        "progress_percent": get_progress_percent(context),
        "questions_asked": context.state.questions_asked,
        "time_elapsed_mins": get_time_elapsed(context),
        "time_remaining_mins": get_time_remaining(context),
        "topics_covered": context.state.topics_covered,
    }


# ======================
# GET CONVERSATION HISTORY
# ======================

@router.get("/{interview_id}/history")
async def get_conversation_history(interview_id: str, user_id: int):
    """
    Get full conversation history.
    """
    
    context = load_context(interview_id)
    if not context:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    if context.user_id != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    return {
        "interview_id": interview_id,
        "candidate": context.candidate.model_dump(),
        "conversation": [turn.model_dump() for turn in context.conversation],
        "performance": context.performance.model_dump(),
    }


# ======================
# PAUSE/RESUME INTERVIEW
# ======================

@router.post("/{interview_id}/pause")
async def pause_interview(interview_id: str, user_id: int):
    """Pause the interview."""
    
    context = load_context(interview_id)
    if not context:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    if context.user_id != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    context.state.is_paused = True
    save_context(context)
    
    return {"status": "paused", "interview_id": interview_id}


@router.post("/{interview_id}/resume")
async def resume_interview(interview_id: str, user_id: int):
    """Resume the interview."""
    
    context = load_context(interview_id)
    if not context:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    if context.user_id != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    context.state.is_paused = False
    save_context(context)
    
    # Get last interviewer message to continue
    last_message = None
    for turn in reversed(context.conversation):
        if turn.role == "interviewer":
            last_message = turn.text
            break
    
    return {
        "status": "resumed",
        "interview_id": interview_id,
        "continue_with": last_message,
    }