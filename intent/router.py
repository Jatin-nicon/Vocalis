from __future__ import annotations
from dataclasses import dataclass
from typing import Callable
from .rules import match_command, IntentResult
from .knowledge import match_knowledge_query
from .semantic_router import resolve_semantic_intent, SemanticDecision
from .classifier import is_informational_question
from .llm_fallback import answer_question_with_llm
from config import settings


@dataclass
class DispatchResult:
    category: str  # "command", "dictate", "mode", "answer", "unknown"
    action_name: str
    message: str
    text_to_paste: str = ""


class IntentRouter:
    """
    Intelligent Hybrid Router:
    1. Local fast path (< 1ms) for natural commands and offline queries.
    2. Reliable Question vs. PC Task differentiation: answers informational questions aloud.
    3. Memory of previous answer so the user can say "can you type it down".
    4. Active text editing (backspaces, delete word, delete sentence, undo) in both command and typing modes.
    5. Dynamic semantic understanding for flexible phrasing.
    """
    def __init__(self, dictation_handler: Callable[[str], str] | None = None):
        self.dictation_handler = dictation_handler
        self.typing_mode = False
        self.last_answer: str = ""

    def route_and_execute(self, text: str) -> DispatchResult:
        raw = text.strip()
        if not raw:
            return DispatchResult("none", "none", "No speech detected.")

        # 1. Check ultra-fast local deterministic rules (< 1ms)
        rule_result: IntentResult = match_command(raw)

        if rule_result.matched:
            # Handle "Type it down" / "Can you type it down"
            if rule_result.category == "type_last_answer":
                if self.last_answer:
                    msg = "Typed answer."
                    if self.dictation_handler:
                        msg = self.dictation_handler(self.last_answer)
                    return DispatchResult("dictate", "type_last_answer", "Typed it down for you.", text_to_paste=self.last_answer)
                else:
                    return DispatchResult("answer", "no_last_answer", "There is no previous answer to type down. Ask a question first or say 'type [your text]'.")

            # Handle Typing Mode Toggles
            if rule_result.category == "mode":
                if rule_result.action_name == "start_typing":
                    self.typing_mode = True
                    return DispatchResult("mode", "start_typing", rule_result.payload)
                elif rule_result.action_name == "stop_typing":
                    self.typing_mode = False
                    return DispatchResult("mode", "stop_typing", rule_result.payload)

            # Handle Explicit Dictation: "type ...", "write down ...", "type down ..."
            if rule_result.category == "dictate":
                content = rule_result.payload
                msg = "Dictated text."
                if self.dictation_handler:
                    msg = self.dictation_handler(content)
                return DispatchResult("dictate", "dictate", msg, text_to_paste=content)

            # Handle Windows PC Commands (Volume, Media, Tabs, Editing, Apps, etc.)
            if rule_result.category == "command" and rule_result.execute:
                result_msg = rule_result.execute()
                return DispatchResult("command", rule_result.action_name, result_msg)

        # 2. Check instant local offline knowledge (Time, Date, Battery, Identity, Jokes, Volume status, etc.)
        knowledge_ans = match_knowledge_query(raw)
        if knowledge_ans:
            self.last_answer = knowledge_ans
            return DispatchResult("answer", "knowledge_answer", knowledge_ans)

        # 3. If in continuous typing mode:
        if self.typing_mode:
            # Intercept editing controls and stop commands so user doesn't paste them
            rule_check = match_command(raw)
            if rule_check.matched:
                if rule_check.category == "mode" and rule_check.action_name == "stop_typing":
                    self.typing_mode = False
                    return DispatchResult("mode", "stop_typing", rule_check.payload)
                if rule_check.category == "command" and rule_check.action_name in (
                    "backspace", "delete_word", "delete_sentence", "undo", "delete_all", "new_line"
                ):
                    res_msg = rule_check.execute() if rule_check.execute else "Done."
                    return DispatchResult("command", rule_check.action_name, res_msg)
                if rule_check.category == "type_last_answer":
                    if self.last_answer:
                        if self.dictation_handler:
                            self.dictation_handler(self.last_answer)
                        return DispatchResult("dictate", "type_last_answer", "Typed it down for you.", text_to_paste=self.last_answer)
                    else:
                        return DispatchResult("answer", "no_last_answer", "There is no previous answer to type down.")

            # Otherwise normal speech is pasted into focused window
            msg = "Typed text."
            if self.dictation_handler:
                msg = self.dictation_handler(raw)
            return DispatchResult("dictate", "typing_mode_paste", msg, text_to_paste=raw)

        # 4. Question vs Command Differentiation:
        # Check if the user is asking an informational question/inquiry to be answered aloud
        is_q, query_for_llm = is_informational_question(raw)
        if is_q:
            ai_ans = answer_question_with_llm(query_for_llm)
            if ai_ans:
                self.last_answer = ai_ans
                return DispatchResult("answer", "ai_answer", ai_ans)
            else:
                fallback_msg = "I couldn't retrieve an answer right now. Please check your internet connection."
                return DispatchResult("answer", "ai_fallback", fallback_msg)

        # 5. Dynamic Semantic Router (Understands ANY natural phrasing, decides Task vs Answer)
        semantic_dec: SemanticDecision = resolve_semantic_intent(raw)

        if semantic_dec.intent_type == "type_last_answer":
            if self.last_answer:
                msg = "Typed answer."
                if self.dictation_handler:
                    msg = self.dictation_handler(self.last_answer)
                return DispatchResult("dictate", "type_last_answer", "Typed it down for you.", text_to_paste=self.last_answer)
            else:
                return DispatchResult("answer", "no_last_answer", "There is no previous answer to type down. Ask a question first or say 'type [your text]'.")

        elif semantic_dec.intent_type in ("task", "command"):
            return DispatchResult("command", semantic_dec.action_name, semantic_dec.message)

        elif semantic_dec.intent_type == "mode":
            if semantic_dec.action_name == "start_typing":
                self.typing_mode = True
            elif semantic_dec.action_name == "stop_typing":
                self.typing_mode = False
            return DispatchResult("mode", semantic_dec.action_name, semantic_dec.message)

        elif semantic_dec.intent_type == "dictate":
            content = semantic_dec.text_to_paste or raw
            msg = "Dictated text."
            if self.dictation_handler:
                msg = self.dictation_handler(content)
            return DispatchResult("dictate", "dictate", msg, text_to_paste=content)

        elif semantic_dec.intent_type == "answer":
            self.last_answer = semantic_dec.message
            return DispatchResult("answer", semantic_dec.action_name, semantic_dec.message)

        # 5. If auto_paste_unmatched is explicitly enabled in config
        if getattr(settings, "auto_paste_unmatched", False):
            msg = "Pasted text."
            if self.dictation_handler:
                msg = self.dictation_handler(raw)
            return DispatchResult("dictate", "auto_paste", msg, text_to_paste=raw)

        # 6. Default response: inform user with clear spoken guidance
        return DispatchResult(
            "unknown",
            "unknown",
            "I didn't recognize that command. Say 'help' to hear commands, or 'type' to dictate.",
        )
