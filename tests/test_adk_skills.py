from moodle_mcp.adk.agents import EDUCATION_AGENT_SPECS
from moodle_mcp.adk.skills import EDUCATION_SKILLS, SKILLS_BY_NAME, SUPPORTED_MOODLE_TOOLS


def test_education_skill_names_are_unique():
    names = [skill.name for skill in EDUCATION_SKILLS]

    assert len(names) == len(set(names))
    assert set(names) == set(SKILLS_BY_NAME)


def test_education_skills_only_reference_known_supported_tools():
    for skill in EDUCATION_SKILLS:
        assert set(skill.supported_tools) <= SUPPORTED_MOODLE_TOOLS


def test_broad_mvp_skill_catalog_is_present():
    assert {
        "course-creation-skill",
        "lesson-planning-skill",
        "assessment-builder-skill",
        "student-tutor-skill",
        "admin-enrollment-skill",
        "progress-engagement-skill",
        "content-curator-skill",
        "support-assistant-skill",
    } == {skill.name for skill in EDUCATION_SKILLS}


def test_agent_specs_reference_existing_skills():
    for spec in EDUCATION_AGENT_SPECS:
        assert spec.skill_names
        assert set(spec.skill_names) <= set(SKILLS_BY_NAME)
        assert spec.description
        assert "future tool" in spec.instruction()
