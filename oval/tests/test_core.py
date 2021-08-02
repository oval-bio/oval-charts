"""
Tests for the atxcf.core module.
"""
import os
import tempfile
import unittest
import zipfile

import oval.core


class TestCore(unittest.TestCase):
    def setUp(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            self._tmpfile = f.name

    def tearDown(self):
        os.remove(self._tmpfile)

    def test_core_bundle_create(self):
        """
        Test creating an oval data bundle.
        """
        # with
        metadata = {
            "test_value": 123,
            "test_value2": 124}
        bundle = oval.core.Bundle(self._tmpfile)

        # when
        bundle.create(**metadata)

        # then
        self.assertEqual(
            bundle.read_attribute("test_value"),
            metadata["test_value"])
        self.assertEqual(
            bundle.read_attribute("test_value2"),
            metadata["test_value2"])
