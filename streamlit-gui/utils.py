import streamlit as st
import hmac
import time
import os
import dropbox 
import io 


# Password screen for dashboard (note: only very basic authentication!)
# Based on https://docs.streamlit.io/knowledge-base/deploy/authentication-without-sso
def check_password():
    """Returns 'True' if the user has entered a correct password."""

    def login_form():
        """Form with widgets to collect user information"""
        with st.form("Credentials"):
            st.text_input("Username", key="username")
            st.text_input("Password", type="password", key="password")
            st.form_submit_button("Log in", on_click=password_entered)

    def password_entered():
        """Checks whether username and password entered by the user are correct."""
        if st.session_state.username in st.secrets.passwords and hmac.compare_digest(
            st.session_state.password,
            st.secrets.passwords[st.session_state.username],
        ):
            st.session_state.password_correct = True

        else:
            st.session_state.password_correct = False

        del st.session_state.password  # don't store password in session state

    # Return True, username if password was already entered correctly before
    if st.session_state.get("password_correct", False):
        return True, st.session_state.username

    # Otherwise show login screen
    login_form()
    if "password_correct" in st.session_state:
        st.error("User or password incorrect")
    return False, st.session_state.username


def check_if_interview_completed(directory, username):
    """Check if interview transcript/time file exists which signals that interview was completed."""

    # Test account has multiple interview attempts
    if username != "testaccount":

        # Check if file exists
        try:
            with open(os.path.join(directory, f"{username}.txt"), "r") as _:
                return True

        except FileNotFoundError:
            return False

    else:

        return False


def save_interview_data(
    username,
    transcripts_directory,
    times_directory,
    dropbox_access_token, 
    file_name_addition_transcript="",
    file_name_addition_time="",
):
    """Write interview data (transcript and time) to disk."""

    dbx = dropbox.Dropbox(dropbox_access_token) 

    # Store chat transcript
    text_content = io.BytesIO() 
    for message in st.session_state.messages: 
        text_content.write(f"{message['role']}: {message['content']}\n".encode("utf-8"))
    text_content.seek(0) 
    dbx.files_upload(text_content.read(), os.path.join(transcripts_directory, f"{username}{file_name_addition_transcript}.txt"), mode=dropbox.files.WriteMode("overwrite")) 

    # Store file with start time and duration of interview
    text_content = io.BytesIO() 
    duration = (time.time() - st.session_state.start_time) / 60
    text_content.write(f"Start time (UTC): {time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(st.session_state.start_time))}\nInterview duration (minutes): {duration:.2f}".encode("utf-8")) 
    text_content.seek(0) 
    dbx.files_upload(text_content.read(), os.path.join(times_directory, f"{username}{file_name_addition_time}.txt"), mode=dropbox.files.WriteMode("overwrite"))