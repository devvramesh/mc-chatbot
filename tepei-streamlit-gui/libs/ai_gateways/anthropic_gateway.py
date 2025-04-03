import anthropic 
from typing import List, Dict, Generator 

from .gateway import AICompanyGateway

class AnthropicGateway (AICompanyGateway): 
    name = 'anthropic' 

    def setup_client(self, api_key:str) -> None: 
        """Sets up the client to the AI company SDK 

        Args:
            api_key (str): the api key 
        """
        self.__client = anthropic.Anthropic(api_key=api_key) 


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
        msg = self.__client.messages.create(
            model=model, 
            messages=messages, 
            max_tokens=max_tokens, 
            system=system_message, 
            **kwargs
        ) 
        return msg.content[0].text 


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
        with self.__client.messages.stream(
            model=model, 
            messages=messages, 
            max_tokens=max_tokens, 
            system=system_message, 
            **kwargs
        ) as stream: 
            for text_delta in stream.text_stream: 
                yield text_delta 