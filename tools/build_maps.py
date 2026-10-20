#!/usr/bin/env python3
"""Rebuild assets/*.js for all missions from the Tiled maps in tiled/. Run from anywhere: python3 tools/build_maps.py"""
import subprocess, sys, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for tmx, name in (('Scrapyard_outpost.tmx', 'outpost'), ('foundry_gate.tmx', 'foundry'), ('overlord_node.tmx', 'overlord')):
    print('==', tmx)
    subprocess.check_call([sys.executable, os.path.join(root, 'tools', 'convert_tmx.py'), os.path.join(root, 'tiled', tmx), os.path.join(root, 'assets', name + '.js'), name])
