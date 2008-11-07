
import os
import sys
from appinst.platforms.shortcut_creation_error import ShortcutCreationError

##############################################################################
# THIS CODE NOT YET TESTED OR COMPLETE
##############################################################################

class OSX(object):
    """
    A class for application installation operations on Mac OS X.

    """

    #==========================================================================
    # Public API methods
    #==========================================================================

    def install_application_menus(self, menus, shortcuts, mode):
        """
        Install application menus.

        """

        try:
            self._install_application_menus(menus, shortcuts)
        except ShortcutCreationError, ex:
            warnings.warn(ex.message)

        return

    #==========================================================================
    # Internal API methods
    #==========================================================================

    def _install_application_menus(self, menus, shortcuts):
        dir_path = '/Applications'
        queue = [(dir_path, menu_spec, '') for menu_spec in menus]
        category_map = {}
        while len(queue) > 0:
            dir_path, menu_spec, parent_category = queue.pop(0)
            
            # Directory name should match the menu name
            dir_path = os.path.join(dir_path, menu_spec['name'])
        
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
            
            # id's of the menus will be mapped to categories of the shortcuts
            # if no category is present. This determines which directories to
            # put shortcuts in
            category = menu_spec.get('category',
                menu_spec.get('id').capitalize())

            if len(parent_category) > 1:
                category = '%s.%s' % (parent_category, category)

            category_map[category] = dir_path

            # For every sub-menu, append the directory containing the sub-menu,
            # the sub-menu, spec, and it's category.
            for child_spec in menu_spec.get('sub-menus', []):
                queue.append((dir_path, child_spec, category))

        SHELL_SCRIPT ="#!/bin/sh\n%s %s\n"
        
        for shortcut in shortcuts:
            for mapped_category in shortcut['categories']:
                cmd = shortcut['cmd']
                args = []
                # Finder is automatically launched when a folder link is 
                # selected, so {{FILEBROWSER}} (which specifies the file manager
                # on linux) can be removed.
                # There is also a webbrowser check which returns 'default'
                # OS X, so we should check for that as well.
                if cmd[0] == '{{FILEBROWSER}}' or cmd[0] == 'default':
                    del cmd[0]
                
                # In case the command has arguements, e.g. ipython -pylab
                if len(cmd) > 1:
                    args = cmd[1:]
                
                # If the file is executable, create a double-clickable shell
                # script that will execute it
                if os.path.isfile(cmd[0]) and os.access(cmd[0], os.X_OK):
                    target_name = os.path.basename(cmd[0]) + '.command'
                    target_path = os.path.join(category_map[mapped_category],
                        target_name)
                    f_script = open(target_path, 'w')
                    f_script.write(SHELL_SCRIPT % (cmd[0], ' '.join(args)))
                    f_script.close()
                    os.chmod(target_path, 0755)
                else:
                    # It's possible we may only need this section. Symlinks to
                    # executable scripts are double-clickable on 10.5, although
                    # there would be no way to figure out custom icons.
                    target_name = os.path.basename(cmd[0])
                    target_path = os.path.join(category_map[mapped_category],
                        target_name)
                    if not os.path.exists(target_path):
                        os.symlink(cmd[0], target_path)