# AI Interviewer 

The code in this repository is used for the AI interviewer project. 

## Setting up environment

### Python 

To match HBS's computing cluster, we are using Python 3.10.12, and for the virtual environment we're using `pipenv`. To manage several versions of Python, you can use `pyenv` (documentation [here](https://github.com/pyenv/pyenv)). To install the packages from `Pipfile.lock` and stay up to date with the dependencies, run `pipenv sync`. To activate the pipenv shell and run programs in the virtual environment run `pipenv shell`. After that, you can run the code normally. 

## File Structure 

`streamlit-gui`

This folder contains all the code used to create the GUI on Streamlit for the AI interviewer. 