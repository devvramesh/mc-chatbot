import streamlit as st 
import streamlit_authenticator as stauth 
from datetime import datetime, timezone 
import hashlib 
import yaml 
from typing import Dict, Generator 
import time 

from .ai_gateways.gateway import AICompanyGateway 


class StreamlitGUI: 
    def __init__(self, page_title:str, page_icon:str, ai_company:str, ai_model:str, max_tokens:int, system_message:str, auth_required:bool, interviewer_avatar:str, user_avatar:str, closing_messages:Dict[str, str]) -> None: 
        self.page_title = page_title 
        self.page_icon = page_icon 
        self.ai_company = ai_company 
        self.ai_model = ai_model 
        self.max_tokens = max_tokens 
        self.system_message = system_message 
        self.auth_required = auth_required 
        self.interviewer_avatar = interviewer_avatar
        self.user_avatar = user_avatar
        self.closing_messages = closing_messages 

        st.set_page_config(
            page_title=self.page_title, 
            page_icon=self.page_icon
        )

        if self.auth_required: 
            stauth_config = yaml.safe_load(st.secrets['STREAMLIT_AUTHENTICATOR_CONFIG'])
            self.authenticator = stauth.Authenticate(credentials=stauth_config['credentials'], auto_hash=False)

        self.header_container = st.container() 
        self.chat_container = st.container() 


    def setup(self) -> None: 
        """Sets up the page"""
        with self.header_container: 
            st.title(self.page_title) 
        self.setup_session_vars() 
        self.display_login_page() 
        self.display_quit_interview_button() 
        self.display_user_input() 


    def run(self) -> None: 
        """Main function that runs the whole page"""
        self.setup() 
        self.display_message_history() 
        if st.session_state.interview_active: 
            self.send_initial_message() 


    # --------------------------------------------------------------------------
    # frontend 
    # --------------------------------------------------------------------------


    def setup_session_vars(self) -> None: 
        if not self.auth_required: 
            st.session_state.authentication_status = True 
            st.session_state.username = 'testuser'
            st.session_state.show_login_form = False 

        if self.auth_required and 'show_login_form' not in st.session_state:
            # flag for whether to show the login page or not 
            st.session_state.show_login_form = True 

        if "interview_active" not in st.session_state: 
            # flag for whether the interview is active or not 
            st.session_state.interview_active = st.session_state.get('authentication_status', False) 

        if "transcript_history" not in st.session_state: 
            # will store the transcript history of the conversation so far
            st.session_state.transcript_history = [] 
            # will store the messages to display on the screen 
            st.session_state.gui_message_history = [] 

        if 'session_id' not in st.session_state and 'username' in st.session_state: 
            # store the start time of the interview 
            st.session_state.start_time = datetime.now(timezone.utc).timestamp() 

            # create and store the session ID of the interview 
            data = f"{st.session_state.username}+{st.session_state.start_time}"
            st.session_state.session_id = hashlib.sha256(data.encode()).hexdigest() 

        if 'quit_button_hit' not in st.session_state: 
            st.session_state.quit_button_hit = False 


    def display_login_page(self) -> None: 
        if self.auth_required: 
            if st.session_state.show_login_form:
                try: 
                    self.authenticator.login()
                except Exception as e: 
                    st.error(e) 
                
                if st.session_state.get('authentication_status') is False: 
                    st.error("Username/password is incorrect") 
                elif st.session_state.get('authentication_status'):
                    st.session_state.show_login_form = False 
                    st.rerun() 

            if st.session_state.get('authentication_status'): 
                with st.sidebar: 
                    st.write(f"# Welcome {st.session_state.get('name')}")
                    if not st.session_state.quit_button_hit: 
                        st.session_state.interview_active = True 
                    self.authenticator.logout(callback=self.on_logout) 


    def display_quit_interview_button(self) -> None: 
        if st.session_state.interview_active: 
            # Add 'Quit' button to the side bar 
            with st.sidebar: 
                st.markdown("To end the interview and receive a summary of your chat, click quit below")
                st.button("Quit", key='quit', help='End the interview', on_click=self.on_quit_button)


    def display_message_history(self) -> None: 
        if not st.session_state.show_login_form: 
            with self.chat_container: 
                for message in st.session_state.gui_message_history: 
                    if message['role'] == 'assistant': 
                        avatar = self.interviewer_avatar 
                    elif message['role'] == 'user': 
                        avatar = self.user_avatar 
                    with st.chat_message(message['role'], avatar=avatar): 
                        st.markdown(message['content']) 


    def display_user_input(self) -> None: 
        if st.session_state.interview_active: 
            st.chat_input("Your message here", key="user_input", accept_file=True, file_type=['pdf', 'docx'], on_submit=self.on_user_input_submit)


    # --------------------------------------------------------------------------
    # backend 
    # --------------------------------------------------------------------------


    def on_logout(self, *args, **kwargs) -> None: 
        st.session_state.interview_active = False 
        st.session_state.show_login_form = True
        for key in ['transcript_history', 'gui_message_history', 'start_time', 'session_id', 'quit_button_hit']: 
            if key in st.session_state:
                del st.session_state[key]


    def on_user_input_submit(self) -> None: 
        text = st.session_state.user_input.text 
        files = st.session_state.user_input.files 
        with self.chat_container: 
            with st.chat_message('user', avatar=self.user_avatar): 
                st.markdown(text) 
        st.session_state.gui_message_history.append({'role': 'user', 'content': text})
        client = AICompanyGateway.factory(company=self.ai_company, api_key=st.secrets[f"API_KEY_{self.ai_company.upper()}"]) 
        stream = client.stream_message(model=self.ai_model, messages=st.session_state.gui_message_history.copy(), max_tokens=self.max_tokens, system_message=self.system_message)
        self.stream_message(stream) 


    def on_quit_button(self) -> None: 
        st.session_state.interview_active = False 
        st.session_state.gui_message_history.append({'role': 'assistant', 'content': "You have cancelled the interview."}) 
        st.session_state.quit_button_hit = True 


    def send_initial_message(self) -> None: 
        if not st.session_state.gui_message_history: 
            # no messages so far, send initial message 
            client = AICompanyGateway.factory(company=self.ai_company, api_key=st.secrets[f"API_KEY_{self.ai_company.upper()}"]) 
            stream = client.stream_message(model=self.ai_model, messages=[{"role": "user", "content": "Hi!"}], max_tokens=self.max_tokens, system_message=self.system_message)
            self.stream_message(stream) 


    def stream_message(self, stream:Generator) -> None: 
        with self.chat_container: 
            with st.chat_message("assistant", avatar=self.interviewer_avatar): 
                streamlit_msg = st.empty() 
                msg_so_far = "" 
                for chunk in stream: 
                    if chunk: 
                        msg_so_far += chunk 
                    if msg_so_far in self.closing_messages: 
                        streamlit_msg.empty() 
                        break 
                    if len(msg_so_far) > 5: 
                        streamlit_msg.markdown(msg_so_far + "▌")
                if msg_so_far in self.closing_messages: 
                    streamlit_msg.markdown(self.closing_messages[msg_so_far]) 
                    st.session_state.interview_active = False 
                    st.session_state.gui_message_history.append({'role': 'assistant', 'content': self.closing_messages[msg_so_far]})
                else: 
                    streamlit_msg.markdown(msg_so_far)
                    st.session_state.gui_message_history.append({'role': 'assistant', 'content': msg_so_far})