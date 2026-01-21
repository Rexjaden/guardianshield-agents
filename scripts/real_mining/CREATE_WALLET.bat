@echo off
echo Installing Monero library...
pip install monero
echo.
echo Generating your wallet...
python -c "from monero.seed import Seed; s=Seed(); print('='*70); print('SAVE THIS - YOUR MONERO WALLET'); print('='*70); print(); print('SEED PHRASE (25 words - WRITE DOWN!):'); print(s.phrase); print(); print('WALLET ADDRESS (for mining):'); print(s.public_address()); print(); print('='*70)"
echo.
pause
