# Meta prompt 模板用于 CursorFocus 生成 cursorrules 的元提示
META_PROMPT = r"""
You are an AI assistant tasked with generating a JSON-based .cursorrules file
for an AI agent project. This .cursorrules file will guide the behavior and
standards of AI agents in the project. Your task requires careful analysis of
the provided context and adherence to a specific JSON structure.

First, review the following context information:

Project Context Information:
---------------
${project_info_mdx}
-----------------
${codebase_xml}
----------------
${project_metadata}

Now, let's proceed with the analysis and generation of the .cursorrules file.
Follow these steps:

1. Analyze the provided context:
   Wrap your analysis inside <context_analysis> tags.
   Your analysis should include:
   a. Summarize key points from each context variable
   b. Identify programming languages, frameworks, and AI/ML components
   c. List development standards and best practices
   d. Evaluate the meta-prompt and meta-schema, suggesting optimizations

2. Generate the .cursorrules JSON:
   Based on your analysis and optimizations, create .cursorrules JSON object.
   Ensure it follows the structured output schema defined by the Pydantic
   models.

3. Validate the JSON:
   After generating the JSON, perform a final check to ensure:
   - It's valid and complies with the provided structure
   - All required fields are present
   - No additional keys are included beyond those in the structure
   - The "last_updated" field contains the current date and time

<important_details>

Important details:
1. Use only the information provided in the context variables
2. Must produce valid JSON without code fences or extra text
3. Must not contain additional keys beyond those in the schema
4. The "project_analysis" has {basic_info, ai_behavior, communication}
5. The "ai_behavior" includes {code_generation, testing, documentation,
   collaboration}
6. The "last_updated" field should be the current date and time
7. Use the provided context from `codebase.xml`, project_metadata, and user's
   `project_info.mdx` to shape accurate field content
8. This is for a Python-based AI Agent project, possibly with NextJS front-end
9. No extra commentary. Return only final JSON

</important_details>

Now let's incorporate:

- codebase.xml: XML listing of files, classes, frameworks, and key variables
- project_metadata: CursorFocus scan results with frameworks and stats
- project_info.mdx: User-curated project domain, background and standards info

Remember:
- Use only the information provided in the context variables
- Ensure the JSON is valid and complete
- Do not include any fields not specified in the schema
- The "last_updated" field should be the current date and time

Begin your response with your analysis in <context_analysis> tags. Then,
provide the final .cursorrules JSON without any additional commentary.
"""

# Export the META_PROMPT
__all__ = ['META_PROMPT']
