#!/bin/bash

workflows_dir="$ALFRED_PREF_DIR/Alfred.alfredpreferences/workflows"
dest_dir="src/$2"

mkdir -p "$dest_dir"

rsync -ar "$workflows_dir/user.workflow.$1/" "$dest_dir"
