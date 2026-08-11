from app.agent import root_agent


def test_agent_has_only_administrative_tools() -> None:
    assert root_agent.name == "doctor_apple"
    assert {getattr(tool, "name", tool.__name__) for tool in root_agent.tools} == {
        "find_patient",
        "resolve_eligibility",
        "check_requested_tests",
        "generate_questionnaire_prefill",
    }
