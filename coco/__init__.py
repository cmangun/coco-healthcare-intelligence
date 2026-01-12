"""
CoCo: Careware for Healthcare Intelligence

End-to-end healthcare AI platform demonstrating the 12-phase
Forward Deployed Engineering production playbook.
"""

__version__ = "1.0.0"
__author__ = "Christopher Mangun"
__email__ = "cmangun@gmail.com"

from coco.workflows.care_gap_workflow import CareGapWorkflow
from coco.workflows.readmission_workflow import ReadmissionWorkflow
from coco.workflows.summarization_workflow import SummarizationWorkflow

__all__ = [
    "CareGapWorkflow",
    "ReadmissionWorkflow",
    "SummarizationWorkflow",
]
