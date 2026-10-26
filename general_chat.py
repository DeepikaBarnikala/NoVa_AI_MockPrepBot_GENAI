
import streamlit as st
import chat_history as history


GENERAL_CHAT_PROMPT = """
You are NOVA, a friendly and helpful AI assistant.

Your purpose in this mode is to have a natural conversation with the user.

IMPORTANT RULES:
1. Answer the user's actual question directly.
2. Do not behave like an interviewer unless the user explicitly asks
   to practise an interview.
3. Do not automatically evaluate answers or give interview scores.
4. Explain technical concepts in simple, beginner-friendly English.
5. When asked for code, provide working code and explain it.
6. When asked for a dry run, trace the code step by step with example
   input and output.
7. Help with Python, Java, SQL, Flask, React, DSA, AI, projects,
   debugging, study plans, and general questions.
8. If the user asks a follow-up question, use the previous conversation
   to understand the context.
9. If information is missing, ask a relevant clarification question.
10. Never invent code execution results. Clearly explain assumptions.

Respond naturally, like a helpful tutor and conversation partner.
"""


def render_general_chat(client, generate_with_retry, model_name):
    st.header("💬 General Chat with NOVA")
    st.caption(
        "Ask anything. Learn concepts, write code, practise dry runs, "
        "debug errors, or have a normal conversation."
    )

    # Find only general-chat conversations in the existing database.
    all_chats = history.list_conversations()
    general_chats = [
        chat for chat in all_chats
        if chat["chat_type"] == "general"
    ]

    # Start a separate general conversation.
    if st.button("➕ New General Chat", key="new_general_chat"):
        chat_id = history.create_conversation(
            title="New General Chat",
            chat_type="general",
            metadata={"mode": "general_chat"}
        )
        st.session_state["active_general_chat_id"] = chat_id
        st.rerun()

    # Select an existing general conversation.
    if general_chats:
        chat_options = {
            f'{chat["title"]} (Chat #{chat["id"]})': chat["id"]
            for chat in general_chats
        }
        labels = list(chat_options.keys())

        current_id = st.session_state.get("active_general_chat_id")
        matching_label = next(
            (
                label for label, chat_id in chat_options.items()
                if chat_id == current_id
            ),
            labels[0]
        )

        selected_label = st.selectbox(
            "Saved general conversations",
            labels,
            index=labels.index(matching_label),
            key="general_chat_selector"
        )

        selected_id = chat_options[selected_label]
        st.session_state["active_general_chat_id"] = selected_id

    active_id = st.session_state.get("active_general_chat_id")

    if not active_id:
        st.info("Click **New General Chat** to start a conversation.")
        return

    conversation = history.get_conversation(active_id)

    if not conversation or conversation["chat_type"] != "general":
        st.warning("Please start a new general chat.")
        return

    messages = history.get_messages(active_id)

    # Display previous messages.
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept normal questions, not mock-interview answers.
    user_prompt = st.chat_input(
        "Ask NOVA anything...",
        key="general_chat_input"
    )

    if user_prompt:
        # Save the user's message first.
        history.add_message(active_id, "user", user_prompt)

        with st.chat_message("user"):
            st.markdown(user_prompt)

        # Use recent messages as conversation context.
        recent_messages = messages[-10:]

        conversation_context = "\n".join(
            f'{msg["role"].upper()}: {msg["content"]}'
            for msg in recent_messages
        )

        prompt = f"""
{GENERAL_CHAT_PROMPT}

PREVIOUS CONVERSATION:
{conversation_context if conversation_context else "This is the beginning of the conversation."}

LATEST USER MESSAGE:
{user_prompt}

Respond to the latest user message directly. Do not turn it into an
interview question unless the user specifically requests interview practice.
"""

        with st.chat_message("assistant"):
            with st.spinner("NOVA is thinking..."):
                try:
                    answer = generate_with_retry(
                        client=client,
                        prompt=prompt,
                        temperature=0.5,
                        max_tokens=1800
                    )

                    if not answer or not str(answer).strip():
                        answer = (
                            "I couldn't generate a response this time. "
                            "Please try asking again."
                        )

                    st.markdown(answer)

                    # Save the response to the same conversation.
                    history.add_message(
                        active_id,
                        "assistant",
                        str(answer)
                    )

                    # Give the first conversation a useful title.
                    if not messages:
                        title = " ".join(user_prompt.split())[:45]
                        history.update_conversation(
                            active_id,
                            title=title or "General Chat"
                        )

                except Exception as error:
                    st.error(
                        "NOVA couldn't respond right now. "
                        "Please try again."
                    )
                    # Keep technical details in the terminal, not the UI.
                    print(f"General chat error: {error}")
