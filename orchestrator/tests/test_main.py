"""Tests for DFIReballz orchestrator."""


def test_import_main():
    """Test that main module can be imported."""
    from main import app
    assert app is not None
    assert app.title == "DFIReballz Orchestrator"


def test_import_case_manager():
    """Test that case_manager module can be imported."""
    from case_manager import CaseManager
    assert CaseManager is not None


def test_import_playbook_runner():
    """Test that playbook_runner module can be imported."""
    from playbook_runner import PlaybookRunner
    assert PlaybookRunner is not None


def test_import_report_generator():
    """Test that report_generator module can be imported."""
    from report_generator import ReportGenerator
    assert ReportGenerator is not None


def test_case_create_model():
    """Test CaseCreate pydantic model."""
    from main import CaseCreate
    case = CaseCreate(title="Test Case", case_type="malware_analysis")
    assert case.title == "Test Case"
    assert case.case_type == "malware_analysis"
    assert case.classification == "confidential"


def test_ioc_create_model():
    """Test IOCCreate pydantic model."""
    from main import IOCCreate
    ioc = IOCCreate(ioc_type="ip", value="192.168.1.1")
    assert ioc.ioc_type == "ip"
    assert ioc.value == "192.168.1.1"
    assert ioc.confidence == 50
