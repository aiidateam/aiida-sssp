# -*- coding: utf-8 -*-
import os
import ipywidgets as ipw
from traitlets import Instance

from aiida_sssp import __version__
from aiida_sssp.groups.family import SsspFamily
from aiida_sssp.cli.list import get_sssp_families_builder
from aiida_sssp.cli.install import URL_BASE, URL_MAPPING, download_family

from aiida import load_profile

load_profile()


class SsspSelectorWidget(ipw.VBox):
    """Jupyter widget to install and select SSSP family."""

    family = Instance(SsspFamily, allow_none=True)

    def __init__(self, **kwargs):
        """Initialize SsspSelectorWidget."""
        self.dropdown = ipw.Dropdown(
            label='Select the family',
            options=[('Select the family', (None, None, None))] + [(v, k) for k, v in URL_MAPPING.items()],
        )
        self.dropdown.observe(self.validate_family_selection, names=['value'])
        self.install_button = ipw.Button(description='Install family', layout={'visibility': 'hidden'})
        self.install_button.on_click(self.install_family)
        self.output = ipw.HTML()
        super().__init__(children=[ipw.HBox([self.dropdown, self.install_button]), self.output], **kwargs)

    def validate_family_selection(self, change=None):
        """Check if selected family is installed. If not, enable the functionality to do install."""
        installed = get_sssp_families_builder(*change['new']).all(flat=True)
        if len(installed) == 1:
            self.output.value = ''
            self.button.hidden = True
            self.family = installed[0]
            return
        if len(installed) > 1:
            raise ValueError('More then one family found. Something is wrong.')
        self.output.value = 'Family is not installed, do you want me to install it?'
        self.install_button.layout.visibility = 'visible'

    def install_family(self, _=None):
        """Install pseudo family."""
        url_base = os.path.join(URL_BASE, self.dropdown.label)
        label = '{}/{}/{}/{}'.format('SSSP', *self.dropdown.value)
        description = 'SSSP v{} {} {} installed with aiida-sssp v{}'.format(*self.dropdown.value, __version__)
        download_family(url_base, label=label, description=description)
