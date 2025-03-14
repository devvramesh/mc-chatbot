from libs.streamlit_gui import StreamlitGUI
import config 

if __name__ == "__main__": 
    app = StreamlitGUI(
        page_title=config.PAGE_TITLE, 
        page_icon=config.PAGE_ICON, 
        ai_company=config.AI_COMPANY,
        ai_model=config.MODEL, 
        max_tokens=config.MAX_OUTPUT_TOKENS, 
        system_message=config.SYSTEM_PROMPT, 
        generate_summary_prompt=config.GENERATE_SUMMARY_PROMPT, 
        auth_required=config.LOGINS, 
        interviewer_avatar=config.AVATAR_INTERVIEWER,
        user_avatar=config.AVATAR_RESPONDENT, 
        closing_messages=config.CLOSING_MESSAGES, 
        dropbox_path=config.DROPBOX_PATH, 
        interview_instructions=config.INTERVIEW_INSTRUCTIONS 
    )
    app.run() 