import streamlit as st 
import streamlit_authenticator as stauth 
from datetime import datetime
import pytz 
import hashlib 
import yaml 
from typing import Dict, Generator, Tuple, List 
import dropbox 
import dropbox.files 
import pandas as pd 
import pypandoc 
import io 
import csv 
from pathlib import Path 
import threading 
import logging 
import time 
import tempfile 
import base64 

from .ai_gateways.gateway import AICompanyGateway 
from .logger import setup_logger 


class StreamlitGUI: 
    def __init__(self, page_title:str, page_icon:str, ai_company:str, ai_model:str, max_tokens:int, system_message:str, generate_summary_prompt:str, auth_required:bool, interviewer_avatar:str, user_avatar:str, first_interviewer_message:str, closing_messages:Dict[str, str], dropbox_path:str, interview_instructions:str) -> None: 
        """Set up the object

        Args:
            page_title (str): the title for the page 
            page_icon (str): the icon to use for the page 
            ai_company (str): the name of the AI company to use 
            ai_model (str): the name of the AI model to use 
            max_tokens (int): the max number of output tokens for the model 
            system_message (str): the system prompt for the bot 
            generate_summary_prompt (str): the summary prompt for the bot 
            auth_required (bool): True if logins are enabled and authentication is required, False otherwise 
            interviewer_avatar (str): the string for the interviewer avatar
            user_avatar (str): the string for the user avatar 
            closing_messages (Dict[str, str]): a dict that maps closing code to closing message 
            dropbox_path (str): the path to the dropbox data folder to store the transcripts 
            interview_instructions (str): the instructions to display for the bot 
        """
        # set the global vars
        self.page_title = page_title 
        self.page_icon = page_icon 
        self.ai_company = ai_company 
        self.ai_model = ai_model 
        self.max_tokens = max_tokens 
        self.system_message = system_message 
        self.generate_summary_prompt = generate_summary_prompt
        self.auth_required = auth_required 
        self.interviewer_avatar = interviewer_avatar
        self.user_avatar = user_avatar
        self.first_interviewer_message = first_interviewer_message
        self.closing_messages = closing_messages 
        self.dropbox_path = dropbox_path 
        self.interview_instructions = interview_instructions

        # set up the page 
        st.set_page_config(
            page_title=self.page_title, 
            page_icon=self.page_icon
        )

        if self.auth_required: 
            # set up the authentication 
            stauth_config = yaml.safe_load(st.secrets['STREAMLIT_AUTHENTICATOR_CONFIG'])
            self.authenticator = stauth.Authenticate(credentials=stauth_config['credentials'], auto_hash=False)

        # create some containers for the header (where the title will live) and for the chat (where chat history will live) 
        self.header_container = st.container() 
        self.error_container = st.container() 
        self.instructions_container = st.container() 
        self.paper_upload_container = st.container() 
        self.uploaded_paper_container = st.container() 
        self.chat_container = st.container() 


    def setup(self) -> None: 
        """Sets up the components of the page"""
        # set the title of the page 
        with self.header_container: 
            st.markdown("## " + self.page_title) 
            # add some html code that hides the file uploader list from streamlit 
            css = """
                <style>
                    div[data-testid="stFileUploaderFile"] {
                        display: none;
                    }
                    div.st-emotion-cache-fis6aj.e17y52ym5 {
                        display: none;
                    }
                </style>
            """
            st.markdown(css, unsafe_allow_html=True)
        self.setup_session_vars() 
        self.display_login_page() 
        self.display_instructions_expander() 
        self.display_paper_uploader() 
        self.display_uploaded_paper() 
        self.display_load_past_session() 
        self.display_restart_interview_button()
        self.display_generate_summary_button() 
        self.display_user_input() 


    def run(self) -> None: 
        """Main function that runs the whole page"""
        self.setup() 
        self.display_message_history() 
        if st.session_state.reached_error: 
            self.display_error_message() 
        else: 
            if st.session_state.interview_status and not st.session_state.first_instructions_shown: 
                self.display_instructions()
            if st.session_state.interview_status: 
                self.stream_initial_message() 
            if st.session_state.interview_status and not st.session_state.first_instructions_shown: 
                time.sleep(1) 
                # change flag so that the dialog doesn't show up anymore 
                st.session_state.first_instructions_shown = True 


    # --------------------------------------------------------------------------
    # frontend 
    # --------------------------------------------------------------------------


    def setup_session_vars(self) -> None: 
        """Sets up the session vars

        Initializes any session variables that haven't been initialized yet 
        """
        if not self.auth_required: 
            # since we're not doing logins set these session vars to defaults
            st.session_state.authentication_status = True 
            st.session_state.username = 'testuser'
            st.session_state.show_login_form = False 

        if self.auth_required and 'show_login_form' not in st.session_state:
            # flag for whether to show the login page or not 
            st.session_state.show_login_form = True 

        if "interview_status" not in st.session_state: 
            # flag for whether the interview is active or not 
            st.session_state.interview_status = st.session_state.get('authentication_status', False) 

        if "transcript_history" not in st.session_state: 
            # will store the transcript history of the conversation so far
            st.session_state.transcript_history = [] 

        if 'session_id' not in st.session_state and 'username' in st.session_state: 
            # store the start time of the interview 
            st.session_state.start_time = datetime.now(pytz.timezone('UTC')).timestamp() 

            # create and store the session ID of the interview 
            data = f"{st.session_state.username}+{st.session_state.start_time}"
            st.session_state.session_id = hashlib.sha256(data.encode()).hexdigest() 

        if 'first_instructions_shown' not in st.session_state: 
            # flag for whether the instructions have been shown for the first time or not 
            st.session_state.first_instructions_shown = False 

        if 'show_confirm_restart' not in st.session_state: 
            # flag for whether to show a confirm restart message
            st.session_state.show_confirm_restart = False 
            st.session_state.show_confirm_restart_time = 0 
        else: 
            if st.session_state.show_confirm_restart: 
                if time.time() - st.session_state.show_confirm_restart_time > 20: 
                    # if it's been more than a minute since the confirm has been shown, turn it back to original 
                    st.session_state.show_confirm_restart = False 

        if 'found_closing_msg' not in st.session_state: 
            # flag for whether the AI outputted a closing message 
            st.session_state.found_closing_msg = False 

        if 'uploaded_paper_content' not in st.session_state: 
            # object to store the uploaded paper 
            st.session_state.uploaded_paper_content = None 
            st.session_state.uploaded_paper_name = None 

        if 'reached_error' not in st.session_state: 
            # flag for whether we reached an error or not 
            st.session_state.reached_error = False 

        if 'log' not in st.session_state: 
            # objects for logging 
            log_stream, log = setup_logger('ai-referee-interviewer-streamlit-gui')
            st.session_state.log = log 
            st.session_state.log_stream = log_stream 


    def display_login_page(self) -> None: 
        """Display the login page and the log out button after authentication success"""
        if self.auth_required: 
            # only do this if we're using logins 
            if st.session_state.show_login_form:
                # if the session state says show the form, then show it 
                with st.empty(): 
                    try: 
                        # show the login form 
                        self.authenticator.login()
                    except Exception as e: 
                        st.error(e) 

                with st.empty(): 
                    if st.session_state.get('authentication_status') is False: 
                        # password is wrong
                        st.error("Username/password is incorrect") 
                    elif st.session_state.get('authentication_status'):
                        # password is right so change the flag and rerun the script
                        st.session_state.show_login_form = False 
                        st.rerun() 

            if st.session_state.get('authentication_status'): 
                # when authentication is confirmed, show the logout button
                with st.sidebar: 
                    # welcome the user 
                    st.write(f"# Welcome {st.session_state.get('name')}")
                    st.session_state.interview_status = True 
                    # add logout button that runs self.on_logout when hit 
                    self.authenticator.logout(callback=self.on_logout) 


    def display_instructions_expander(self) -> None: 
        """Shows the instructions expander"""
        if not st.session_state.show_login_form: 
            with self.instructions_container: 
                with st.expander("See instructions"): 
                    st.markdown(self.interview_instructions)


    @st.dialog(f"AI Referee Intervier Guide", width='large')
    def display_instructions(self) -> None: 
        """Displays instructions in a pop up dialog"""
        st.markdown(self.interview_instructions)


    def display_paper_uploader(self) -> None: 
        """Displays the paper upload section"""
        if not st.session_state.show_login_form and st.session_state.interview_status and not st.session_state.reached_error: 
            with self.paper_upload_container: 
                # add option to upload one pdf here 
                st.markdown("##### Upload the paper here")
                st.file_uploader(
                    label="Upload the paper here", 
                    type="pdf", 
                    on_change=self.on_paper_upload,
                    key='file_uploader',
                    accept_multiple_files=False, 
                    help="Upload a pdf of the paper here. This tool only accepts PDFs and only accepts one file at a time. Uploading a new file will replace the previously uploaded file.", 
                    label_visibility='collapsed'
                )


    def display_uploaded_paper(self) -> None: 
        if not st.session_state.show_login_form and st.session_state.interview_status and not st.session_state.reached_error and st.session_state.uploaded_paper_name: 
            with self.uploaded_paper_container: 
                st.markdown(f"Uploaded paper: {st.session_state.uploaded_paper_name}")


    def display_restart_interview_button(self) -> None: 
        """Displays the restart interview"""
        if not st.session_state.show_login_form: 
            # add 'Restart' button to the side bar
            with st.sidebar: 
                if st.session_state.show_confirm_restart: 
                    # show confirmation message 
                    st.markdown("**Are you sure you want to restart?**\nYou will be starting the conversation from scratch")
                    # add the button and runs self.on_restart_button when hit 
                    st.button(
                        label="**Confirm**", 
                        help='Confirm restarting the interview', 
                        on_click=self.on_restart_button, 
                        type='primary'
                    )
                else: 
                    st.markdown("To restart the interview from scratch, click restart below")
                    # add the button and runs self.on_restart_button when hit 
                    st.button(
                        label="Restart", 
                        help='Restart the interview', 
                        on_click=self.on_restart_button
                    )


    def display_generate_summary_button(self) -> None: 
        """Displays the generate summary button"""
        if not st.session_state.show_login_form and st.session_state.interview_status and not st.session_state.reached_error: 
            # button is always displayed unless we are in the login page to allow people to generate the document at any time 
            with st.sidebar: 
                st.markdown("To generate a summary document of the interview, click generate below") 
                # add the button and runs self.on_generate_summary_button when hit 
                st.button(
                    label="Generate", 
                    help='Generate summary of the interview', 
                    on_click=self.on_generate_summary_button
                )


    def display_load_past_session(self) -> None: 
        """Displays a button that can load a past session"""
        if not st.session_state.show_login_form: 
            with st.sidebar: 
                st.markdown("To load a past session, click below")
                st.button(
                    label="Load a Past Session", 
                    help="Check for past sessions and load them", 
                    on_click=self.on_load_past_session_button
                )


    def display_message_history(self) -> None: 
        """Displays the full message history so far"""
        if not st.session_state.show_login_form: 
            # always show the message history unless we are showing the login page 
            with self.chat_container: 
                for message in st.session_state.transcript_history: 
                    # first set the avatar 
                    if message['role'] == 'assistant': 
                        avatar = self.interviewer_avatar 
                    elif message['role'] == 'user': 
                        avatar = self.user_avatar 

                    # now display the message 
                    with st.chat_message(message['role'], avatar=avatar): 
                        st.markdown(message['content']) 


    def display_user_input(self) -> None: 
        """Display the user input """
        if st.session_state.interview_status and not st.session_state.reached_error and not st.session_state.found_closing_msg: 
            # only display the user input section if the interview is active 
            # display the input section and runs self.on_user_input_submit when text submitted 
            st.chat_input(
                placeholder="Your message here", 
                key="user_input", 
                on_submit=self.on_user_input_submit
            )


    def display_error_message(self) -> None: 
        """Displays an error message"""
        def try_again(): 
            """Call back function for trying again"""
            self.log("warning", "Trying again after error", st.session_state.to_dict())
            # reset reached error 
            st.session_state.reached_error = False 
            # return back to interview status 
            st.session_state.interview_status = True 

        with self.error_container: 
            st.error("An error occurred. Please try again or contact Andrew Wu at anwu@hbs.edu.")
            st.button("Try again", on_click=try_again)

        # set the interview state to False as it's over 
        st.session_state.interview_status = False 


    # --------------------------------------------------------------------------
    # backend 
    # --------------------------------------------------------------------------


    def on_logout(self, *args, **kwargs) -> None: 
        """Function that runs when log out button is hit"""
        self.log("warning", "Logging out", st.session_state.to_dict())

        # stop the interview 
        st.session_state.interview_status = False 
        # show the login form 
        st.session_state.show_login_form = True
        # reset instructions flag 
        st.session_state.first_instructions_shown = False 
        # reset reached error 
        st.session_state.reached_error = False 

        # remove any other session variable to start over 
        for key in ['transcript_history', 'start_time', 'session_id', 'log', 'log_stream', 'show_confirm_restart', 'found_closing_msg', 'uploaded_paper_name', 'uploaded_paper_content']: 
            if key in st.session_state:
                del st.session_state[key]


    def on_user_input_submit(self) -> None: 
        """Function that runs when user input is submitted"""
        try: 
            # get the user inputs 
            text = st.session_state.user_input 

            self.log("warning", f"User input: {text}", st.session_state.to_dict())

            # display the user input 
            with self.chat_container: 
                message = st.chat_message('user', avatar=self.user_avatar) 
                message.markdown(text)

            # save the user input  
            self.save_msg_to_session('user', text)

            # save to the transcript so far to dropbox 
            thread = threading.Thread(target=self.save_transcript_to_dropbox, args=(st.session_state.to_dict(),)) 
            thread.start() 

            # get the response from the AI bot and stream the message 
            client = AICompanyGateway.factory(company=self.ai_company, api_key=st.secrets[f"API_KEY_{self.ai_company.upper()}"]) 
            stream = client.stream_message(model=self.ai_model, messages=self.get_messages_for_ai(), max_tokens=self.max_tokens, system_message=self.system_message)
            self.stream_message(stream) 
        except Exception as e: 
            st.session_state.transcript_history = st.session_state.transcript_history[:-1] 
            st.session_state.reached_error = True 
            self.log("error", f"Error processing user input: {e}", st.session_state.to_dict())


    def on_paper_upload(self) -> None: 
        """Function that runs when a paper is uploaded

        The function will read the paper as base64, and then save it to dropbox
        """
        try: 
            uploaded_paper = st.session_state.file_uploader
            if uploaded_paper: 
                self.log("warning", f"Uploaded paper {uploaded_paper.name}", st.session_state.to_dict())
                # save the base64 so that we can use it in the API 
                st.session_state.uploaded_paper_content = base64.b64encode(uploaded_paper.getvalue()).decode('utf-8') 
                st.session_state.uploaded_paper_name = uploaded_paper.name

                # also save the document to dropbox so that we can know what was uploaded 
                doc_bytes = io.BytesIO(uploaded_paper.read())
                thread = threading.Thread(target=self.save_file_upload_to_dropbox, args=(st.session_state.to_dict(), uploaded_paper.name, doc_bytes)) 
                thread.start() 
        except Exception as e: 
            st.session_state.reached_error = True 
            self.log('error', f"Error processing file upload: {e}", st.session_state.to_dict())


    @st.dialog("Load Past Session", width='large')
    def on_load_past_session_button(self) -> None: 
        self.log("warning", "Checking for past sessions", st.session_state.to_dict()) 
        with st.spinner('Checking for past sessions', show_time=True): 
            past_transcripts_map = self.get_past_sessions(st.session_state.session_id)
        if len(past_transcripts_map) > 0: 
            # there are past transcripts so show to the user 
            session_chosen = st.selectbox(
                'Select a session', 
                past_transcripts_map, 
                index=None, 
                placeholder='Select a past session...', 
                label_visibility='collapsed'
            )

            if session_chosen: 
                # if a session has been chosen, show a preview of the conversation 

                # build the conversation preview 
                session_conversation = "" 
                for row in past_transcripts_map[session_chosen]['transcript']: 
                    session_conversation += f"**{row['role'].capitalize()}:** {row['content']}\n\n"

                # limit the preview so that the page doesn't get too big
                if len(session_conversation) >= 1500: 
                    session_conversation = session_conversation[:1500].strip() + '...'

                # show the preview 
                st.markdown(f"**Session conversation:**\n\n{session_conversation}")

                # add note about uploaded paper 
                if past_transcripts_map[session_chosen]['uploaded_paper'] is not None: 
                    st.markdown(f"Uploaded paper: {past_transcripts_map[session_chosen]['uploaded_paper']['name']}")

                # add confirmation button to move forward with the chosen session 
                confirm_button = st.button(
                    label='Choose session', 
                    help='Click to load the currently selected session', 
                    type='primary', 
                    use_container_width=False
                )
                if confirm_button: 
                    # when confirmed, load the session 
                    st.session_state.transcript_history = past_transcripts_map[session_chosen]['transcript'] 
                    st.session_state.session_id = past_transcripts_map[session_chosen]['transcript'][0]['session_id'] 
                    if past_transcripts_map[session_chosen]['uploaded_paper'] is not None: 
                        st.session_state.uploaded_paper_content = past_transcripts_map[session_chosen]['uploaded_paper']['content']
                        st.session_state.uploaded_paper_name = past_transcripts_map[session_chosen]['uploaded_paper']['name']
                    else: 
                        st.session_state.uploaded_paper_content = None 
                    st.rerun() 
        else: 
            st.markdown("No past sessions found")


    @st.dialog("Interview Summary Document")
    def on_generate_summary_button(self) -> None: 
        """Function that runs when the generate summary button is hit 

        Creates a pop up dialog that shows a loading spinner and then displays a download button 
        """
        self.log("warning", "Generating summary document", st.session_state.to_dict())
        # start the loading spinner and show the time elapsed so far 
        with st.spinner("Generating document", show_time=True):
            try: 
                message = st.empty() 
                message.markdown("This process may take a few minutes. Please be patient and **do not press \"x\" or close this window**.")
                # ask the AI to generate a summary 
                client = AICompanyGateway.factory(company=self.ai_company, api_key=st.secrets[f"API_KEY_{self.ai_company.upper()}"]) 
                generate_message = [{'role': 'user', 'content': self.generate_summary_prompt}]
                summary = client.create_message(
                    model=self.ai_model, 
                    messages=self.get_messages_for_ai() + generate_message, 
                    max_tokens=self.max_tokens, 
                    system_message=self.system_message 
                )

                # check if there are any closing messages in there 
                _, summary = self.check_closing_messages(summary) 
            except Exception as e: 
                st.session_state.reached_error = True 
                self.log("error", f"Error asking AI to generate summary: {e}", st.session_state.to_dict())
                return 

            try: 
                # add the title to the top 
                summary = f"# Interview Summary\n\nGenerated on {datetime.now(pytz.timezone('UTC')).strftime('%Y-%m-%d %H:%M:%S UTC')} by {st.session_state.name}\n\n" + summary 

                # convert the markdown into word doc 
                with tempfile.NamedTemporaryFile(suffix=".docx", delete=True) as tmp_file: 
                    temp_path = tmp_file.name 

                    pypandoc.convert_text(
                        source=summary,
                        to="docx",
                        format="md",
                        outputfile=temp_path 
                    )

                    # read in the bytes 
                    with open(temp_path, "rb") as f: 
                        doc_content = f.read() 

                    doc_bytes = io.BytesIO(doc_content) 

            except Exception as e: 
                st.session_state.reached_error = True 
                self.log("error", f"Error creating docx document: {e}", st.session_state.to_dict())
                return 

        # save the document to dropbox 
        thread = threading.Thread(target=self.save_summary_to_dropbox, args=(st.session_state.to_dict(), doc_bytes)) 
        thread.start() 

        # display download button 
        message.markdown("To download the summary document, click download below")
        st.download_button(
            label='Download document', 
            help='Download interview summary document', 
            data=doc_bytes,
            file_name=f"{st.session_state.username}_interview_summary.docx", 
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
            on_click="ignore", 
            icon=":material/download:"
        )


    def on_restart_button(self) -> None: 
        """Function that runs when the restart button is hit"""
        if st.session_state.show_confirm_restart: 
            # if the user clicked confirm then restart
            self.log("warning", "Restarting interview", st.session_state.to_dict())
            # reset some session state variables 
            for key in ['transcript_history', 'start_time', 'session_id', 'log', 'log_stream', 'show_confirm_restart', 'found_closing_msg', 'uploaded_paper_content', 'uploaded_paper_name']: 
                if key in st.session_state:
                    del st.session_state[key]
            # restart the interview 
            st.session_state.interview_status = True 
            # reset reached error 
            st.session_state.reached_error = False 
            # reset to original restart button
            st.session_state.show_confirm_restart = False 
        else: 
            # ask for confirmation 
            st.session_state.show_confirm_restart = True 
            st.session_state.show_confirm_restart_time = time.time() 


    def stream_initial_message(self) -> None: 
        """Streams the initial message from the AI"""
        if not st.session_state.transcript_history: 
            # no messages so far, stream initial message 
            self.log("warning", "Streaming initial message", st.session_state.to_dict())
            with self.chat_container: 
                with st.chat_message('assistant', avatar=self.interviewer_avatar): 
                    # stream the message 
                    streamlit_msg = st.empty() 
                    for i in range(0, len(self.first_interviewer_message), len(self.first_interviewer_message) // 10): 
                        streamlit_msg.markdown(self.first_interviewer_message[:i] + "▌")
                        time.sleep(0.03)
                    streamlit_msg.markdown(self.first_interviewer_message)
            self.save_msg_to_session('assistant', self.first_interviewer_message)


    def stream_message(self, stream:Generator) -> None: 
        """Helper function to stream AI messages 

        Args:
            stream (Generator): the generator that contains the messages being streamed 
        """ 
        self.log("warning", "Streaming message", st.session_state.to_dict())
        streaming_first_msg = not st.session_state.transcript_history 
        try: 
            with self.chat_container: 
                # stream messages within the chat container
                with st.chat_message("assistant", avatar=self.interviewer_avatar): 
                    # stream messages as the assistant 
                    streamlit_msg = st.empty() # streamlit object for where the message will go 
                    msg_so_far = "" # record the message received so far
                    for chunk in stream: 
                        # iterate through the stream and add the results 
                        if chunk: 
                            msg_so_far += chunk 
                        found_closing_msg, closing_msg = self.check_closing_messages(msg_so_far) 
                        if found_closing_msg: 
                            streamlit_msg.empty() 
                            break 
                        if len(msg_so_far) > 10: 
                            streamlit_msg.markdown(msg_so_far + "▌")

                    # after all the text has streamed
                    if found_closing_msg: 
                        # we found a closing message, so display closing message and shut down the conversation 
                        final_msg = closing_msg
                        st.session_state.interview_status = False 
                        st.session_state.found_closing_msg = True 
                    else: 
                        # did not find closing message, display the message sent 
                        final_msg = msg_so_far 

                    # display the message received 
                    streamlit_msg.markdown(final_msg)

                    self.log("warning", f"Got final message {final_msg}", st.session_state.to_dict())

                    # save the message to the session 
                    self.save_msg_to_session('assistant', final_msg)

                    # save the transcript to dropbox 
                    if not streaming_first_msg: 
                        thread = threading.Thread(target=self.save_transcript_to_dropbox, args=(st.session_state.to_dict(),)) 
                        thread.start() 
        except Exception as e: 
            st.session_state.reached_error = True 
            self.log("error", f"Error streaming message from AI: {e}", st.session_state.to_dict())


    # --------------------------------------------------------------------------
    # utils 
    # --------------------------------------------------------------------------


    def log(self, level:str, message:str, session_state:Dict) -> None: 
        """Logs messages to dropbox 

        Args:
            level (str): the level to log at 
            message (str): the message to log 
            session_state (Dict): the current session state 
        """
        show_traceback = level.upper() == "ERROR"
        session_state["log_stream"].seek(0, 2) 

        level = getattr(logging, level.upper())
        session_state['log'].log(level, message, exc_info=show_traceback) 

        session_state['log_stream'].seek(0) 
        thread = threading.Thread(target=self.save_log_to_dropbox, args=(session_state, session_state['log_stream'])) 
        thread.start() 
        session_state['log_stream'].seek(0, 2) 


    def save_log_to_dropbox(self, session_state:Dict, log_stream:io.BytesIO) -> None: 
        """Saves logs to dropbox 

        Args:
            session_state (Dict): the current session state
            log_stream (io.BytesIO): the log stream with all the log messages 
        """
        save_fpath = Path(self.dropbox_path)/session_state['username']/f"log+{session_state['username']}+{session_state['session_id']}.log"

        content = log_stream.getvalue().encode("utf-8") 

        self.save_to_dropbox(io.BytesIO(content), str(save_fpath))


    def save_transcript_to_dropbox(self, session_state:Dict) -> None: 
        """Saves the transcript to dropbox 

        Usually runs in a separate thread to not interrupt the main chatbot experience 

        Args:
            session_state (Dict): the current session state dict to reference inside the thread 
        """
        # creates the path to save to 
        save_fpath = Path(self.dropbox_path)/session_state['username']/f"transcript+{session_state['username']}+{session_state['session_id']}.csv"

        self.log("warning", f"Saving transcript to dropbox to {save_fpath}", session_state)

        # save the transcript history 
        df = pd.DataFrame(session_state['transcript_history'])
        csv_content = io.BytesIO() 
        df.to_csv(csv_content, index=False, encoding='utf-8')
        csv_content.seek(0)
        self.save_to_dropbox(csv_content, str(save_fpath))


    def save_summary_to_dropbox(self, session_state:Dict, doc_content:io.BytesIO) -> None: 
        """Saves the summary docx to dropbox 

        Usually runs in a separate thread to not interrupt the main chatbot experience 

        Args:
            session_state (Dict): the current session state dict to reference inside the thread 
            doc_content (io.BytesIO): the docx data to save 
        """
        # create the path to save to 
        save_fpath = Path(self.dropbox_path)/session_state['username']/f"summary_document+{session_state['username']}+{session_state['session_id']}+{int(datetime.now(pytz.timezone('UTC')).timestamp())}.docx"

        self.log("warning", f"Saving summary to dropbox to {save_fpath}", session_state)

        # save the content to dropbox 
        self.save_to_dropbox(doc_content, str(save_fpath))


    def save_file_upload_to_dropbox(self, session_state:Dict, file_name:str, doc_content:io.BytesIO) -> None: 
        """Saves the uploaded PDF to dropbox 

        Usually runs in a separate thread to not interrupt the main chatbot experience 

        Args:
            session_state (Dict): the current session state dict to reference inside the thread 
            file_name (str): the name of the file
            doc_content (io.BytesIO): the docx data to save 
        """
        # create the path to save to 
        save_fpath = Path(self.dropbox_path)/session_state['username']/f"uploaded_paper+{session_state['username']}+{session_state['session_id']}+{int(datetime.now(pytz.timezone('UTC')).timestamp())}+{file_name}"

        self.log("warning", f"Saving uploaded PDF to dropbox to {save_fpath}", session_state)

        # save the content to dropbox 
        self.save_to_dropbox(doc_content, str(save_fpath))


    def save_to_dropbox(self, content:io.BytesIO, save_fpath:str) -> None: 
        """Saves some content to dropbox 

        Usually runs in a separate thread to not interrupt the main chatbot experience 

        Args:
            content (io.BytesIO): the content to save
            save_fpath (str): the path to save to 
        """
        tries = 3
        for x in range(1, tries+1): 
            try: 
                # create the dropbox client 
                dbx = dropbox.Dropbox(oauth2_refresh_token=st.secrets['REFRESH_TOKEN_DROPBOX'], app_key=st.secrets['APP_KEY_DROPBOX'], app_secret=st.secrets['APP_SECRET_DROPBOX']) 

                # upload the file to dropbox and overwrite the existing file 
                dbx.files_upload(
                    content.read(), 
                    save_fpath, 
                    mode=dropbox.files.WriteMode("overwrite")
                ) 
                break 
            except: 
                time.sleep(2 ** x)


    def save_msg_to_session(self, role:str, content:str) -> None: 
        """Saves messages in the conversation to our session state variables 

        Args:
            role (str): the role of the message sender
            content (str): the message sent 
        """
        st.session_state.transcript_history.append({
            'time': datetime.now(pytz.timezone('UTC')).isoformat(timespec='milliseconds'), 
            'session_id': st.session_state.session_id, 
            'user': st.session_state.username, 
            'role': role, 
            'content': content 
        })


    def get_messages_for_ai(self) -> List[Dict[str, str]]: 
        """Gets the messages for the AI from the transcript history 

        Returns:
            List[Dict[str, str]]: a list of dicts with the messages for the AI
        """
        messages = [] 
        if st.session_state.uploaded_paper_content: 
            if self.ai_company == 'anthropic': 
                messages.append({
                    'role': 'user', 
                    'content': [
                        {
                            'type': 'document', 
                            'source': {
                                'type': 'base64', 
                                'media_type': 'application/pdf', 
                                'data': st.session_state.uploaded_paper_content
                            }, 
                            'cache_control': {'type': 'ephemeral'}
                        }, 
                        {
                            'type': 'text', 
                            'text': 'The paper that I am reviewing is attached to give you additional context as you help me with my referee report. You do not need to acknowledge receipt of this document.'
                        }
                    ]
                })
        for row in st.session_state.transcript_history: 
            messages.append({
                'role': row['role'], 
                'content': row['content']
            })
        if self.ai_company == 'anthropic' and messages[-1]['role'] == 'user': 
            content = messages[-1]['content'] 
            messages[-1] = {
                'role': 'user', 
                'content': [
                    {
                        'type': 'text', 
                        'text': content, 
                        'cache_control': {'type': 'ephemeral'}
                    }
                ]
            }
        return messages 


    def check_closing_messages(self, msg:str) -> Tuple[bool, str]: 
        """Check if a message contains any of the closing messages 

        Args:
            msg (str): the message to check 

        Returns:
            Tuple[bool, str]: a tuple that returns a bool of whether a closing message was found and a string of the final message 
        """
        for c, m in self.closing_messages.items(): 
            if c.lower() in msg.lower() or m.lower() in msg.lower(): 
                return True, m 
        return False, msg 
    

    @st.cache_resource(show_spinner=False)
    def get_past_sessions(_self, current_session_id:str) -> Dict: 
        """Function that searches for past sessions in dropbox 

        Args:
            current_session_id (str): the current session ID so that we don't include it 

        Returns:
            Dict: a dictionary that maps session name to a dictionary {'transcript': [contains transcript], 'uploaded_paper': {'name': [name of file], 'content': [pdf content]}}
        """
        # connect to dropbox 
        dbx = dropbox.Dropbox(oauth2_refresh_token=st.secrets['REFRESH_TOKEN_DROPBOX'], app_key=st.secrets['APP_KEY_DROPBOX'], app_secret=st.secrets['APP_SECRET_DROPBOX']) 

        # search for transcript files 
        transcripts_fpath = Path(_self.dropbox_path)/st.session_state['username']
        past_transcripts = dbx.files_search_v2(
            query="transcript*.csv", 
            options=dropbox.files.SearchOptions(
                path=str(transcripts_fpath), 
                order_by=dropbox.files.SearchOrderBy.last_modified_time
            )
        )

        past_transcripts_map = {}
        session_count = 1
        for transcript in list(past_transcripts.matches)[::-1]: 
            # get the transcript 
            fname = transcript.metadata.get_metadata().name 
            past_transcript_session_id = fname.replace('.csv', '').split('+')[-1] 
            if past_transcript_session_id == current_session_id: 
                # skip current session 
                continue 
            _, response = dbx.files_download(str(transcripts_fpath/fname))
            content = response.content.decode('utf-8') 

            # read the transcript and save it 
            csv_reader = csv.DictReader(io.StringIO(content))
            transcript_data = [row for row in csv_reader] 
            first_time = datetime.fromisoformat(transcript_data[0]['time']).astimezone(pytz.timezone('US/Eastern')).strftime('%Y-%m-%d %H:%M:%S EST')
            past_transcripts_map[f"Session {session_count} from {first_time}"] = {'transcript': transcript_data} 

            # find uploaded paper 
            past_uploaded_paper = dbx.files_search_v2(
                query=f"uploaded_paper+{st.session_state['username']}+{past_transcript_session_id}+*.pdf", 
                options=dropbox.files.SearchOptions(
                    path=str(transcripts_fpath), 
                    order_by=dropbox.files.SearchOrderBy.last_modified_time
                )
            )
            if past_uploaded_paper.matches: 
                # if there was an uploaded paper, get the last uploaded file 
                last_uploaded_paper = max(
                    [x.metadata.get_metadata().name for x in past_uploaded_paper.matches], 
                    key=lambda x: int(x.replace('.pdf', '').split('+')[-2]) # max by the timestamp 
                ) 
                # read the content of the paper 
                _, response = dbx.files_download(str(transcripts_fpath/last_uploaded_paper))
                content = base64.b64encode(response.content).decode('utf-8')
                # save it 
                past_transcripts_map[f"Session {session_count} from {first_time}"]['uploaded_paper'] = {
                    'name': last_uploaded_paper.split('+')[-1], 
                    'content': content 
                }
            else: 
                # no uploaded paper so set to None 
                past_transcripts_map[f"Session {session_count} from {first_time}"]['uploaded_paper'] = None 
            session_count += 1
        return past_transcripts_map 
