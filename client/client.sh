ip route del default
ip route add default via 10.0.10.254

echo "Client gateway set"

python backend/main.py 

npm run dev