#!/bin/sh
ip route del default
ip route add default via 10.0.10.254

echo "Client gateway set"
cd frontend
npm run dev

