from typing import List, Dict 
import openai 
import json 


def turn_level_annotation(client:openai.OpenAI, model:str, past_messages:List[Dict], response:str) -> Dict[str, int]: 
    context = "" 
    for row in past_messages: 
        context += f"*{row['role']}*: {row['content']}\n"
    prompt = f"""
        ### Instruction: 
        You are the managing editor of a top academic journal in finance. Your role is to ensure that referee reports are insightful, thorough, and accurate. You are seeing a conversation between a referee and an AI-powered simulator acting as the managing editor of a top academic journal. The response you see is from the referee to the AI's comments. Given the context and the goal of the conversation, to generate a high quality referee report, rate the context relevance, specificity, clarity, constructiveness, politeness and overall quality of the **response** on a scale of 1 (worst) to 5 (best) and just output the corresponding ratings. Use the full 1-5 range. Assign 5 only if the response is truly exceptional, meeting or exceeding every part of the criterion without any significant shortcomings. If you are at all uncertain—such as a merely “very good” response—choose a lower score. Keep 5s rare so they truly stand out as extraordinary.

        The definitions of the categories are: 

        1) Relevance:
        - 1 = Completely off-topic or fails to address the previous questions or statements
        - 3 = Partially relevant, includes some unrelated or tangential details
        - 5 = Highly relevant, directly addresses and stays focused on the preceding discussion

        2) Specificity:
        - 1 = Extremely vague, offering only generic or superficial statements
        - 3 = Moderately specific, providing a few concrete details or examples
        - 5 = Very specific, with detailed evidence, references, or concrete examples

        3) Clarity:
        - 1 = Confusing or incoherent, difficult to follow
        - 3 = Somewhat clear, but occasionally ambiguous or disorganized
        - 5 = Extremely clear and well-structured, easy to understand

        4) Constructiveness:
        - 1 = Non-helpful or purely critical without offering solutions or positive suggestions
        - 3 = Somewhat constructive, with a few mild suggestions or partial solutions
        - 5 = Very constructive, providing helpful feedback, clear solutions, or meaningful next steps

        5) Politeness:
        - 1 = Rude, disrespectful, or abrasive language
        - 3 = Neutral or polite enough, with limited courtesy markers
        - 5 = Very polite, respectful, and considerate in tone

        6) Overall Quality:
        - 1 = Poor overall quality
        - 3 = Adequate or acceptable overall
        - 5 = Excellent, thorough, and well-formed response

        ### Context: 
        {context} 

        ### Response: 
        {response} 

        ### Output Format: 
        relevance - x 
        specificity - x 
        clarity - x
        constructiveness - x
        politeness - x 
        overall - x 
    """
    completion = client.chat.completions.create(
        model=model, 
        messages=[{'role': 'user', 'content': prompt}], 
        temperature=0.7, 
        top_p=0.95, 
        response_format={
            'type': 'json_schema', 
            'json_schema': {
                'name': 'annotation_schema', 
                'strict': True, 
                'schema': {
                    'type': 'object', 
                    'properties': {
                        'relevance': {
                            'type': 'integer', 
                            'description': 'Relevance rating on a scale of 1 (worst) to 5 (best)'
                        }, 
                        'specificity': {
                            'type': 'integer', 
                            'description': 'Specificity rating on a scale of 1 (worst) to 5 (best)'
                        }, 
                        'clarity': {
                            'type': 'integer', 
                            'description': 'Clarity rating on a scale of 1 (worst) to 5 (best)'
                        }, 
                        'constructiveness': {
                            'type': 'integer', 
                            'description': 'Constructiveness rating on a scale of 1 (worst) to 5 (best)'
                        }, 
                        'politeness': {
                            'type': 'integer', 
                            'description': 'Politeness rating on a scale of 1 (worst) to 5 (best)'
                        }, 
                        'overall': {
                            'type': 'integer', 
                            'description': 'Overall rating on a scale of 1 (worst) to 5 (best)'
                        }
                    }, 
                    'required': ['relevance', 'specificity', 'clarity', 'constructiveness', 'politeness', 'overall'], 
                    'additionalProperties': False 
                }
            }
        }
    )
    annotation = completion.choices[0].message 
    return json.loads(annotation.content) 



def referee_report_annotation(client:openai.OpenAI, model:str, report:str) -> Dict[str, int]: 
    prompt = f"""
        ### Instruction: 
        You are the managing editor of a top academic journal in finance. Your job is to ensure that referee reports are thorough, useful, and professionally presented. 

        You will receive a *final referee report* produced by a reviewer. Based on the report's content and structure, rate the completeness, specificity, clarity, constructiveness, politeness and overall quality of the **response** on a scale of 1 (worst) to 5 (best) and just output the corresponding ratings. Use the full 1-5 range. Assign 5 only if the response is truly exceptional, meeting or exceeding every part of the criterion without any significant shortcomings. If you are at all uncertain—such as a merely “very good” response—choose a lower score. Keep 5s rare so they truly stand out as extraordinary.

        Use these definitions:

        1) Completeness:
        - 1 = Major aspects of the paper or key elements of the review are missing
        - 3 = Partially covers the main components, but important points are overlooked or briefly addressed
        - 5 = Thoroughly covers all relevant aspects (theory, methods, data, results, etc.) with no significant omissions

        2) Specificity:
        - 1 = Very vague, offers only generic or superficial statements
        - 3 = Moderately specific, includes some concrete details or examples
        - 5 = Highly detailed, with clear evidence, references, or examples

        3) Clarity:
        - 1 = Confusing or incoherent, difficult to follow
        - 3 = Somewhat clear, with occasional ambiguity or disorganization
        - 5 = Extremely clear, well-structured, and easy to understand

        4) Constructiveness:
        - 1 = Purely critical or unhelpful, offers no actionable suggestions
        - 3 = Offers some suggestions or partial solutions
        - 5 = Very constructive, providing helpful feedback, clear recommendations, or meaningful next steps

        5) Politeness:
        - 1 = Rude, disrespectful, or abrasive
        - 3 = Neutral or polite enough, though not especially courteous
        - 5 = Very polite, respectful, and considerate in tone

        6) Overall:
        - 1 = Poor overall quality
        - 3 = Adequate or acceptable overall
        - 5 = Excellent, thorough, and well-formed review 

        ### Report: 
        {report} 

        ### Output Format: 
        completeness - x 
        specificity - x 
        clarity - x
        constructiveness - x
        politeness - x 
        overall - x 
    """
    completion = client.chat.completions.create(
        model=model, 
        messages=[{'role': 'user', 'content': prompt}], 
        temperature=0.7, 
        top_p=0.95, 
        response_format={
            'type': 'json_schema', 
            'json_schema': {
                'name': 'annotation_schema', 
                'strict': True, 
                'schema': {
                    'type': 'object', 
                    'properties': {
                        'completeness': {
                            'type': 'integer', 
                            'description': 'Completeness rating on a scale of 1 (worst) to 5 (best)'
                        }, 
                        'specificity': {
                            'type': 'integer', 
                            'description': 'Specificity rating on a scale of 1 (worst) to 5 (best)'
                        }, 
                        'clarity': {
                            'type': 'integer', 
                            'description': 'Clarity rating on a scale of 1 (worst) to 5 (best)'
                        }, 
                        'constructiveness': {
                            'type': 'integer', 
                            'description': 'Constructiveness rating on a scale of 1 (worst) to 5 (best)'
                        }, 
                        'politeness': {
                            'type': 'integer', 
                            'description': 'Politeness rating on a scale of 1 (worst) to 5 (best)'
                        }, 
                        'overall': {
                            'type': 'integer', 
                            'description': 'Overall rating on a scale of 1 (worst) to 5 (best)'
                        }
                    }, 
                    'required': ['completeness', 'specificity', 'clarity', 'constructiveness', 'politeness', 'overall'], 
                    'additionalProperties': False 
                }
            }
        }
    )
    annotation = completion.choices[0].message 
    return json.loads(annotation.content) 