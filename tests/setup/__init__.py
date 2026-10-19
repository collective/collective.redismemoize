"""What loading the package registers, and the layer offered to integrators.

The package has no GenericSetup profile: the chooser is a global utility, the
same for every site in the process, so there is nothing to install per site.
"""

#: The REST service, as registered for the site root.
SERVICE = "@redismemoize"
