#!/bin/sh
cd ${0%/*}

while true
do
	python bot.py
	wait $!
done

