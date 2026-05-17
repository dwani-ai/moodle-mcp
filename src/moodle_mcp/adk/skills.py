from dataclasses import dataclass


SUPPORTED_MOODLE_TOOLS = frozenset(
    {
        "get_current_user",
        "list_course_categories",
        "create_course",
        "add_url_resource",
        "add_page_resource",
        "list_my_courses",
        "get_course_contents",
        "get_activities_completion_status",
        "get_users_by_field",
    }
)


@dataclass(frozen=True)
class EducationSkill:
    """ADK skill metadata for an education workflow."""

    name: str
    title: str
    purpose: str
    supported_tools: tuple[str, ...]
    future_tools: tuple[str, ...]
    instructions: tuple[str, ...]

    def instruction_block(self) -> str:
        supported = ", ".join(self.supported_tools) or "none yet"
        future = ", ".join(self.future_tools) or "none"
        steps = "\n".join(f"- {instruction}" for instruction in self.instructions)
        return (
            f"Skill: {self.title} ({self.name})\n"
            f"Purpose: {self.purpose}\n"
            f"Supported Moodle tools: {supported}.\n"
            f"Future Moodle tools: {future}.\n"
            f"Workflow guidance:\n{steps}"
        )


EDUCATION_SKILLS: tuple[EducationSkill, ...] = (
    EducationSkill(
        name="course-creation-skill",
        title="Course Creation",
        purpose="Create Moodle-ready course shells and starter resources.",
        supported_tools=(
            "list_course_categories",
            "create_course",
            "add_url_resource",
            "add_page_resource",
            "get_course_contents",
        ),
        future_tools=("create_section", "upload_file", "duplicate_course"),
        instructions=(
            "Start by finding the right category before proposing a course shell.",
            "Ask for missing fullname, shortname, category, visibility, and target audience.",
            "Use URL resources for starter materials when the user provides external links.",
            "Describe future content or section changes clearly when Moodle tools are not available.",
        ),
    ),
    EducationSkill(
        name="lesson-planning-skill",
        title="Lesson Planning",
        purpose="Design lesson outlines, learning objectives, activities, and Moodle-ready plans.",
        supported_tools=(
            "get_course_contents",
            "add_page_resource",
            "add_url_resource",
            "list_course_categories",
        ),
        future_tools=("create_assignment", "create_forum", "create_book"),
        instructions=(
            "Convert broad topics into objectives, prerequisites, activities, and checks for understanding.",
            "Use course contents to align new lesson plans with existing sections.",
            "Prefer Moodle-ready structure: section title, objective, activity, resource, assessment.",
            "Flag any activity that needs a future Moodle creation tool before claiming it was created.",
        ),
    ),
    EducationSkill(
        name="assessment-builder-skill",
        title="Assessment Builder",
        purpose="Draft quizzes, rubrics, question banks, and assessment instructions.",
        supported_tools=("get_course_contents",),
        future_tools=("create_quiz", "create_question", "create_assignment", "create_rubric"),
        instructions=(
            "Ask for learning outcomes, difficulty, question count, grading policy, and feedback style.",
            "Generate balanced assessments across recall, application, and analysis.",
            "Produce Moodle-ready quiz and rubric drafts even when creation tools are pending.",
            "Never imply quizzes or grades were written to Moodle until the matching tool exists.",
        ),
    ),
    EducationSkill(
        name="student-tutor-skill",
        title="Student Tutor",
        purpose="Help learners understand course content and choose next study steps.",
        supported_tools=(
            "list_my_courses",
            "get_course_contents",
            "get_activities_completion_status",
            "get_current_user",
        ),
        future_tools=("get_grades", "get_feedback"),
        instructions=(
            "Ground answers in enrolled courses and visible course contents when possible.",
            "Explain concepts at the learner's level and ask one clarifying question when context is thin.",
            "Recommend next actions using section/module names from Moodle.",
            "Avoid changing Moodle state for student workflows.",
        ),
    ),
    EducationSkill(
        name="admin-enrollment-skill",
        title="Admin Enrollment",
        purpose="Guide user lookup, enrollment, role, cohort, and access workflows.",
        supported_tools=("get_current_user", "get_users_by_field", "list_course_categories", "list_my_courses"),
        future_tools=("enrol_user", "unenrol_user", "assign_role", "manage_cohort"),
        instructions=(
            "Identify whether the request is informational, access troubleshooting, or an enrollment change.",
            "Explain required Moodle permissions and token capabilities before administrative changes.",
            "When enrollment tools are missing, provide a precise Moodle UI or Web Services checklist.",
            "Treat role and cohort changes as high-impact operations requiring explicit confirmation.",
        ),
    ),
    EducationSkill(
        name="progress-engagement-skill",
        title="Progress Engagement",
        purpose="Summarize learner engagement and identify possible support interventions.",
        supported_tools=("list_my_courses", "get_course_contents", "get_activities_completion_status"),
        future_tools=("get_grades", "get_logs", "get_activity_report"),
        instructions=(
            "Use available course structure to frame what progress signals should be reviewed.",
            "Do not fabricate grades, completion status, or risk scores without reporting tools.",
            "Suggest supportive interventions before punitive escalation.",
            "Separate observed Moodle data from inferred recommendations.",
        ),
    ),
    EducationSkill(
        name="content-curator-skill",
        title="Content Curator",
        purpose="Recommend, organize, and add education resources to Moodle courses.",
        supported_tools=(
            "get_course_contents",
            "add_page_resource",
            "add_url_resource",
            "list_course_categories",
        ),
        future_tools=("upload_file", "create_folder", "tag_resource"),
        instructions=(
            "Ask for learner level, topic, resource type, license constraints, and course section.",
            "Prefer concise resource descriptions that explain why the item supports the objective.",
            "Use URL resource creation only after the target course and section are clear.",
            "Mention file/page creation as pending when the content is not URL-based.",
        ),
    ),
    EducationSkill(
        name="support-assistant-skill",
        title="Support Assistant",
        purpose="Help teachers and students navigate Moodle and resolve common setup issues.",
        supported_tools=("get_current_user", "get_users_by_field", "list_my_courses", "get_course_contents"),
        future_tools=("reset_password", "inspect_capabilities", "get_site_config"),
        instructions=(
            "Diagnose whether the issue is login, enrollment, visibility, content, or Web Services setup.",
            "Use current user and course visibility data before recommending admin action.",
            "Give step-by-step Moodle UI guidance when a direct tool is not available.",
            "Escalate token, role, or capability issues with the exact missing capability when known.",
        ),
    ),
)


SKILLS_BY_NAME = {skill.name: skill for skill in EDUCATION_SKILLS}


def skill_instruction(names: tuple[str, ...]) -> str:
    return "\n\n".join(SKILLS_BY_NAME[name].instruction_block() for name in names)
