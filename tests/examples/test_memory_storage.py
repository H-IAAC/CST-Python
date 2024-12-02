import os
import re

from testbook import testbook
from testbook.client import TestbookNotebookClient

from ..utils import get_examples_path

examples_path = get_examples_path()

@testbook(os.path.join(examples_path, "Memory Storage.ipynb"), execute=True)
def test_gym_integration(tb :TestbookNotebookClient):
    
    expected_result = {"info1":"'First node info'",
                       "info2":"''",
                       "info3":"'First node info'",
                       "info4":"'Second node info'",
                       "info5":"[1, 2, 3]",
                       }
    
    for tag in expected_result:
        result = tb.cell_output_text(tag)

        assert result == expected_result[tag]


