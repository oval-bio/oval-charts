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
        self.assertTrue(bundle.has_attribute("test_value"))
        self.assertEqual(
            bundle.read_attribute("test_value"),
            metadata["test_value"])
        self.assertEqual(
            bundle.read_attribute("test_value2"),
            metadata["test_value2"])

    def test_core_bundle_attributes(self):
        """
        Test listing metadata attributes.
        """
        # with
        metadata = {
            "test_value": 123,
            "test_value2": 124}
        bundle = oval.core.Bundle(self._tmpfile)

        # when
        bundle.create(**metadata)

        # then
        attributes = bundle.attributes()
        for key in metadata.keys():
            self.assertIn(key, attributes)

    def test_core_bundle_write_attribute(self):
        """
        Test writing an oval data bundle attribute.
        """
        # with
        metadata = {
            "test_value": 123,
            "test_value2": 124}
        bundle = oval.core.Bundle(self._tmpfile)

        # when
        bundle.create(**metadata)
        bundle.write_attribute("test_value3", 1000.0)

        # then
        self.assertEqual(
            bundle.read_attribute("test_value3"),
            1000.0)

    def test_core_bundle_remove_attribute(self):
        """
        Test removing an oval data bundle attribute.
        """
        # with
        metadata = {
            "test_value": 123,
            "test_value2": 124}
        bundle = oval.core.Bundle(self._tmpfile)

        # when
        bundle.create(**metadata)
        bundle.remove_attribute("test_value2")

        # then
        self.assertIn("test_value", bundle.attributes())
        self.assertNotIn("test_value2", bundle.attributes())

    def test_core_num_charts_0(self):
        """
        Test num charts default.
        """
        # with
        bundle = oval.core.Bundle(self._tmpfile)

        # when
        bundle.create()

        # then
        self.assertEqual(bundle.num_charts(), 0)
