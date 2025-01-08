import os
import json
from pathlib import Path
import pytest
from cursorrules_generation import (
    generate_cursorrules_json,
    validate_cursorrules_json,
    save_cursorrules
)


@pytest.fixture
def test_project_path():
    """返回测试项目路径"""
    current_dir = Path(__file__).parent
    return str(current_dir / "test_project")


@pytest.fixture
def project_info():
    """返回测试项目基本信息"""
    return {
        "name": "TestProject",
        "version": "0.1.0",
        "description": "Test project for cursorrules generation",
        "type": "python_project"
    }


def test_generate_cursorrules(test_project_path, project_info):
    """测试生成 .cursorrules JSON"""
    # 准备测试数据
    project_info_mdx = os.path.join(test_project_path, "project_info.mdx")
    assert os.path.exists(project_info_mdx), "project_info.mdx should exist"

    # 生成 .cursorrules
    result = generate_cursorrules_json(
        project_info=project_info,
        codebase_xml_path=os.path.join(test_project_path, "codebase.xml"),
        project_info_mdx_path=project_info_mdx,
        project_root_path=test_project_path
    )

    # 验证结果
    assert result is not None, "Should generate content"
    
    # 保存结果
    save_cursorrules(result, test_project_path)
    
    # 验证生成的文件
    cursorrules_path = os.path.join(test_project_path, ".cursorrules")
    assert os.path.exists(cursorrules_path), ".cursorrules should be created"
    
    # 验证JSON格式
    with open(cursorrules_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert validate_cursorrules_json(content), "Should be valid JSON"


def test_validate_cursorrules_json():
    """测试JSON验证功能"""
    # 有效的JSON
    valid_json = {
        "name": ".cursorrules",
        "version": "1.0.0",
        "last_updated": "2024-03-21T10:00:00Z",
        "project_analysis": {
            "basic_info": {
                "name": "TestProject",
                "version": "0.1.0",
                "language": "python",
                "frameworks": {
                    "frontend": [],
                    "backend": ["fastapi"],
                    "ml": ["langchain"],
                    "ai": ["openai"]
                },
                "type": "python_project",
                "environment": {
                    "python_version": "3.9",
                    "node_version": "N/A",
                    "cuda_support": False
                }
            },
            "ai_behavior": {
                "code_generation": {
                    "style": {
                        "prefer": ["PEP8"],
                        "avoid": []
                    },
                    "error_handling": {
                        "strategies": ["try-except"],
                        "logging": ["structured"]
                    },
                    "performance": {
                        "optimization": [],
                        "memory_management": []
                    }
                },
                "ai_specific": {
                    "llm_integration": {
                        "providers": ["openai"],
                        "model_configurations": []
                    },
                    "agent_system": {
                        "architecture": "simple",
                        "communication": [],
                        "roles": []
                    },
                    "ml_pipeline": {
                        "frameworks": ["langchain"],
                        "data_processing": [],
                        "model_management": []
                    }
                }
            },
            "development_standards": {
                "testing": {
                    "frameworks": ["pytest"],
                    "coverage": {
                        "threshold": 80.0,
                        "excludes": []
                    },
                    "types": ["unit", "integration"]
                },
                "documentation": {
                    "style": "google",
                    "required_sections": [
                        "Args",
                        "Returns",
                        "Raises"
                    ],
                    "api_documentation": True
                },
                "code_quality": {
                    "linters": ["flake8"],
                    "formatters": ["black"],
                    "metrics": ["complexity"]
                }
            }
        },
        "project_info": {
            "name": "TestProject",
            "description": "Test project for cursorrules generation",
            "objectives": [
                "Test .cursorrules generation",
                "Validate JSON schema",
                "Verify AI integration"
            ],
            "architecture": "microservices",
            "team_structure": [
                "Lead Developer",
                "AI Engineer",
                "QA Engineer"
            ],
            "development_process": "Agile with 2-week sprints"
        }
    }
    
    assert validate_cursorrules_json(
        json.dumps(valid_json)
    ), "Valid JSON should pass validation"

    # 无效的JSON - 缺少必要字段
    invalid_json = {
        "name": ".cursorrules",
        "version": "1.0.0"
    }
    assert not validate_cursorrules_json(
        json.dumps(invalid_json)
    ), "Invalid JSON should fail validation" 