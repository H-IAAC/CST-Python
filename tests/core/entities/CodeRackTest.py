import unittest

class Test(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

    def tearDown(self) -> None:
        super().tearDown()

    @classmethod
    def tearDownClass(cls):
        ...

    def test_(self) -> None:
        ...