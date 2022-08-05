#!/usr/bin/env python3
# Copyright 2022 Mariyan Dimitrov
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Charm the service.

Refer to the following post for a quick-start guide that will help you
develop a new k8s charm using the Operator Framework:

    https://discourse.charmhub.io/t/4208
"""

import logging

from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus
from charms.nginx_ingress_integrator.v0.ingress import IngressRequires

logger = logging.getLogger(__name__)


class CharmedNorrisCharm(CharmBase):
    """Charm the service."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(
                self.on.norris_pebble_ready, self._on_norris_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)

        self.ingress = IngressRequires(self, {
            "service-hostname": "charmed.norris",
            "service-name": self.app.name,
            "service-port": 3333
        })

    def _norris_layer(self):
        """Returns a Pebble configration layer for Norris"""
        return {
		    "summary": "norris layer",
		    "description": "pebble config layer for norris",
		    "services": {
		    	"norris": {
		    		"override": "replace",
		    		"summary": "norris",
		    		"command": "/charmed-norris",
		    		"startup": "enabled",
		    		"environment": {
						"CHUCK_CATEGORY": self.config["category"]
						},
		    		}
		    	},
		    }

    def _on_norris_pebble_ready(self, event):
        """Define and start a workload using the Pebble API.

        TEMPLATE-TODO: change this example to suit your needs.
        You'll need to specify the right entrypoint and environment
        configuration for your specific workload. Tip: you can see the
        standard entrypoint of an existing container using docker inspect

        Learn more about Pebble layers at https://github.com/canonical/pebble
        """
        # Get a reference the container attribute on the PebbleReadyEvent
        container = event.workload
        # Define an initial Pebble layer configuration
        pebble_layer = self._norris_layer()
        # Add initial Pebble config layer using the Pebble API
        container.add_layer("norris", pebble_layer, combine=True)
        # Autostart any services that were defined with startup: enabled
        container.autostart()
        # Learn more about statuses in the SDK docs:
        # https://juju.is/docs/sdk/constructs#heading--statuses
        self.unit.status = ActiveStatus()


    def _on_config_changed(self, _):
        """Just an example to show how to deal with changed configuration.

        TEMPLATE-TODO: change this example to suit your needs.
        If you don't need to handle config, you can remove this method,
        the hook created in __init__.py for it, the corresponding test,
        and the config.py file.

        Learn more about config at https://juju.is/docs/sdk/config
        """
        # Get the norris container so we can configure/manipulate it
        container = self.unit.get_container("norris")
        # Create a new config layer
        layer = self._norris_layer()
        # Get the current config
        services = container.get_plan().to_dict().get("services", {})
        # Check if there are any changes to services
        if services != layer["services"]:
            # Changes were made, add the new layer
            container.add_layer("norris", layer, combine=True)
            logging.info("Added updated layer 'norris' to Pebble plan")
            # Stop the service if it is already running
            if container.get_service("norris").is_running():
                container.stop("norris")
            # Restart it and report a new status to Juju
            container.start("norris")
            logging.info("Restarted norris service")
        self.ingress.update_config({"service-hostname": "charmed.norris", "service-port": 3333})
        # All is well, set an ActiveStatus
        self.unit.status = ActiveStatus()

if __name__ == "__main__":
    main(CharmedNorrisCharm)
