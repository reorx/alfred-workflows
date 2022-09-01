#!/bin/bash

workflows_dir="$HOME/Library/Application Support/Alfred/Alfred.alfredpreferences/workflows"

rsync -ar "$workflows_dir/user.workflow.$1/" $2
