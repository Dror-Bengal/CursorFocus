import os
import json
import argparse
import logging
import traceback
from typing import Dict, Any, Optional
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel # 使用 OpenAI 兼容模式
from dotenv import load_dotenv

# 导入项目代码库扫描功能
from project_detector import scan_for_projects
from rules_analyzer import RulesAnalyzer
from config import load_config
from content_generator import generate_focus_content

# 导入 meta prompt 和 models
from meta_prompts.meta_prompt import META_PROMPT
from meta_prompts.meta_models import CursorRules


# 设置日志记录
def setup_logging(log_file: str = "cursorrules_generation.log"):
    """设置日志记录器"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


# 全局日志记录器
logger = setup_logging()


def load_openrouter_api_key() -> str:
    """从环境变量中获取 OpenRouter API key。"""
    load_dotenv()
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY not found in environment variables. "
            "Please add it to .env file in the root directory."
        )
    return api_key


def get_agent() -> Agent[None, CursorRules]:
    """创建并配置 PydanticAI Agent，使用 OpenRouter。

    Returns:
        Agent[None, CursorRules]: 配置好的 Agent，输出 CursorRules 对象
    """
    api_key = load_openrouter_api_key()

    # 配置 LLM Model 使用 OpenRouter OpenAI 兼容模式
    model = OpenAIModel(
        model_name="anthropic/claude-3.5-sonnet",
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key
    )

    # 创建一个 PydanticAI Agent
    agent = Agent[None, CursorRules](
        model=model,
        result_type=CursorRules,
        system_prompt=META_PROMPT
    )

    return agent


def gather_context_from_codebase_xml(
    codebase_xml_path: str
) -> str:
    """
    从 codebase.xml 文件中解析上下文信息。
    如果文件不存在或读取失败，则返回相应提示。
    """
    if not os.path.exists(codebase_xml_path):
        return "No codebase.xml found."

    try:
        with open(codebase_xml_path, "r", encoding="utf-8") as f:
            xml_content = f.read()
        # 超过30000字符则截断
        if len(xml_content) > 30000:
            return xml_content[:30000] + "...(truncated codebase.xml)"
        return xml_content
    except Exception as e:
        return f"Error reading codebase.xml: {str(e)}"


def gather_context_from_project_metadata(
    project_metadata: Dict[str, Any]
) -> str:
    """
    从项目元数据中提取上下文信息并转换为字符串。
    """
    try:
        if not project_metadata:
            return "No project_metadata found or provided."
        metadata_str = json.dumps(
            project_metadata,
            indent=2,
            ensure_ascii=False
        )
        return f"Project Metadata:\n{metadata_str}\n"
    except Exception as e:
        return f"Error converting project_metadata: {str(e)}"


def gather_context_from_project_info_mdx(
    mdx_path: str
) -> str:
    """
    从 project_info.mdx 文件中读取项目信息。
    """
    if not os.path.exists(mdx_path):
        return "No project_info.mdx found."

    try:
        with open(mdx_path, "r", encoding="utf-8") as f:
            mdx_content = f.read()
        return mdx_content
    except Exception as e:
        return f"Error reading project_info.mdx: {str(e)}"


def gather_codebase_analysis(project_path: str) -> Dict[str, Any]:
    """
    利用 content_generator.generate_focus_content 来对项目进行扫描分析。
    然后从生成的 Markdown 中提取出关键信息如文件数量、行数、警报等。
    """
    config = load_config() or {}
    markdown_report = generate_focus_content(project_path, config)
    analysis_data = {}
    lines = markdown_report.splitlines()
    metrics_section_found = False

    for line in lines:
        if line.strip().startswith("# Project Metrics Summary"):
            metrics_section_found = True
            continue

        if metrics_section_found:
            if "Total Files:" in line:
                analysis_data["total_files"] = line.split(":")[1].strip()
            elif "Total Lines:" in line:
                analysis_data["total_lines"] = line.split(":")[1].strip()
            elif line.strip().startswith("**Files by Type:**"):
                analysis_data["files_by_type"] = []
            elif line.strip().startswith("- "):
                if "files (" in line:
                    analysis_data["files_by_type"].append(
                        line.strip().lstrip("- ").strip()
                    )
            elif "**Code Quality Alerts:**" in line:
                analysis_data["code_quality_alerts"] = {}
            elif line.strip().startswith("- 🚨 Severe Length Issues:"):
                val = line.split(":")[1].strip()
                analysis_data["code_quality_alerts"]["severe_issues"] = val
            elif line.strip().startswith("- ⚠️ Critical Length Issues:"):
                val = line.split(":")[1].strip()
                analysis_data["code_quality_alerts"]["critical_issues"] = val
            elif line.strip().startswith("- 📄 Length Warnings:"):
                val = line.split(":")[1].strip()
                analysis_data["code_quality_alerts"]["warnings"] = val
            elif line.strip().startswith("- 🔄 Duplicate Functions:"):
                val = line.split(":")[1].strip()
                analysis_data["code_quality_alerts"][
                    "duplicate_functions"
                ] = val
            elif line.strip().startswith("Last updated:"):
                # 结束
                break

    return analysis_data


def combine_all_contexts(
    codebase_xml: str,
    project_metadata_text: str,
    project_info_mdx: str
) -> str:
    """
    合并所有上下文信息为单个字符串，以便传递给 LLM。
    """
    return (
        "===== codebase.xml content =====\n"
        f"{codebase_xml}\n\n"
        "===== project_metadata =====\n"
        f"{project_metadata_text}\n\n"
        "===== project_info.mdx =====\n"
        f"{project_info_mdx}\n"
    )


def build_system_prompt(
    project_info: Dict[str, Any],
    combined_context: str
) -> str:
    """
    组合预先定义好的 META_PROMPT 与收集到的上下文，构建 LLM 的 system prompt。
    """
    project_data_str = json.dumps(project_info, indent=2, ensure_ascii=False)
    # 在这里可以自由组合 META_PROMPT 与上下文
    system_prompt = (
        f"{META_PROMPT}\n\n"
        f"PROJECT_INFO:\n{project_data_str}\n\n"
        f"ADDITIONAL CONTEXT:\n{combined_context}\n"
    )
    return system_prompt


def json_serialize(obj):
    """自定义 JSON 序列化函数，处理 datetime 等特殊类型"""
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    return str(obj)


def generate_cursorrules_json(
    project_info: Dict[str, Any],
    codebase_xml_path: str,
    project_metadata: Optional[Dict[str, Any]] = None,
    project_info_mdx_path: Optional[str] = None,
    api_key: Optional[str] = None,
    project_root_path: Optional[str] = None
) -> str:
    """
    核心函数：生成 .cursorrules JSON。
    结合 codebase.xml, project_metadata, project_info.mdx 等上下文信息，
    并调用 PydanticAI 以 anthropic/claude-3.5-sonnet 模型生成最终的 JSON。
    """
    try:
        logger.info("\n=== Project Scanning Start ===")
        # 如果没有提供 project_metadata 并且提供了 project_root_path，则尝试自动扫描
        if not project_metadata and project_root_path:
            logger.info(f"Scanning project at: {project_root_path}")
            found_projects = scan_for_projects(project_root_path)
            if found_projects:
                chosen_project = found_projects[0]
                project_json = json.dumps(chosen_project, indent=2)
                logger.info(f"\nDetected project: {project_json}")

                analyzer = RulesAnalyzer(chosen_project['path'])
                analyzed_info = analyzer.analyze_project_for_rules()
                rules_json = json.dumps(analyzed_info, indent=2)
                logger.info(f"\nAnalyzed rules info: {rules_json}")

                codebase_analysis = gather_codebase_analysis(
                    chosen_project['path']
                )
                analysis_json = json.dumps(codebase_analysis, indent=2)
                logger.info(f"\nCodebase analysis: {analysis_json}")

                project_metadata = {
                    "detected_project": chosen_project,
                    "rules_analyzer_info": analyzed_info,
                    "codebase_analysis": codebase_analysis
                }
            else:
                logger.info("\nNo projects found by scanner.")
                project_metadata = {
                    "scanning": "No projects found by scanner."
                }

        if not project_metadata:
            logger.info("\nNo project metadata available, using default.")
            project_metadata = {"no_metadata": True}

        logger.info("\n=== Project Scanning Complete ===\n")

        # 获取 agent
        agent = get_agent()

        # 构建提示
        prompt = (
            "Project Info:\n"
            f"{json.dumps(project_info, indent=2)}\n\n"
            "Project Metadata:\n"
            f"{json.dumps(project_metadata, indent=2)}\n\n"
            "Please generate a valid .cursorrules JSON that follows the "
            "CursorRules schema. The output should be a complete, valid "
            "JSON object."
        )
        logger.info("\n=== Generated Prompt ===")
        logger.info(prompt)
        logger.info("=== End of Prompt ===\n")

        # 调用 AI 模型生成内容
        logger.info("\n=== Calling AI Model ===")
        try:
            result = agent.run_sync(user_prompt=prompt)
            logger.info("AI model call completed successfully")
        except Exception as model_error:
            logger.error(f"Error calling AI model: {str(model_error)}")
            raise model_error

        if not result or not result.data:
            logger.error("\nError: No data generated by the model")
            raise ValueError("No data generated by the model")

        # 记录解析后的结果
        logger.info("\n=== Model Result ===")
        try:
            result_json = json.dumps(
                result.data.model_dump(),
                indent=2,
                default=json_serialize
            )
            logger.info(result_json)
            logger.info("Model result successfully logged")
        except Exception as parse_error:
            logger.error(f"Error logging model result: {str(parse_error)}")
            logger.error(f"Result data type: {type(result.data)}")
            logger.error(f"Result data content: {str(result.data)}")
        logger.info("=== End Model Result ===\n")

        # 验证生成的内容
        logger.info("\n=== Validating Generated Content ===")
        try:
            CursorRules.model_validate(result.data.model_dump())
            logger.info("Validation successful!")
        except Exception as validation_error:
            logger.error(f"Validation failed: {str(validation_error)}")
            raise validation_error

        return result.data

    except Exception as e:
        logger.error(f"\nError in generate_cursorrules_json: {str(e)}")
        if hasattr(e, '__traceback__'):
            import traceback
            logger.error("\nFull traceback:")
            traceback.print_tb(e.__traceback__)
        return ""


def validate_cursorrules_json(content: str) -> bool:
    """
    验证 cursorrules JSON 内容的函数。
    如果可以解析并被 CursorRules 接受，则认为有效。
    """
    try:
        data = json.loads(content)
        CursorRules.parse_obj(data)
        return True
    except Exception:
        return False


def save_cursorrules(content: str, project_path: str) -> None:
    """
    保存生成的 .cursorrules 内容到项目目录。

    Args:
        content: 生成的 .cursorrules JSON 内容
        project_path: 项目根目录路径
    """
    cursorrules_path = os.path.join(project_path, ".cursorrules")
    try:
        # 如果内容是 CursorRules 对象，将其转换为 JSON 字符串
        if isinstance(content, CursorRules):
            content = json.dumps(
                content.model_dump(),
                indent=2,
                default=json_serialize
            )
        with open(cursorrules_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Successfully generated .cursorrules at {cursorrules_path}")
    except Exception as e:
        print(f"Error saving .cursorrules: {e}")
        logger.error(f"Error saving .cursorrules: {e}")
        if hasattr(e, '__traceback__'):
            logger.error("\nFull traceback:")
            traceback.print_tb(e.__traceback__)


def main():
    """主入口点，处理命令行参数并执行生成过程。"""
    parser = argparse.ArgumentParser(
        description="Generate .cursorrules for a project"
    )
    parser.add_argument(
        "--project_path",
        required=True,
        help="Path to the project root directory"
    )
    args = parser.parse_args()

    project_path = os.path.abspath(args.project_path)
    if not os.path.exists(project_path):
        print(f"Error: Project path {project_path} does not exist")
        return 1

    try:
        # 准备基本的项目信息
        project_info = {
            "name": os.path.basename(project_path),
            "path": project_path,
            "type": "vscode_extension"  # 从配置或检测中获取
        }

        # 生成 .cursorrules JSON
        cursorrules_content = generate_cursorrules_json(
            project_info=project_info,
            codebase_xml_path=os.path.join(project_path, "codebase.xml"),
            project_root_path=project_path
        )

        if cursorrules_content:
            # 保存生成的内容
            save_cursorrules(cursorrules_content, project_path)
            return 0
        else:
            print("Error: Failed to generate .cursorrules content")
            return 1

    except Exception as e:
        print(f"Error generating .cursorrules: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
