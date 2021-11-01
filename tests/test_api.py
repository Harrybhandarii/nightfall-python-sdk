import os
import pytest

from nightfall.api import Nightfall
from nightfall.detection_rules import DetectionRule, Detector, LogicalOp, Confidence, ExclusionRule, ContextRule, \
    WordList, MatchType, RedactionConfig, MaskConfig, Regex
from nightfall.findings import Finding, Range


@pytest.fixture
def nightfall():
    yield Nightfall(os.environ['NIGHTFALL_API_KEY'])


def test_scan_text_detection_rules_v3(nightfall):
    result, redactions = nightfall.scan_text(
        ["4916-6734-7572-5015 is my credit card number"],
        detection_rules=[DetectionRule(logical_op=LogicalOp.ANY, detectors=[
            Detector(min_confidence=Confidence.LIKELY,
                     min_num_findings=1,
                     display_name="Credit Card Number",
                     nightfall_detector="CREDIT_CARD_NUMBER",
                     context_rules=[ContextRule(regex=Regex("fake regex", is_case_sensitive=False),
                                                window_before=10, window_after=10,
                                                fixed_confidence=Confidence.VERY_UNLIKELY)],
                     exclusion_rules=[ExclusionRule(MatchType.FULL,
                                                    word_list=WordList(["never", "match"],
                                                                       is_case_sensitive=True))],
                     redaction_config=RedactionConfig(remove_finding=False,
                                                      mask_config=MaskConfig(masking_char='👀',
                                                                             num_chars_to_leave_unmasked=3,
                                                                             chars_to_ignore=["-"]))
                     )])]
    )

    assert len(result) == 1
    assert result[0][0] == Finding(
        "4916-6734-7572-5015",
        '491👀-👀👀👀👀-👀👀👀👀-👀👀👀👀',
        None, None,
        "Credit Card Number",
        result[0][0].detector_uuid,
        Confidence.VERY_LIKELY,
        Range(0, 19), Range(0, 19),
        [], ["Inline Detection Rule #1"])
    assert len(redactions) == 1
    assert redactions[0] == "491👀-👀👀👀👀-👀👀👀👀-👀👀👀👀 is my credit card number"


@pytest.mark.filetest
def test_scan_file_detection_rules(nightfall):
    file = "file.txt"

    with open(file, "w") as fp:
        fp.write("4916-6734-7572-5015 is my credit card number")

    id, message = nightfall.scan_file(
        file,
        os.environ['WEBHOOK_ENDPOINT'],
        detection_rules=[DetectionRule(logical_op=LogicalOp.ANY, detectors=[
            Detector(min_confidence=Confidence.LIKELY, min_num_findings=1,
                     display_name="Credit Card Number", nightfall_detector="CREDIT_CARD_NUMBER")])]
    )

    assert id is not None
    assert message == 'scan initiated'
