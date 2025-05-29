#!/bin/bash
# Script to prepare data files for packaging
# This copies data/ to share/ulauncher/ which is what pdm-backend expects

rm -rf share/
mkdir -p share/ulauncher
cp -r data/* share/ulauncher/
echo "Data files prepared in share/ulauncher/"
