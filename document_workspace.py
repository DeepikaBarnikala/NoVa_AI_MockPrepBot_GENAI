
import json
import re
import streamlit as st
import pandas as pd

from document_generator import generate_document


FORMAT_OPTIONS = {
    "PDF document": "pdf",
    "Word document": "docx",
    "PowerPoint presentation": "pptx",
    "Excel workbook": "xlsx",
}


def extract_json(text):
    """Extract JSON returned by Gemini."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("Gemini did not return valid JSON.")

    return json.loads(text[start:end + 1])


def generate_plan_content(
    client,
    generate_with_retry,
    model_name,
    request,
):
    """Ask Gemini for structured content suitable for documents."""

    prompt = f"""
You are NOVA, an expert study planner and document creator.

Create a detailed, practical preparation resource for this request:

{request}

Return ONLY valid JSON with this structure:

{{
  "title": "Document title",
  "sections": [
    {{
      "heading": "Section heading",
      "content": "Detailed explanation. Use newline characters for separate points."
    }}
  ],
  "table": {{
    "headers": ["Day", "Tasks", "Expected outcome"],
    "rows": [
      ["Day 1", "Specific tasks", "Measurable outcome"]
    ]
  }},
  "chart": {{
    "title": "Progress or study plan chart",
    "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
    "values": [25, 50, 75, 100],
    "ylabel": "Cumulative target (%)"
  }}
}}

Rules:
- Adapt the structure to the user's actual request.
- For a 30-day plan, include all 30 days in the schedule table.
- Organize work into achievable daily tasks.
- Include revision, practice, mock interviews, and job applications when relevant.
- Use a chart only when meaningful. Chart values must be numeric.
- Do not claim that illustrative progress targets guarantee employment.
- Make content specific, useful, and beginner-friendly.
- Do not invent external links or claim unverified facts.
- Keep the JSON valid. Do not wrap it in Markdown fences.
"""

    response = generate_with_retry(
        client,
        prompt,
        temperature=0.3,
        max_tokens=7000,
    )

    return extract_json(response.text)


def render_document_workspace(
    client,
    generate_with_retry,
    model_name,
):
    st.title("📄 NOVA Document Studio")
    st.write(
        "Create preparation plans, study notes, reports, "
        "charts, PDFs, presentations, and workbooks."
    )

    with st.form("nova_document_form"):
        request = st.text_area(
            "What should NOVA prepare?",
            placeholder=(
                "Example: Create a 30-day job preparation plan "
                "for a beginner Python developer."
            ),
            height=120,
        )

        selected_format = st.selectbox(
            "Choose the downloadable format",
            list(FORMAT_OPTIONS.keys()),
        )

        include_chart = st.checkbox(
            "Include a chart when relevant",
            value=True,
        )

        submitted = st.form_submit_button(
            "✨ Generate Preparation Material"
        )

    if submitted:
        if not request.strip():
            st.warning("Please describe what you want NOVA to prepare.")
            return

        try:
            with st.spinner("NOVA is preparing your content..."):
                content = generate_plan_content(
                    client,
                    generate_with_retry,
                    model_name,
                    request.strip(),
                )

                if not include_chart:
                    content.pop("chart", None)

                st.session_state["nova_generated_content"] = content
                st.session_state["nova_generated_format"] = (
                    FORMAT_OPTIONS[selected_format]
                )
                st.session_state["nova_generated_request"] = request.strip()

        except Exception as exc:
            st.error(f"Could not generate the preparation material: {exc}")
            return

    content = st.session_state.get("nova_generated_content")

    if not content:
        st.info("Enter a request above to create your first document.")
        return

    st.divider()
    st.subheader(content.get("title", "Your preparation material"))

    for section in content.get("sections", []):
        st.markdown(f"### {section.get('heading', '')}")
        st.markdown(section.get("content", ""))

    table_data = content.get("table", {})
    if table_data.get("headers"):
        st.subheader("Schedule / Practice Table")
        st.dataframe(
          pd.DataFrame(
              table_data.get("rows", []),
              columns=table_data["headers"],
          ),
          use_container_width=True,
      )

    chart_data = content.get("chart")
    if chart_data and chart_data.get("labels") and chart_data.get("values"):
        st.subheader(chart_data.get("title", "Progress Chart"))
        try:
            st.bar_chart(
                {
                    "Target": dict(
                        zip(chart_data["labels"], chart_data["values"])
                    )
                }
            )
        except Exception:
            st.caption("The chart could not be displayed.")

    st.divider()
    st.subheader("Download your preparation material")

    current_format = st.session_state.get(
        "nova_generated_format", "pdf"
    )

    try:
        if st.button("🔄 Create / Refresh Downloadable File"):
            with st.spinner("Creating your file..."):
                path = generate_document(content, current_format)
                st.session_state["nova_last_generated_path"] = str(path)

        saved_path = st.session_state.get("nova_last_generated_path")

        if saved_path:
            from pathlib import Path

            path = Path(saved_path)

            if path.is_file():
                mime_types = {
                    "pdf": "application/pdf",
                    "docx": (
                        "application/vnd.openxmlformats-officedocument."
                        "wordprocessingml.document"
                    ),
                    "pptx": (
                        "application/vnd.openxmlformats-officedocument."
                        "presentationml.presentation"
                    ),
                    "xlsx": (
                        "application/vnd.openxmlformats-officedocument."
                        "spreadsheetml.sheet"
                    ),
                }

                with open(path, "rb") as file:
                    st.download_button(
                        label=f"⬇️ Download {path.name}",
                        data=file.read(),
                        file_name=path.name,
                        mime=mime_types.get(
                            path.suffix.lstrip("."),
                            "application/octet-stream",
                        ),
                    )

    except Exception as exc:
        st.error(f"File creation failed: {exc}")
