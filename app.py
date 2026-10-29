
import os
from datetime import date, time

import streamlit as st
from dotenv import load_dotenv
from google import genai

from database import (
    initialize_database,
    save_appointment,
    get_appointment,
)


load_dotenv()

st.set_page_config(
    page_title="CareFlow AI",
    page_icon="🩺",
    layout="centered",
)

# Initialize the database and create the table if necessary.
initialize_database()


SYSTEM_PROMPT = """
You are CareFlow AI, a health education assistant.

Your responsibilities:
1. Answer general healthcare service and clinic-related FAQs.
2. Help users understand appointment booking procedures.
3. Draft polite, professional administrative messages when requested.
4. Use only the clinic information and policies provided
   by the application when answering clinic-specific questions.

Instructions:
- Understand the user's intent before answering.
- Give clear, concise, and relevant responses.
- Use bullet points for multiple steps when appropriate.
- If required information is missing, ask a clarifying question.
- Never invent clinic policies, appointment availability,
  prices, or medical information.
- Do not diagnose medical conditions or prescribe treatment.
- For medical emergencies, advise the user to contact
  local emergency services immediately.
- If you cannot answer reliably, say so and suggest
  contacting an appropriate healthcare professional.

Privacy:
- Do not request unnecessary sensitive personal information.
- Do not repeat sensitive information unless necessary
  to answer the user's request.

Response style:
- Be empathetic, professional, and easy to understand.
- Clearly distinguish general information from
  confirmed clinic-specific information.
"""


st.title("🩺 CareFlow AI")
st.subheader("Your AI-powered health education assistant")

st.write(
    "Ask general health education questions or submit "
    "an appointment request."
)

st.warning(
    "Educational prototype only. This tool does not diagnose "
    "conditions, prescribe medication, or replace a qualified "
    "healthcare professional. Do not enter personal medical details. "
    "Appointment requests are not confirmed bookings."
)


# --------------------------------------------------
# APPOINTMENT REQUEST FORM
# --------------------------------------------------

st.divider()
st.header("📅 Request an Appointment")

st.write(
    "Complete the form to save an appointment request. "
    "The request will remain pending until confirmed by the clinic."
)

with st.form("appointment_form", clear_on_submit=False):
    full_name = st.text_input(
        "Full name",
        max_chars=100,
        placeholder="Enter your name",
    )

    contact = st.text_input(
        "Contact information",
        max_chars=150,
        placeholder="Email address or phone number",
    )

    appointment_date = st.date_input(
        "Preferred appointment date",
        value=date.today(),
        min_value=date.today(),
    )

    appointment_time = st.time_input(
        "Preferred appointment time",
        value=time(10, 0),
        step=900,
    )

    note = st.text_area(
        "Optional administrative note",
        max_chars=300,
        placeholder=(
            "For example: I prefer a morning appointment. "
            "Do not enter medical details."
        ),
    )

    submitted = st.form_submit_button(
        "Submit Appointment Request",
        type="primary",
        use_container_width=True,
    )

if submitted:
    if not full_name.strip():
        st.error("Please enter your full name.")

    elif not contact.strip():
        st.error("Please enter your contact information.")

    elif appointment_date < date.today():
        st.error("Please select today or a future date.")

    else:
        try:
            appointment_id = save_appointment(
                full_name=full_name,
                contact=contact,
                appointment_date=appointment_date.isoformat(),
                appointment_time=appointment_time.strftime("%H:%M"),
                note=note,
            )

            saved_appointment = get_appointment(appointment_id)

            if saved_appointment:
                st.session_state["last_appointment_id"] = (
                    appointment_id
                )
                st.success(
                    "Appointment request saved successfully!"
                )
                st.info(
                    f"Request ID: {appointment_id}\n\n"
                    "Status: Pending\n\n"
                    "This is a request, not a confirmed booking."
                )
            else:
                st.error(
                    "The request could not be verified. "
                    "Please try again."
                )

        except Exception:
            st.error(
                "Unable to save the appointment request. "
                "Please check the database configuration."
            )


# Show details of the most recently saved request.
last_appointment_id = st.session_state.get(
    "last_appointment_id"
)

if last_appointment_id is not None:
    with st.expander("View my latest saved request"):
        try:
            appointment = get_appointment(last_appointment_id)

            if appointment:
                st.write(
                    f"**Request ID:** {appointment['id']}"
                )
                st.write(
                    f"**Name:** {appointment['full_name']}"
                )
                st.write(
                    f"**Preferred date:** "
                    f"{appointment['appointment_date']}"
                )
                st.write(
                    f"**Preferred time:** "
                    f"{appointment['appointment_time']}"
                )
                st.write(
                    f"**Status:** {appointment['status']}"
                )
                st.caption(
                    "Your contact information is not displayed here."
                )
            else:
                st.warning("The saved request was not found.")

        except Exception:
            st.error("Unable to retrieve the saved request.")


# --------------------------------------------------
# GEMINI HEALTH EDUCATION ASSISTANT
# --------------------------------------------------

st.divider()
st.header("💬 Ask CareFlow AI")

examples = [
    "What is blood pressure?",
    "Why is sleep important?",
    "What is the difference between viruses and bacteria?",
]

st.markdown("### Try an example question")

selected_question = st.selectbox(
    "Choose a question",
    ["Select an example..."] + examples,
)

question = st.text_area(
    "Your health education question",
    placeholder="For example: Why is hydration important?",
    max_chars=1000,
)

if st.button("Generate answer", type="primary"):
    final_question = (
        question.strip()
        if question.strip()
        else (
            selected_question
            if selected_question != "Select an example..."
            else ""
        )
    )

    if not final_question:
        st.error("Please enter a question or choose an example.")

    elif not os.getenv("GEMINI_API_KEY"):
        st.error(
            "API key not configured. Check your local .env file."
        )

    else:
        try:
            with st.spinner(
                "Generating an educational response..."
            ):
                client = genai.Client(
                    api_key=os.getenv("GEMINI_API_KEY")
                )

                response = client.models.generate_content(
                    model=os.getenv(
                        "GEMINI_MODEL",
                        "gemini-2.5-flash",
                    ),
                    contents=(
                        SYSTEM_PROMPT
                        + "\n\nUser question:\n"
                        + final_question
                    ),
                )

                answer = response.text

                if answer:
                    st.markdown("### AI-generated response")
                    st.markdown(answer)
                    st.caption(
                        "AI-generated information may be incomplete "
                        "or incorrect. Verify important health "
                        "information with a qualified professional."
                    )
                else:
                    st.error(
                        "No response was returned. Please try again."
                    )

        except Exception:
            st.error(
                "The AI request failed. Check your internet "
                "connection, API key, model availability, and "
                "API quota, then try again."
            )


st.divider()
st.caption(
    "CareFlow AI | Healthcare education prototype | "
    "Python, Streamlit, SQLite and Google Gemini"
)
