"""
RAG Prompt Templates for Code Q&A

These prompts ensure the LLM generates grounded, citation-backed responses
using only the retrieved code context.
"""

SYSTEM_PROMPT = """You are an expert code analyst helping developers understand codebases.

Your role is to:
- Answer questions about code using ONLY the provided code snippets
- Always cite exact file paths and line numbers
- Be precise and technical
- Never hallucinate or make assumptions about code you haven't seen
- If the answer isn't in the provided context, say so clearly

Format your responses with:
1. Direct answer to the question
2. Specific code references with file paths
3. Explanation of how the code works
"""

CODE_QA_PROMPT_TEMPLATE = """Based on the following code snippets from the repository, answer the user's question.

User Question: {question}

Retrieved Code Context:
{context}

Instructions:
- Answer ONLY based on the code provided above
- Always include file paths and line numbers when referencing code
- If you reference a function or class, mention its exact location
- If the information isn't in the provided context, state that clearly
- Be concise but thorough

Answer:"""

FLOW_ANALYSIS_PROMPT_TEMPLATE = """Analyze the execution flow for the following code segments.

User Question: {question}

Code Segments (in execution order):
{ordered_segments}

Call Graph Information:
{call_graph}

Instructions:
- Describe the execution flow step by step
- Mention each function/method in the flow with its file location
- Explain what each step does
- Include data flow between functions
- Cite exact file paths and line numbers

Execution Flow Analysis:"""

CONTEXT_FORMATTER = """
File: {file_path}
Lines: {start_line}-{end_line}
Function/Class: {identifier}

Code:
```{language}
{code}
```

Dependencies: {dependencies}
Called by: {callers}
Calls: {callees}
---
"""

def format_code_context(code_chunks):
    """Format retrieved code chunks for LLM context"""
    formatted_contexts = []
    
    for chunk in code_chunks:
        context = CONTEXT_FORMATTER.format(
            file_path=chunk.get('file_path', 'unknown'),
            start_line=chunk.get('start_line', 0),
            end_line=chunk.get('end_line', 0),
            identifier=chunk.get('identifier', 'N/A'),
            language=chunk.get('language', 'text'),
            code=chunk.get('code', ''),
            dependencies=', '.join(chunk.get('dependencies', [])) or 'None',
            callers=', '.join(chunk.get('callers', [])) or 'None',
            callees=', '.join(chunk.get('callees', [])) or 'None'
        )
        formatted_contexts.append(context)
    
    return '\n'.join(formatted_contexts)

def create_qa_prompt(question, code_chunks):
    """Create the final prompt for code Q&A"""
    context = format_code_context(code_chunks)
    return CODE_QA_PROMPT_TEMPLATE.format(
        question=question,
        context=context
    )

def create_flow_prompt(question, ordered_segments, call_graph):
    """Create prompt for execution flow analysis"""
    context = format_code_context(ordered_segments)
    
    # Format call graph
    graph_str = '\n'.join([
        f"{caller} -> {callee}" 
        for caller, callee in call_graph
    ])
    
    return FLOW_ANALYSIS_PROMPT_TEMPLATE.format(
        question=question,
        ordered_segments=context,
        call_graph=graph_str
    )
