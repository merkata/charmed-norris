# Copyright 2022 Mariyan Dimitrov
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

import unittest

from unittest.mock import patch
from ops.model import ActiveStatus
from ops.testing import Harness
from charm import CharmedNorrisCharm


class TestCharm(unittest.TestCase):
    def setUp(self):
        self.harness = Harness(CharmedNorrisCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def test_on_config_changed(self):
        self.assertEqual(self.harness.charm.config["category"], "")
        expected = {
            "summary": "norris layer",
            "description": "pebble config layer for norris",
            "services": {
                "norris": {
                    "override": "replace",
                    "summary": "norris",
                    "command": "/charmed-norris",
                    "startup": "enabled",
                    "environment": {
                        "CHUCK_CATEGORY": ""
                    },
                }
            },
        }
        self.assertEqual(self.harness.charm._norris_layer(), expected)
        # Simulate making the Pebble socket available
        self.harness.set_can_connect("norris", True)
        # And now test with a different value in the redirect-map config option.
        self.harness.update_config({"category": "dev"})
        expected["services"]["norris"]["environment"]["CHUCK_CATEGORY"] = "dev"
        self.assertEqual(self.harness.charm._norris_layer(), expected)
        container = self.harness.model.unit.get_container("norris")
        self.assertEqual(container.get_service("norris").is_running(), True)
        self.assertEqual(self.harness.model.unit.status, ActiveStatus())

        # Now test again with different config, knowing that the "norris"
        # service is running (because we've just tested it above), so we'll
        # be testing the `is_running() == True` codepath.
        self.harness.update_config({"category": "religion"})
        plan = self.harness.get_container_pebble_plan("norris")
        # Adjust the expected plan
        expected["services"]["norris"]["environment"]["CHUCK_CATEGORY"] = "religion"
        expected.pop("description")
        expected.pop("summary")
        self.assertEqual(plan.to_dict(), expected)
        self.assertEqual(container.get_service("norris").is_running(), True)
        self.assertEqual(self.harness.model.unit.status, ActiveStatus())

        # And finally test again with the same config to ensure we exercise
        # the case where the plan we've created matches the active one. We're
        # going to mock the container.stop and container.start calls to confirm
        # they were not called.
        with patch('ops.model.Container.start') as _start,\
                patch('ops.model.Container.stop') as _stop:
            self.harness.charm.on.config_changed.emit()
            _start.assert_not_called()
            _stop.assert_not_called()

    def test_norris_pebble_ready(self):
        # Simulate making the Pebble socket available
        self.harness.set_can_connect("norris", True)
        # Check the initial Pebble plan is empty
        initial_plan = self.harness.get_container_pebble_plan("norris")
        self.assertEqual(initial_plan.to_yaml(), "{}\n")
        # Expected plan after Pebble ready with default config
        expected_plan = self.harness.charm._norris_layer()
        expected_plan.pop("description", "")
        expected_plan.pop("summary", "")
        # Get the norris container from the model
        container = self.harness.model.unit.get_container("norris")
        # Emit the PebbleReadyEvent carrying the norris container
        self.harness.charm.on.norris_pebble_ready.emit(container)
        # Get the plan now we've run PebbleReady
        updated_plan = self.harness.get_container_pebble_plan("norris").to_dict()
        # Check we've got the plan we expected
        self.assertEqual(expected_plan, updated_plan)
        # Check the service was started
        service = self.harness.model.unit.get_container("norris").get_service("norris")
        self.assertTrue(service.is_running())
        # Ensure we set an ActiveStatus with no message
        self.assertEqual(self.harness.model.unit.status, ActiveStatus())
