#!/bin/sh

# Enable local ESXi Shell
vim-cmd hostsvc/enable_esx_shell
vim-cmd hostsvc/start_esx_shell

# Enable remote ESXi Shell (TSM SSH)
vim-cmd hostsvc/enable_ssh
vim-cmd hostsvc/start_ssh

