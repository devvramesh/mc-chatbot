import openai 
from typing import List, Dict, Generator 

from .gateway import AICompanyGateway

class OpenAIGateway (AICompanyGateway): 
    name = 'openai' 

    def setup_client(self, api_key:str) -> None: 
        """Sets up the client to the AI company SDK 

        Args:
            api_key (str): the api key 
        """
        self.__client = openai.OpenAI(api_key=api_key) 


    def create_message(self, model:str, messages:List[Dict], max_tokens:int, system_message:str=None, **kwargs) -> str: 
        """Returns a message from the API. Overriden by subclass 

        Args:
            model (str): the name of the model 
            messages (List[Dict]): a list of messages of the conversation so far 
            max_tokens (int): the max number of tokens that can be generated in the chat completion 
            system_message (str): a system message, if any. The system message can also be included in the messages param. Defaults to None.

        Returns:
            str: the messsage sent by the API 
        """
        def _check_for_system_message(messages:List[Dict]) -> bool: 
            """Checks to see if there is a system message already in the conversation 

            Args:
                messages (List[Dict]): messages in the conversation so far 

            Returns:
                bool: True if a system message exists already. False otherwise 
            """
            for msg in messages: 
                if msg['role'] == 'system': 
                    return True 
            return False 
        if system_message and not _check_for_system_message(messages): 
            # add system message without overriding existing system message 
            messages.insert(0, {"role": "system", "content": system_message})
        msg = self.__client.chat.completions.create(
            model=model, 
            messages=messages, 
            max_completion_tokens=max_tokens, 
            **kwargs 
        ) 
        return msg.choices[0].message.content 


    def stream_message(self, model:str, messages:List[Dict], max_tokens:int, system_message:str=None, **kwargs) -> Generator[str, None, None]: 
        """Streams a message from the API. Overriden by subclass 

        Args:
            model (str): the name of the model 
            messages (List[Dict]): a list of messages of the conversation so far 
            max_tokens (int): the max number of tokens that can be generated in the chat completion 
            system_message (str): a system message, if any. The system message can also be included in the messages param. Defaults to None.

        Yields:
            Generator[str, None, None]: yields the messages sent by the AI 
        """
        def _check_for_system_message(messages:List[Dict]) -> bool: 
            """Checks to see if there is a system message already in the conversation 

            Args:
                messages (List[Dict]): messages in the conversation so far 

            Returns:
                bool: True if a system message exists already. False otherwise 
            """
            for msg in messages: 
                if msg['role'] == 'system': 
                    return True 
            return False 
        if system_message and not _check_for_system_message(messages): 
            # add system message without overriding existing system message 
            messages.insert(0, {"role": "system", "content": system_message})
        with self.__client.chat.completions.create(
            model=model, 
            messages=messages, 
            max_completion_tokens=max_tokens, 
            stream=True, 
            **kwargs 
        ) as stream: 
            for chunk in stream: 
                yield chunk.choices[0].delta.content 