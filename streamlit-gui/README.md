# Streamlit GUI for AI Interviewer 

The code in this folder is used to create the GUI on Streamlit for the AI interviewer. To run the app and see the GUI, you need to first activate the virtual environment by running `pipenv shell` on the command line. Then you can run `streamlit run streamlit-gui/app.py` to get the Streamli GUI started. It should automatically open on your browser. 

## Code structure 

`app.py` 

This file is where the streamlit app gets run from. It inherits the GUI code from the our `libs`. 

`config.py` 

This file contains all the configuration information for the app, such as the prompts, model name, and other parameters. 

`libs/streamlit_gui.py` 

This file contains all the code that creates the streamlit GUI. 

`libs/ai_gateways`

The files in this folder contain gateways to the AI company Python SDKs. The goal of the gateway is to use standardized sets of input and outputs and modify them for the respective SDK so that the end user doesn't need to worry about different SDK structures and formats. 

`resources`

The files in this folder are used as resources for the GUI. 