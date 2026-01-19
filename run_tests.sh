#!/bin/bash
# Simple Test Launcher

echo "--- Image Slideshow Test Menu ---"
echo "1) Automated GUI Test"
echo "2) Interactive Demo"
echo "3) Component Tests (No GUI)"
echo "4) Create Test Images"
echo "5) Exit"
echo "---------------------------------"
read -p "Choice [1-5]: " choice

case $choice in
    1) python3 tests/test_gui.py ;;
    2) python3 tests/demo_gui.py ;;
    3) python3 tests/test_slideshow.py ;;
    4) python3 tests/create_test_images.py ;;
    5) exit 0 ;;
    *) echo "Invalid choice"; exit 1 ;;
esac
