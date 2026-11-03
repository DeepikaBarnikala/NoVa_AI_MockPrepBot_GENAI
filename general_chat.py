
import streamlit as st
import chat_history as history


# =========================================================
# 1. GENERAL CHAT SYSTEM PROMPT
# =========================================================

GENERAL_CHAT_PROMPT = """
You are NOVA, a helpful, intelligent, friendly AI assistant.

Your role is to answer questions naturally and help users learn,
solve problems, write code, and complete practical tasks.

RESPONSE RULES:

1. Answer the user's latest question directly.
2. Use previous messages to understand follow-up questions.
3. Never behave like an interviewer unless explicitly requested.
4. Explain technical concepts in simple, beginner-friendly English.
5. For coding requests, provide correct, readable, working code.
6. For dry runs, show the input, variable changes, loop iterations,
   and final output step by step.
7. For debugging, identify the likely cause and explain the fix.
8. For study plans, provide realistic daily tasks and clear priorities.
9. If the user requests a PDF or another file, create the actual file
   when the application provides file-generation capabilities.
   Never claim that a file was created if it was not.
10. For current events, weather, cyclones, news, and live information,
    use verified current sources if tools are available. If they are
    unavailable, clearly explain that you cannot verify current facts.
11. Never invent facts, execution results, sources, or capabilities.
12. Use headings, bullet points, examples, and code blocks when useful.
13. Do not repeat the entire previous answer unnecessarily.
14. If the question is ambiguous, ask a relevant clarification question.
15. Do not expose internal API responses, SDK objects, metadata,
    hidden reasoning, or implementation details to the user.

Write naturally, as a knowledgeable tutor and assistant.
Prioritize accuracy, clarity, practical examples, and usefulness.
"""


# =========================================================
# 2. HELPER: EXTRACT ONLY THE GENERATED TEXT
# =========================================================

def extract_answer(response):
    """
    Extract readable text from Gemini's response object.
    Never display the complete SDK response object.
    """

    if isinstance(response, str):
        answer = response
    else:
        answer = getattr(response, "text", None)

    if not isinstance(answer, str) or not answer.strip():
        raise RuntimeError(
            "Gemini returned no readable text. Please try again."
        )

    return answer.strip()


# =========================================================
# 3. HELPER: FORMAT CONVERSATION CONTEXT
# =========================================================

def build_conversation_context(messages, max_messages=16):
    """
    Format recent saved messages for the next Gemini request.
    Database messages remain the source of truth.
    """

    recent_messages = messages[-max_messages:]
    context_lines = []

    for message in recent_messages:
        role = message.get("role", "")
        content = message.get("content", "")

        if role not in ("user", "assistant"):
            continue

        if not content:
            continue

        speaker = "User" if role == "user" else "NOVA"

        context_lines.append(
            f"{speaker}:\n{content}"
        )

    return "\n\n".join(context_lines)


# =========================================================
# 4. GENERAL CHAT PAGE
# =========================================================

def render_general_chat(client, generate_with_retry, model_name):

    st.header("💬 NOVA General Chat")

    st.caption(
        "Ask questions, learn coding, understand dry runs, "
        "debug errors, create study plans, and have natural conversations."
    )

    # -----------------------------------------------------
    # SESSION STATE
    # -----------------------------------------------------

    if "active_general_chat_id" not in st.session_state:
        st.session_state.active_general_chat_id = None

    # -----------------------------------------------------
    # LOAD GENERAL CHAT HISTORY FROM SQLITE
    # -----------------------------------------------------

    all_chats = history.list_conversations()

    general_chats = [
        chat
        for chat in all_chats
        if chat.get("chat_type") == "general"
    ]

    # -----------------------------------------------------
    # NEW CHAT
    # -----------------------------------------------------

    if st.button(
        "➕ New General Chat",
        key="new_general_chat",
        use_container_width=True,
    ):
        new_chat_id = history.create_conversation(
            title="New General Chat",
            chat_type="general",
            metadata={"mode": "general_chat"},
        )

        # Activate the new conversation.
        # Old conversations remain safely stored in SQLite.
        st.session_state.active_general_chat_id = new_chat_id

        st.rerun()

    st.divider()

    # -----------------------------------------------------
    # SELECT A PREVIOUS CONVERSATION
    # -----------------------------------------------------

    if general_chats:

        st.subheader("🕘 Saved General Conversations")

        chat_options = {
            (
                f"{chat.get('title') or 'General Chat'} "
                f"(Chat #{chat['id']})"
            ): chat["id"]
            for chat in general_chats
        }

        labels = list(chat_options.keys())

        selected_label = st.selectbox(
            "Choose a saved conversation",
            options=labels,
            key="general_chat_history_selector",
        )

        selected_id = chat_options[selected_label]

        if st.button(
            "📂 Open Selected Conversation",
            key="open_general_chat",
            use_container_width=True,
        ):
            st.session_state.active_general_chat_id = selected_id
            st.rerun()

    else:
        st.caption(
            "Your previous conversations will appear here automatically "
            "after you start chatting."
        )

    # -----------------------------------------------------
    # GET THE ACTIVE CONVERSATION
    # -----------------------------------------------------

    active_id = st.session_state.active_general_chat_id

    if active_id is None:
        st.info(
            "Click **New General Chat** to start a fresh conversation."
        )
        return

    conversation = history.get_conversation(active_id)

    if (
        not conversation
        or conversation.get("chat_type") != "general"
    ):
        st.warning(
            "This conversation could not be loaded. "
            "Please start a new General Chat."
        )

        st.session_state.active_general_chat_id = None
        return

    st.caption(
        f"Current conversation: {conversation.get('title') or 'General Chat'}"
    )

    # -----------------------------------------------------
    # LOAD ONLY THE ACTIVE CHAT'S MESSAGES
    # -----------------------------------------------------

    messages = [
        {
            "role": message["role"],
            "content": message["content"],
        }
        for message in history.get_messages(active_id)
        if message.get("role") in ("user", "assistant")
    ]

    # Display messages from this conversation only.
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # -----------------------------------------------------
    # USER INPUT
    # -----------------------------------------------------

    user_prompt = st.chat_input(
        "Ask NOVA anything...",
        key="general_chat_input",
    )

    if not user_prompt:
        return

    user_prompt = user_prompt.strip()

    if not user_prompt:
        st.warning("Please enter a question.")
        return

    # -----------------------------------------------------
    # BUILD CONTEXT BEFORE SAVING THE LATEST QUESTION
    # -----------------------------------------------------

    previous_context = build_conversation_context(
        messages,
        max_messages=16,
    )

    prompt = f"""
{GENERAL_CHAT_PROMPT}

CONVERSATION HISTORY:
{previous_context if previous_context else
"No previous messages. This is the first question in this conversation."}

LATEST USER MESSAGE:
{user_prompt}

IMPORTANT:
- Answer the latest user message.
- Use conversation history only when relevant.
- Resolve follow-up references such as "it", "that", and "explain more"
  using the previous conversation.
- Do not repeat old answers unless needed.
- Do not include SDK metadata or raw API response information.
- Return only the answer intended for the user.
"""

    # -----------------------------------------------------
    # SAVE AND DISPLAY THE USER MESSAGE
    # -----------------------------------------------------

    history.add_message(
        active_id,
        "user",
        user_prompt,
    )

    with st.chat_message("user"):
        st.markdown(user_prompt)

    # -----------------------------------------------------
    # GENERATE AND SAVE THE ASSISTANT RESPONSE
    # -----------------------------------------------------

    with st.chat_message("assistant"):

        try:
            with st.spinner("NOVA is thinking..."):

                response = generate_with_retry(
                    client=client,
                    prompt=prompt,
                    temperature=0.5,
                    max_tokens=2200,
                )

                # Critical fix:
                # Extract response.text instead of str(response).
                answer = extract_answer(response)

            st.markdown(answer)

            history.add_message(
                active_id,
                "assistant",
                answer,
            )

            # Give the conversation a useful title after its first question.
            if not messages:
                title = " ".join(user_prompt.split())[:55]

                if len(user_prompt) > 55:
                    title += "..."

                history.update_conversation(
                    active_id,
                    title=title or "General Chat",
                )

        except Exception as error:
            st.error(
                "NOVA could not generate a response. "
                "Please try again."
            )

            # Keep detailed errors in the terminal for debugging.
            print(f"General chat error: {error}")

    # Refresh messages from SQLite on the next Streamlit run.
    st.rerun()
