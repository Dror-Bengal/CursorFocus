# dev-README: CoderAgentFocus .cursorrules Generation Feature

## 背景与目标

在 CoderAgentFocus (Fork from CursorFocus) 项目的最新开发中，引入了一个自动生成 **.cursorrules** 文件的新功能，以为“AI-Coder Agent”自动创建一份在项目中可充当“system_prompt”的配置与规则。
该功能旨在结合项目的实际技术栈、文件结构、元数据等信息，生成满足以下要求的 `.cursorrules` JSON：

1. 基于 **Pydantic** 模型（`CursorRules`）实现严格的 JSON 结构验证
2. 能准确体现目标项目的技术栈、语言、依赖框架、AI 行为规范、开发标准等
3. 动态地使用项目代码扫描结果（如 `codebase.xml`、`project_metadata`、`project_info.mdx` 等），自动合成符合项目真实情况的“AI system_prompt”

此功能主要由以下文件完成：
- **`cursorrules_generation.py`**
- **`metat-prompts/meta_models.py`**
- **`metat-prompts/meta_prompt.py`**

## 关键文件与架构

### 1. `cursorrules_generation.py`

这是本功能的核心逻辑文件，主要包含以下部分：

1. **`generate_cursorrules_json(...)` 函数**
   - 核心入口，用于收集项目上下文信息并调用 AI 生成最终 `.cursorrules` 文件（JSON字符串格式）。
   - 可选择传入：
     - `project_info`：如项目名称、版本、语言等基础信息
     - `codebase_xml_path`：`codebase.xml` 文件路径
     - `project_metadata`：通过项目扫描（**scan_for_projects** 等功能）或其他信息源得到的项目元数据
     - `project_info_mdx_path`：用户自定义维护的 `project_info.mdx` 说明文件
     - `api_key`：OpenRouter/OpenAI 的 API key（支持在 `.env` 文件中配置）
     - `project_root_path`：提供项目根路径，可以自动扫描项目，提取相应信息

2. **上下文信息收集**
   - 通过 `gather_context_from_codebase_xml`、`gather_context_from_project_metadata`、`gather_context_from_project_info_mdx` 等函数，读取并截取必要的文件内容和元数据，组合为一份长文本上下文。
   - 在 `combine_all_contexts` 函数中将这些上下文进行合并，包含：
     - codebase.xml 内容
     - project_metadata（JSON 或 Python dict）
     - project_info.mdx

3. **构建并发送 Prompt**
   - 使用 `build_system_prompt(...)` 将 `META_PROMPT`（来自 `metat-prompts/meta_prompt.py`）和收集到的上下文信息合并生成最终的 `system_prompt`。
   - 创建一个 `Agent`（来自 `pydantic_ai`），使用指定的 `model = OpenAIModel(...)`，并通过 `agent.run_sync(...)` 发送对话请求，得到生成的 JSON 字符串。

4. **验证 JSON**
   - `CursorRules.parse_raw(...)` 检查 AI 返回的 JSON 是否满足在 `metat-prompts/meta_models.py` 中定义的 `CursorRules` 结构。若解析出错，则抛出错误提醒无效输出。
   - 最终返回 `.cursorrules` 字符串给调用者或写入文件。

5. **辅助函数**
   - `validate_cursorrules_json(...)`：用于对外暴露的验证，判断 `.cursorrules` JSON 字符串是否能被 `CursorRules` 模型正确解析。
   - `gather_codebase_analysis`：利用 `content_generator.generate_focus_content` 对项目进行扫描，并抽取基础统计信息（如文件总数、行数、警告等），可用于项目元数据合并。

#### 使用示例

```python
from cursorrules_generation import generate_cursorrules_json

project_info = {
    "name": "MyAIProject",
    "version": "0.1.0",
    "language": "python",
    # ... 其他项目信息
}

generated_json = generate_cursorrules_json(
    project_info=project_info,
    codebase_xml_path="/absolute/path/to/codebase.xml",
    project_metadata={"some": "metadata"},
    project_info_mdx_path="/absolute/path/to/project_info.mdx",
    api_key="YOUR_API_KEY",  # 或在 .env 里提供
    project_root_path="/path/to/project"  # 可选，用于自动扫描
)

print("Generated .cursorrules JSON:")
print(generated_json)

2. metat-prompts/meta_models.py
	•	定义了 .cursorrules JSON 的具体 Pydantic 模型，包括 CursorRules、ProjectAnalysis、AIBehavior、DevelopmentStandards、BasicInfo 等多层嵌套模型。
	•	CursorRules 是最顶层的模型，描述了在最终 JSON 中所需的字段：
	•	name、version、last_updated
	•	project_analysis：包含 basic_info、ai_behavior、development_standards 等
	•	project_info：一个通用 dict，可容纳项目特定的自定义信息

	注意：每次 .cursorrules 更新时，last_updated 字段需设置为当前时间。AI 会自动从 Prompt 中获取要求并注入该信息。

3. metat-prompts/meta_prompt.py
	•	存放一个多行字符串常量 META_PROMPT。
	•	它包含对 AI 提示的基本结构和步骤：
	1.	解析项目上下文
	2.	生成 .cursorrules JSON
	3.	验证 JSON 格式
	•	这里也声明了一些“重要细节”的规范，如：
	•	只能使用上下文中提供的信息
	•	JSON 需严格符合 CursorRules 结构
	•	“project_analysis” 字段中的子字段结构固定等

当在 cursorrules_generation.py 中 build_system_prompt 函数调用 META_PROMPT 时，会将收集到的上下文（codebase.xml、project_metadata、project_info.mdx）一并插入 Prompt 中，让 AI 能够更好地理解项目背景并生成针对性更强的 .cursorrules。

注意事项
	1.	OpenRouter / Anthropics API Key
	•	需在 .env 文件或环境变量里提供 OPENROUTER_API_KEY。
	•	或者在调用 generate_cursorrules_json 时显式传递 api_key 参数。
	2.	上下文截断
	•	如果 codebase.xml 内容过长（超过 30,000 字符），cursorrules_generation.py 会进行截断，以防发送给 LLM 过多上下文导致 Token 超限。
	3.	模型选择
	•	默认选用 "anthropic/claude-3.5-sonnet" 并通过 base_url="https://openrouter.ai/api/v1"，可在代码中自行修改为其他模型或 API 地址。
	4.	自动扫描元数据
	•	若用户不提供 project_metadata，可通过 scan_for_projects 自动检测项目类型并提取部分信息。
	5.	与现有 rules_generator.py 的差异
	•	rules_generator.py 是此前的静态 .cursorrules 生成器，基于预定义模板 + project_info。
	•	cursorrules_generation.py 是面向 AI Copilot / AI-Coder 的动态生成方式，在 meta_prompt 驱动下产生更细粒度、更灵活的规则 JSON。

后续工作
	•	测试覆盖：完善单元测试，包含对“AI 无法正确输出 JSON”或“上下文缺失”场景的测试。
	•	与 CI/CD 集成：在持续集成流程中自动生成/更新 .cursorrules，并在 PR 中进行验证。
	•	扩展多模型支持：若在 PydanticAI 中配置其他模型（如 OpenAI GPT-4），可直接替换以生成 .cursorrules。

如对以上功能有疑问或改进建议，欢迎在本 CoderAgentFocus Fork 项目讨论区或原项目 CursorFocus 讨论区或提交 issue 进行反馈。
