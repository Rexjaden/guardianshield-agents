python3 -c "import sys; content=open('DEPLOY_MASTER_STACK.sh', 'rb').read().replace(b'\r\n', b'\n'); open('DEPLOY_MASTER_STACK.sh', 'wb').write(content); print('Fixed Windows characters in DEPLOY_MASTER_STACK.sh')"

bash DEPLOY_MASTER_STACK.sh