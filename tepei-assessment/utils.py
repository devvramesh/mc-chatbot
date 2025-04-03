def get_latex_code(student_name, r1_topics, r2_topics, r3_topics, all_topics, r1_fig, r2_fig, r3_fig, over_time_fig, concreteness_fig, subjectiveness_fig, specificity_fig): 
    return f"""
\\documentclass[11pt]{{article}}
\\usepackage[usenames]{{xcolor}}

%----------Packages----------
\\usepackage{{enumerate}}
\\usepackage[shortlabels]{{enumitem}}
\\usepackage{{pythontex}}
\\usepackage{{verbatim}} %%includes comment environment
\\usepackage{{fullpage}} %%smaller margins
\\usepackage{{multicol}}
\\usepackage{{multirow}}
\\usepackage{{color}}
\\usepackage{{hyperref}}
\\usepackage{{etoolbox}}
\\AtEndPreamble{{\\usepackage{{pythontex}}}}
\\hypersetup{{
    colorlinks=true,
    linkcolor=blue,
    urlcolor=blue,
    citecolor=blue,
    linktoc=all
}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[english]{{babel}}
\\usepackage{{titlesec}}
\\usepackage{{enumitem}}
\\usepackage{{booktabs}}
\\usepackage{{makecell}}
\\usepackage{{rotating}}
\\usepackage{{float}}
\\usepackage{{graphicx}}
\\usepackage{{amssymb}}
\\usepackage{{bbm}}
\\usepackage[normalem]{{ulem}}
\\useunder{{\\uline}}{{\\ul}}{{}}
\\usepackage[labelfont=bf, labelsep=period]{{caption}} 
\\captionsetup[table]{{skip=10pt}}

% tikz plot
\\usepackage{{tikz}}
\\usepackage{{pgf}}
\\usepackage{{lmodern}}
\\usepackage{{import}}
\\makeatletter\\@ifpackageloaded{{underscore}}{{}}{{\\usepackage[strings]{{underscore}}}}\\makeatother

\\usepackage{{adjustbox}}
\\usepackage{{placeins}}
\\usepackage[authoryear,round]{{natbib}}

\\newcommand{{\\notetable}}[1]{{\\vskip5pt\\begin{{minipage}}{{\\linewidth}}\\footnotesize#1\\end{{minipage}}\\vskip5pt}}
\\newcommand{{\\notefigure}}[1]{{\\vskip5pt\\begin{{minipage}}{{\\linewidth}}\\footnotesize#1\\end{{minipage}}\\vskip5pt}}


\\newcommand{{\\head}}[1]{{
	\\begin{{center}}
		{{\\large #1}}
	\\end{{center}}
	
	\\bigskip 
}}

\\begin{{document}}

\\head{{{student_name} Referee Report Topic Distribution and NLP Analysis}}

In this analysis, we look at the main topics you discussed across the three referee reports you've worked on so far, how your coverage of these topics compares to the class average, how the coverage has evolved across assignments. We also examine a set of NLP-based scores---such as concreteness, subjectivity, and specificity---to evaluate how your writing style and level of detail evolved over time. By combining both the content (which topics you focused on) and the style (how concrete, subjective, or specific your feedback was), we provide a comprehensive view of your development as a reviewer.

\\section{{Topic Distributions Across Referee Reports}}

To identify the topics discussed in your reports, we use LLooM's concept-induction algorithm, which scans your text, produces high-level topics, and assigns each topic a 0-1 relevance score. A score of 0 means the topic is not present at all, while a score of 1 means your writing aligns strongly with that topic. By averaging these scores across the full report and converting them into percentages, we estimate how much space you dedicated to each topic---capturing both the extensive margin (whether you mentioned the topic at all) and the intensive margin (how much emphasis you gave each topic). 

\\subsection{{R1 Assignment}}

In this section, we focus on the core topics identified from everyone's first referee report. By analyzing all R1 submissions, we derived the following set of key themes that frequently appeared across the class: 
{r1_topics}

\\begin{{figure}}[H]
    \\caption{{Student vs. Class R1 Topic Distribution Comparison}}
    \\centering 

    \\includegraphics[width=\\textwidth]{{{r1_fig}}}

    \\notefigure{{This figure shows how your R1 referee report's topic distribution compares to the class average. The bars indicate how much emphasis each topic received in the report.}}
\\end{{figure}}

\\subsection{{R2 Assignment}}

In this section, we focus on the core topics identified from everyone's second referee report. By analyzing all R2 submissions, we derived the following set of key themes that frequently appeared across the class: 
{r2_topics}

\\begin{{figure}}[H]
    \\caption{{Student vs. Class R2 Topic Distribution Comparison}}
    \\centering 

    \\includegraphics[width=\\textwidth]{{{r2_fig}}}

    \\notefigure{{This figure shows how your R2 referee report's topic distribution compares to the class average. The bars indicate how much emphasis each topic received in the report.}}
\\end{{figure}}

\\subsection{{R3 Assignment}}

In this section, we focus on the core topics identified from everyone's third referee report. By analyzing all R3 submissions, we derived the following set of key themes that frequently appeared across the class: 
{r3_topics}

\\begin{{figure}}[H]
    \\caption{{Student vs. Class R3 Topic Distribution Comparison}}
    \\centering 

    \\includegraphics[width=\\textwidth]{{{r3_fig}}}

    \\notefigure{{This figure shows how your R3 referee report's topic distribution compares to the class average. The bars indicate how much emphasis each topic received in the report.}}
\\end{{figure}}

\\subsection{{R1, R2, and R3 Assignments}}

In this final section, we compare your R1, R2, and R3 topic distributions to provide an understanding of your focus across the three reports. Drawn from R1, R2, and R3, we created the following combined set of key themes: 
{all_topics}

\\begin{{figure}}[H]
    \\caption{{Within Student Topic Distribution Comparison Across Reports}}
    \\centering 

    \\includegraphics[width=\\textwidth]{{{over_time_fig}}}

    \\notefigure{{This figure shows how your topic distribution changed in the three assignments. The bars indicate how much emphasis each topic received in the report.}}
\\end{{figure}}

\\section{{Language Use and Writing Style Across Referee Reports}}

Beyond the content, we also evaluated your writing style using three NLP-based tools: 
\\begin{{enumerate}}
    \\item WordTangible, a model that rates each word in your text based on concreteness scores from psycholinguistic studies. Words like ``revenue'' or ``engineer'' are rated as highly concrete, while abstract words like ``efficiency'' or ``approach'' score lower. By averaging these word-level ratings, we estimate how tangible and grounded your writing is, on a 1-5 scale, where 5 is the most concrete.
    \\item TextBlob, a natural language processing library that provides a subjectivity score from 0 to 1, based on a lexicon of adjectives, adverbs, and other subjective expressions. A score of 0 indicates objective, fact-based language, while a score of 1 reflects highly subjective statements. 
    \\item SubjECTiveQA-SPECIFIC, a fine-tuned FinBERT-based model designed to detect specificity in sentences, using probabilistic labels across three levels: not specific, neutrally specific, and highly specific. These are combined into a weighted score from 0 to 1, where higher values indicate more detailed, precise, and actionable feedback.
\\end{{enumerate}}
While none of these tools are perfect and they may occasionally misclassify nuance or tone, they offer a consistent and objective way to reflect how you write---not just what you write about.

\\begin{{figure}}[H]
    \\caption{{R1, R2, and R3 NLP Scores}}
    \\centering 

    \\begin{{minipage}}{{0.3\\textwidth}}
        \\caption*{{Panel A: Concreteness}}
        \\centering
        \\includegraphics[scale=0.4]{{{concreteness_fig}}}
    \\end{{minipage}}
    \\begin{{minipage}}{{0.3\\textwidth}}
        \\caption*{{Panel B: Subjectiveness}}
        \\centering
        \\includegraphics[scale=0.4]{{{subjectiveness_fig}}}
    \\end{{minipage}}
    \\begin{{minipage}}{{0.3\\textwidth}}
        \\caption*{{Panel C: Specificity}}
        \\centering
        \\includegraphics[scale=0.4]{{{specificity_fig}}}
    \\end{{minipage}}

    \\notefigure{{This figure shows how your concreteness (1-5), subjectivity (0-1), and specificity (0-1) evolved in each of your three referee reports. The gray lines represent other students in the class, while the blue line highlights your individual trajectory. A higher concreteness score indicates more tangible, real-world language; a higher subjectivity score means more opinionated or personal statements; and a higher specificity score reflects greater detail and explicitness in your critique.}}
\\end{{figure}}

\\end{{document}}
"""