#!/bin/bash

if [ "$RUN_DEV" = "True" ]
then
    echo "not doing anything, since it is debug mode"
else
    exec python3 /project/src/main.py
fi

