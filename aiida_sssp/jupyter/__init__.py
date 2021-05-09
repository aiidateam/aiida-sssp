# -*- coding: utf-8 -*-
import os
import ipywidgets as ipw
from traitlets import Instance
from IPython.display import clear_output

from aiida_sssp import __version__
from aiida_sssp.groups.family import SsspFamily
from aiida_sssp.cli.list import get_sssp_families_builder
from aiida_sssp.cli.install import URL_BASE, URL_MAPPING, download_family

from aiida import load_profile

load_profile()


class SsspSelectorWidget(ipw.VBox):
    """Jupyter widget to install and select SSSP family.

    family(SsspFamily): trait that points to the selected SsspFamily instance.
    """

    family = Instance(SsspFamily, allow_none=True)

    def __init__(self, description='Pseudopotential family', **kwargs):
        """Initialize SsspSelectorWidget."""
        self.dropdown = ipw.Dropdown(
            description=description,
            label='Select the family',
            options=[('Select the family', (None, None, None))] + [(v, k) for k, v in URL_MAPPING.items()],
            style={'description_width': 'initial'},
        )
        self.dropdown.observe(self.validate_family_selection, names=['value'])
        self.install_button = ipw.Button(description='Install family', layout={'visibility': 'hidden'})
        self.install_button.on_click(self.install_family)
        self.output = ipw.HTML()
        self.download_log = ipw.Output()
        super().__init__(
            children=[ipw.HBox([self.dropdown, self.install_button]), self.output, self.download_log], **kwargs
        )

    def validate_family_selection(self, _=None):
        """Check if selected family is installed. If not, enable the functionality to do install."""
        query = get_sssp_families_builder(*self.dropdown.value)
        installed = query.all(flat=True)  # pylint: disable=unexpected-keyword-arg
        if len(installed) == 1:
            self.output.value = ''
            self.install_button.layout.visibility = 'hidden'
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
        with self.download_log:
            download_family(url_base, label=label, description=description)
            clear_output()
        self.validate_family_selection()
