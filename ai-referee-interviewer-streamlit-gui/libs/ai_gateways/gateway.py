import inspect 
import importlib 
import types 
from typing import Generator, List, Dict 

class AICompanyGateway: 
    """Class for standardized gateways to AI company APIs"""

    # the name of the AI company
    name = None 

    def __init__(self, api_key:str) -> None: 
        """Sets up the object 

        Args:
            api_key (str): api key to the AI company's API 
        """
        self.setup_client(api_key)


    @classmethod
    def factory(cls, company:str=None, **opts) -> 'AICompanyGateway': 
        """Factory method to create a subclass of AICompanyGateway

        Args:
            company (str, optional): the name of the company to create. Defaults to None.

        Raises:
            Exception: raises an exception if an unknown company is passed

        Returns:
            AICompanyGateway: Returns an instance of the <company>_Gateway class 
        """
        def _find_class(module:types.ModuleType, company:str) -> type: 
            """Finds a class within a module 

            Args:
                module (types.ModuleType): the module to search in 
                company (str): the name of the company to look for 

            Raises:
                Exception: raises an exception if an unknown company is passed

            Returns:
                type: The class object for the company gateway 
            """
            class_name = company.lower() + 'gateway' 
            for m in inspect.getmembers(module, inspect.isclass): 
                if m[0].lower() == class_name: 
                    return m[1] 
            raise Exception(f"Cannot find class for AI company {company} in {module.__name__}")

        # search for the module in this folder with the company name 
        module = importlib.import_module("libs.ai_gateways." + company + "_gateway") 
        # find the gateway class for the company 
        AICompanyGatewayClass = _find_class(module, company) 
        return AICompanyGatewayClass(**opts) 


    def setup_client(self, api_key:str) -> None: 
        """Sets up the client to the AI company SDK 

        Args:
            api_key (str): the api key 
        """
        self.__client = None 


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
        pass 


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
        pass  